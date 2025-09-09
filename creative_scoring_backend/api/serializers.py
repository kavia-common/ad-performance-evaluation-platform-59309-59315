from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Audience, Creative, ScoreWeighting, Scorecard, Recommendation, ComparativeTest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff"]


class AudienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audience
        fields = ["id", "name", "description", "size", "traits", "created_at", "updated_at"]


class CreativeSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Creative
        fields = ["id", "title", "description", "creative_type", "file", "metadata", "owner", "created_at", "updated_at"]
        read_only_fields = ["owner", "created_at", "updated_at"]


class CreativeUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Creative
        fields = ["title", "description", "creative_type", "file", "metadata"]


class ScoreWeightingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreWeighting
        fields = ["id", "name", "brand_lift_weight", "performance_weight", "attention_weight", "is_active", "created_at", "updated_at"]


class ScorecardSerializer(serializers.ModelSerializer):
    creative = CreativeSerializer(read_only=True)
    audience = AudienceSerializer(read_only=True)

    class Meta:
        model = Scorecard
        fields = [
            "id",
            "creative",
            "audience",
            "brand_lift",
            "performance",
            "attention",
            "composite",
            "weights_snapshot",
            "breakdown_labels",
            "extra",
            "created_at",
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = ["id", "text", "priority", "category"]


class ComparativeTestSerializer(serializers.ModelSerializer):
    creative_a = CreativeSerializer(read_only=True)
    creative_b = CreativeSerializer(read_only=True)
    audience = AudienceSerializer(read_only=True)

    class Meta:
        model = ComparativeTest
        fields = ["id", "owner", "audience", "creative_a", "creative_b", "lift_projection", "result_summary", "created_at"]
        read_only_fields = ["owner", "created_at"]


class ComparativeTestCreateSerializer(serializers.Serializer):
    creative_a_id = serializers.IntegerField()
    creative_b_id = serializers.IntegerField()
    audience_id = serializers.IntegerField()
