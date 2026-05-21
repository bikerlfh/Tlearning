import pytest

from notifications.models import NotificationPreference, PushSubscription


@pytest.mark.django_db
class TestSubscriptionEndpoints:
    url = "/api/v1/notifications/subscriptions"

    def _payload(self):
        return {
            "endpoint": "https://push.example.com/abc",
            "p256dh_key": "pk_value",
            "auth_key": "ak_value",
            "user_agent": "Chrome on Mac",
        }

    def test_create(self, authed_client, user):
        response = authed_client.post(self.url, self._payload(), format="json")
        assert response.status_code == 201
        assert PushSubscription.objects.filter(user=user).count() == 1

    def test_idempotent_on_same_endpoint(self, authed_client, user):
        authed_client.post(self.url, self._payload(), format="json")
        response = authed_client.post(self.url, self._payload(), format="json")
        assert response.status_code in (200, 201)
        assert PushSubscription.objects.filter(user=user).count() == 1

    def test_delete(self, authed_client, user):
        post = authed_client.post(self.url, self._payload(), format="json")
        sub_id = post.json()["id"]
        response = authed_client.delete(f"{self.url}/{sub_id}")
        assert response.status_code == 204
        assert PushSubscription.objects.filter(id=sub_id).count() == 0

    def test_delete_other_user_404(self, authed_client, other_user):
        sub = PushSubscription.objects.create(
            user=other_user,
            endpoint="https://x",
            p256dh_key="pk",
            auth_key="ak",
            user_agent="ua",
        )
        response = authed_client.delete(f"{self.url}/{sub.id}")
        assert response.status_code == 404


@pytest.mark.django_db
class TestPreferenceEndpoints:
    url = "/api/v1/notifications/preferences"

    def test_get_returns_defaults(self, authed_client, user):
        response = authed_client.get(self.url)
        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is False
        assert body["frequency_per_day"] == 4
        # Time field representation may be "22:00:00" or "22:00" — accept both
        assert body["quiet_hours_start"].startswith("22:00")

    def test_patch_updates(self, authed_client, user):
        response = authed_client.patch(
            self.url,
            {"enabled": True, "frequency_per_day": 6, "weekdays_only": True},
            format="json",
        )
        assert response.status_code == 200
        pref = NotificationPreference.objects.get(user=user)
        assert pref.enabled is True
        assert pref.frequency_per_day == 6
        assert pref.weekdays_only is True
