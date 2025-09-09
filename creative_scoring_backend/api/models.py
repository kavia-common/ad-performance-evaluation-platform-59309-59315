from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimeStampedModel(models.Model):
    """Abstract base with created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Audience(TimeStampedModel):
    """Represents a synthetic audience definition."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    size = models.PositiveIntegerField(default=10000)
    # JSON blob for traits (privacy-friendly synthetic parameters)
    traits = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.name


def creative_upload_path(instance, filename):
    """Compute upload path for creative assets."""
    return f"creatives/{instance.owner_id}/{instance.id}/{filename}"


class Creative(TimeStampedModel):
    """Stores creative asset metadata and file reference."""
    TYPE_CHOICES = [
        ('mp4', 'MP4 Video'),
        ('image', 'Image (JPG/PNG)'),
        ('html5', 'HTML5 Zip/Bundle'),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creatives')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creative_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    file = models.FileField(upload_to=creative_upload_path, blank=True, null=True)
    # Optional metadata stored as JSON
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.creative_type})"


class ScoreWeighting(TimeStampedModel):
    """Admin-managed weighting for composite scoring."""
    name = models.CharField(max_length=128, default='default', unique=True)
    brand_lift_weight = models.FloatField(default=0.34)
    performance_weight = models.FloatField(default=0.33)
    attention_weight = models.FloatField(default=0.33)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Score Weighting"
        verbose_name_plural = "Score Weightings"


class Scorecard(TimeStampedModel):
    """Computed scores for a creative and audience."""
    creative = models.ForeignKey(Creative, on_delete=models.CASCADE, related_name='scorecards')
    audience = models.ForeignKey(Audience, on_delete=models.CASCADE, related_name='scorecards')
    # component scores 0..100
    brand_lift = models.FloatField()
    performance = models.FloatField()
    attention = models.FloatField()
    composite = models.FloatField()
    weights_snapshot = models.JSONField(default=dict, blank=True)
    breakdown_labels = models.JSONField(default=dict, blank=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('creative', 'audience')


class Recommendation(TimeStampedModel):
    """Stores diagnostic recommendations associated to a Scorecard."""
    scorecard = models.ForeignKey(Scorecard, on_delete=models.CASCADE, related_name='recommendations')
    text = models.TextField()
    priority = models.PositiveSmallIntegerField(default=2)  # 1 High, 2 Medium, 3 Low
    category = models.CharField(max_length=128, blank=True)


class ComparativeTest(TimeStampedModel):
    """Represents a comparative test between two creatives for a given audience."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comparative_tests')
    audience = models.ForeignKey(Audience, on_delete=models.CASCADE, related_name='comparative_tests')
    creative_a = models.ForeignKey(Creative, on_delete=models.CASCADE, related_name='comparisons_as_a')
    creative_b = models.ForeignKey(Creative, on_delete=models.CASCADE, related_name='comparisons_as_b')
    lift_projection = models.JSONField(default=dict, blank=True)
    result_summary = models.TextField(blank=True)
