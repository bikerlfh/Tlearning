import pytest
from allauth.socialaccount.models import SocialAccount


@pytest.fixture
def linked_google(user):
    return SocialAccount.objects.create(
        user=user,
        provider="google",
        uid="g-sub-1",
        extra_data={"email": user.email, "name": "Test User"},
    )


@pytest.mark.django_db
class TestSocialAccountList:
    url = "/api/v1/auth/social-accounts"

    def test_requires_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code in (401, 403)

    def test_lists_linked_accounts_for_current_user(self, authed_client, user, linked_google):
        response = authed_client.get(self.url)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        row = data["results"][0]
        assert row["provider"] == "google"
        assert row["uid"] == "g-sub-1"
        assert row["email"] == user.email

    def test_returns_empty_when_no_links(self, authed_client):
        response = authed_client.get(self.url)
        assert response.status_code == 200
        assert response.json() == {"count": 0, "results": []}

    def test_does_not_leak_other_users_links(self, authed_client, other_user):
        SocialAccount.objects.create(
            user=other_user,
            provider="google",
            uid="g-other",
            extra_data={"email": other_user.email},
        )
        response = authed_client.get(self.url)
        assert response.json()["count"] == 0


@pytest.mark.django_db
class TestSocialAccountDisconnect:
    def url(self, pk):
        return f"/api/v1/auth/social-accounts/{pk}/disconnect"

    def test_disconnects_account(self, authed_client, user, linked_google):
        # Make sure the user has a usable password (factory does)
        assert user.has_usable_password()
        response = authed_client.post(self.url(linked_google.pk))
        assert response.status_code == 204
        assert not SocialAccount.objects.filter(pk=linked_google.pk).exists()

    def test_404_for_unknown_account(self, authed_client):
        response = authed_client.post(self.url(99999))
        assert response.status_code == 404

    def test_cannot_disconnect_last_sign_in_method(self, authed_client, user, linked_google):
        # Strip the password to leave Google as the only sign-in method
        user.set_unusable_password()
        user.save()
        response = authed_client.post(self.url(linked_google.pk))
        assert response.status_code == 400
        assert SocialAccount.objects.filter(pk=linked_google.pk).exists()

    def test_cannot_disconnect_other_users_account(self, authed_client, other_user):
        other_link = SocialAccount.objects.create(
            user=other_user,
            provider="google",
            uid="g-other",
            extra_data={"email": other_user.email},
        )
        response = authed_client.post(self.url(other_link.pk))
        assert response.status_code == 404  # scoped by user
