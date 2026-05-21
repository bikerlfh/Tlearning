import pytest
from django.views.generic import View
from django.views.generic.list import MultipleObjectMixin
from rest_framework.test import APIRequestFactory

from accounts.models import ApiToken
from accounts.tokens import generate_token, hash_token
from api.mixins import UserScopedQuerysetMixin


class _DummyView(UserScopedQuerysetMixin, MultipleObjectMixin, View):
    queryset = ApiToken.objects.all()


@pytest.mark.django_db
def test_user_scoped_mixin_filters_to_request_user(user, other_user):
    ApiToken.objects.create(user=user, token_hash=hash_token(generate_token()), name="mine")
    ApiToken.objects.create(user=other_user, token_hash=hash_token(generate_token()), name="other")

    view = _DummyView()
    view.request = APIRequestFactory().get("/")
    view.request.user = user

    qs = view.get_queryset()
    assert qs.count() == 1
    assert qs.first().name == "mine"
