from rest_framework.routers import SimpleRouter

from .views import DeckViewSet

router = SimpleRouter(trailing_slash=False)
router.register("decks", DeckViewSet, basename="deck")
urlpatterns = router.urls
