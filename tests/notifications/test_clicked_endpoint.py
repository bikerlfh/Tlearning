import pytest
from django.utils import timezone

from notifications.enums import NotificationStatus
from notifications.models import NotificationLog


@pytest.fixture
def log_row(user):
    return NotificationLog.objects.create(
        user=user,
        sent_at=timezone.now(),
        status=NotificationStatus.SENT,
    )


@pytest.mark.django_db
class TestNotificationClickedEndpoint:
    def url(self, log_id):
        return f"/api/v1/notifications/{log_id}/clicked"

    def test_authenticated_records_click(self, authed_client, log_row):
        response = authed_client.post(self.url(log_row.id))
        assert response.status_code == 204
        log_row.refresh_from_db()
        assert log_row.clicked_at is not None

    def test_idempotent_second_call_does_not_overwrite(self, authed_client, log_row):
        authed_client.post(self.url(log_row.id))
        log_row.refresh_from_db()
        first_ts = log_row.clicked_at
        authed_client.post(self.url(log_row.id))
        log_row.refresh_from_db()
        assert log_row.clicked_at == first_ts

    def test_anonymous_caller_returns_204_noop(self, api_client, log_row):
        response = api_client.post(self.url(log_row.id))
        assert response.status_code == 204
        log_row.refresh_from_db()
        assert log_row.clicked_at is None

    def test_other_users_log_returns_204_noop(self, authed_client, other_user):
        other_log = NotificationLog.objects.create(
            user=other_user,
            sent_at=timezone.now(),
            status=NotificationStatus.SENT,
        )
        response = authed_client.post(self.url(other_log.id))
        assert response.status_code == 204
        other_log.refresh_from_db()
        assert other_log.clicked_at is None

    def test_unknown_log_returns_204_noop(self, authed_client):
        response = authed_client.post(
            self.url("00000000-0000-0000-0000-000000000000"),
        )
        assert response.status_code == 204
