from typing import Any


class UserScopedQuerysetMixin:
    """Filter the view's queryset to records owned by request.user.

    Assumes the model has a `user` ForeignKey.
    """

    user_field: str = "user"

    def get_queryset(self) -> Any:
        qs = super().get_queryset()  # type: ignore[misc]
        return qs.filter(**{self.user_field: self.request.user})  # type: ignore[attr-defined]
