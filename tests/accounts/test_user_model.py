import pytest

from accounts.enums import UiLanguage
from accounts.models import User


@pytest.mark.django_db
class TestUser:
    def test_create_user_requires_email_and_password(self):
        user = User.objects.create_user(email="alice@example.com", password="securepass1")
        assert user.email == "alice@example.com"
        assert user.check_password("securepass1")
        assert user.is_active
        assert not user.is_staff

    def test_create_user_normalizes_email_domain_case(self):
        user = User.objects.create_user(email="Alice@Example.COM", password="securepass1")
        assert user.email == "Alice@example.com"

    def test_create_user_without_email_raises(self):
        with pytest.raises(ValueError, match="email"):
            User.objects.create_user(email="", password="securepass1")

    def test_default_ui_language_is_spanish(self):
        user = User.objects.create_user(email="alice@example.com", password="securepass1")
        assert user.preferred_ui_language == UiLanguage.SPANISH

    def test_default_timezone_is_utc(self):
        user = User.objects.create_user(email="alice@example.com", password="securepass1")
        assert user.timezone == "UTC"

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="securepass1")
        assert admin.is_staff
        assert admin.is_superuser

    def test_str_returns_email(self):
        user = User.objects.create_user(email="alice@example.com", password="securepass1")
        assert str(user) == "alice@example.com"
