from unittest.mock import patch

import pytest


@pytest.mark.django_db
class TestTestEndpoint:
    url = "/api/v1/notifications/test"

    @patch("notifications.tasks.send_push_notification.delay")
    def test_dispatches_async_task(self, mock_delay, authed_client, user):
        response = authed_client.post(self.url)
        assert response.status_code == 202
        mock_delay.assert_called_once_with(user.id)

    def test_unauth_returns_401(self, api_client):
        response = api_client.post(self.url)
        assert response.status_code in (401, 403)
