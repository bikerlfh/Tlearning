import pytest

from tests.factories import UserFactory


@pytest.mark.django_db
def test_user_factory_creates_unique_users():
    u1 = UserFactory()
    u2 = UserFactory()
    assert u1.email != u2.email
    assert u1.check_password("testpass1")
    assert u2.check_password("testpass1")
