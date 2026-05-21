import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


@pytest.mark.django_db
class TestPasswordResetRequest:
    url = "/api/v1/auth/password-reset/request"

    def test_known_email_sends_reset_link(self, api_client, user, settings):
        settings.FRONTEND_URL = "http://localhost:3000"
        response = api_client.post(self.url, {"email": user.email}, format="json")
        assert response.status_code == 204
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == [user.email]
        assert "http://localhost:3000/reset-password?uid=" in message.body
        assert "&token=" in message.body

    def test_unknown_email_returns_204_silently_and_sends_no_mail(self, api_client):
        response = api_client.post(self.url, {"email": "nobody@example.com"}, format="json")
        assert response.status_code == 204
        assert len(mail.outbox) == 0

    def test_inactive_user_does_not_receive_mail(self, api_client, user):
        user.is_active = False
        user.save()
        response = api_client.post(self.url, {"email": user.email}, format="json")
        assert response.status_code == 204
        assert len(mail.outbox) == 0

    def test_email_is_case_insensitive(self, api_client, user):
        response = api_client.post(self.url, {"email": user.email.upper()}, format="json")
        assert response.status_code == 204
        assert len(mail.outbox) == 1


def _make_link(user):
    return (
        urlsafe_base64_encode(force_bytes(user.pk)),
        default_token_generator.make_token(user),
    )


@pytest.mark.django_db
class TestPasswordResetConfirm:
    url = "/api/v1/auth/password-reset/confirm"

    def test_valid_link_sets_new_password(self, api_client, user):
        uid, token = _make_link(user)
        response = api_client.post(
            self.url,
            {"uid": uid, "token": token, "password": "BrandNewPass123"},
            format="json",
        )
        assert response.status_code == 204
        user.refresh_from_db()
        assert user.check_password("BrandNewPass123")

    def test_old_password_no_longer_works(self, api_client, user):
        # Sanity: the factory installs password "testpass1"
        assert user.check_password("testpass1")
        uid, token = _make_link(user)
        api_client.post(
            self.url,
            {"uid": uid, "token": token, "password": "BrandNewPass123"},
            format="json",
        )
        user.refresh_from_db()
        assert not user.check_password("testpass1")

    def test_invalid_token_rejected(self, api_client, user):
        uid, _ = _make_link(user)
        response = api_client.post(
            self.url,
            {"uid": uid, "token": "garbage-token", "password": "BrandNewPass123"},
            format="json",
        )
        assert response.status_code == 400

    def test_token_invalidated_after_password_change(self, api_client, user):
        """Django's PasswordResetTokenGenerator hashes the current password into the
        token, so a token issued for the previous password becomes invalid once the
        password changes (the second reset attempt with the same token must fail)."""
        uid, token = _make_link(user)
        api_client.post(
            self.url,
            {"uid": uid, "token": token, "password": "FirstNewPass123"},
            format="json",
        )
        response = api_client.post(
            self.url,
            {"uid": uid, "token": token, "password": "SecondNewPass123"},
            format="json",
        )
        assert response.status_code == 400

    def test_short_password_rejected_by_validators(self, api_client, user):
        uid, token = _make_link(user)
        response = api_client.post(
            self.url,
            {"uid": uid, "token": token, "password": "short"},
            format="json",
        )
        assert response.status_code == 400
        assert "password" in response.json()

    def test_unknown_uid_rejected(self, api_client):
        response = api_client.post(
            self.url,
            {
                "uid": urlsafe_base64_encode(force_bytes("00000000-0000-0000-0000-000000000000")),
                "token": "anything",
                "password": "BrandNewPass123",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_missing_fields_rejected(self, api_client):
        response = api_client.post(self.url, {"uid": "x"}, format="json")
        assert response.status_code == 400
