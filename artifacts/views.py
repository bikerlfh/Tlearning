from rest_framework import generics, status
from rest_framework.response import Response

from accounts.models import ApiToken
from api.mixins import UserScopedQuerysetMixin

from .enums import ArtifactSource
from .models import Artifact
from .serializers import ArtifactSerializer


class ArtifactListCreateView(UserScopedQuerysetMixin, generics.ListCreateAPIView):
    queryset = Artifact.objects.select_related("deck")
    serializer_class = ArtifactSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
        return ctx

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if t := params.get("type"):
            qs = qs.filter(type=t)
        if deck := params.get("deck_id"):
            qs = qs.filter(deck_id=deck)
        if q := params.get("q"):
            qs = qs.filter(lemma__icontains=q)
        if src := params.get("source_language"):
            qs = qs.filter(source_language=src)
        if tgt := params.get("target_language"):
            qs = qs.filter(target_language=tgt)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        deck = validated["deck"]
        source = (
            ArtifactSource.MCP
            if isinstance(getattr(request, "auth", None), ApiToken)
            else ArtifactSource.REST_API
        )

        artifact, created = Artifact.objects.update_or_create(
            user=request.user,
            deck=deck,
            type=validated["type"],
            lemma=validated["lemma"],
            defaults={
                "source_language": validated["source_language"],
                "target_language": validated["target_language"],
                "data": validated["data"],
                "source": source,
            },
        )
        out = self.get_serializer(artifact).data
        return Response(out, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ArtifactDetailView(UserScopedQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Artifact.objects.select_related("deck")
    serializer_class = ArtifactSerializer
    lookup_field = "pk"

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
        return ctx
