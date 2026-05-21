class UserScopedQuerysetMixin:
    """Filter the view's queryset to records owned by request.user.

    Assumes the model has a `user` ForeignKey.
    """

    user_field = "user"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(**{self.user_field: self.request.user})
