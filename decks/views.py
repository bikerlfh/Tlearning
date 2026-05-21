from rest_framework import viewsets

from api.mixins import UserScopedQuerysetMixin

from .models import Deck
from .serializers import DeckSerializer


class DeckViewSet(UserScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
