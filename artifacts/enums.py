from django.db import models


class ArtifactType(models.TextChoices):
    WORD = "word", "Word"
    PHRASAL_VERB = "phrasal_verb", "Phrasal verb"
    IDIOM = "idiom", "Idiom"
    COLLOCATION = "collocation", "Collocation"
    EXPRESSION = "expression", "Expression"


class ArtifactSource(models.TextChoices):
    MCP = "mcp", "MCP"
    REST_API = "rest_api", "REST API"
    MANUAL = "manual", "Manual"
