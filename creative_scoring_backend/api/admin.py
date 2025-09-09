from django.contrib import admin
from .models import Audience, Creative, ScoreWeighting, Scorecard, Recommendation, ComparativeTest


@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):
    list_display = ("name", "size", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Creative)
class CreativeAdmin(admin.ModelAdmin):
    list_display = ("title", "creative_type", "owner", "created_at")
    list_filter = ("creative_type",)
    search_fields = ("title", "description", "owner__username")


@admin.register(ScoreWeighting)
class ScoreWeightingAdmin(admin.ModelAdmin):
    list_display = ("name", "brand_lift_weight", "performance_weight", "attention_weight", "is_active", "updated_at")
    list_editable = ("brand_lift_weight", "performance_weight", "attention_weight", "is_active")


@admin.register(Scorecard)
class ScorecardAdmin(admin.ModelAdmin):
    list_display = ("creative", "audience", "composite", "created_at")
    list_filter = ("audience",)
    search_fields = ("creative__title",)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("scorecard", "priority", "category", "created_at")
    list_filter = ("priority", "category")


@admin.register(ComparativeTest)
class ComparativeTestAdmin(admin.ModelAdmin):
    list_display = ("owner", "audience", "creative_a", "creative_b", "created_at")
