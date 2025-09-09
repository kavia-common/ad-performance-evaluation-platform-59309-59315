from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Audience, Creative, Scorecard, Recommendation, ComparativeTest
from .serializers import (
    AudienceSerializer,
    CreativeSerializer,
    CreativeUploadSerializer,
    ScorecardSerializer,
    RecommendationSerializer,
    ComparativeTestSerializer,
    ComparativeTestCreateSerializer,
    ScoreWeightingSerializer,
)
from .services import (
    compute_component_scores,
    compute_composite_score,
    get_active_weights,
    generate_recommendations,
    render_scorecard_pdf,
    render_scorecard_csv,
)
from .models import ScoreWeighting


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health(request):
    """Simple health endpoint."""
    return Response({"message": "Server is up!"})


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_id="upload_creative",
    operation_summary="Upload creative",
    operation_description="Upload a creative asset (MP4, JPG/PNG, or HTML5 bundle) with metadata.",
    manual_parameters=[],
    responses={201: CreativeSerializer},
    tags=["upload"],
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload(request):
    """Accept creative uploads with metadata."""
    serializer = CreativeUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    creative = Creative.objects.create(
        owner=request.user,
        title=serializer.validated_data['title'],
        description=serializer.validated_data.get('description', ''),
        creative_type=serializer.validated_data['creative_type'],
        file=serializer.validated_data.get('file'),
        metadata=serializer.validated_data.get('metadata', {}),
    )
    return Response(CreativeSerializer(creative, context={"request": request}).data, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_id="generate_audience",
    operation_summary="Create or get synthetic audience",
    operation_description="Create a synthetic audience definition from provided traits and size.",
    responses={200: AudienceSerializer},
    tags=["audience"],
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def audience(request):
    """Create or retrieve a synthetic audience."""
    name = request.data.get("name")
    size = int(request.data.get("size", 10000))
    traits = request.data.get("traits", {})
    description = request.data.get("description", "")
    if not name:
        return Response({"detail": "name is required"}, status=400)
    obj, _ = Audience.objects.get_or_create(name=name, defaults={"size": size, "traits": traits, "description": description})
    if not _:
        # update existing basic fields
        obj.size = size
        obj.traits = traits
        obj.description = description
        obj.save()
    return Response(AudienceSerializer(obj).data)


score_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["creative_id", "audience_id"],
    properties={
        "creative_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Creative ID"),
        "audience_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Audience ID"),
    },
)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_id="score_creative",
    operation_summary="Score a creative for an audience",
    operation_description="Compute component scores and composite score, persist scorecard, and return with breakdown.",
    request_body=score_request_schema,
    responses={200: ScorecardSerializer},
    tags=["score"],
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def score(request):
    """Compute a scorecard for a given creative and audience."""
    creative = get_object_or_404(Creative, id=request.data.get("creative_id"))
    audience_obj = get_object_or_404(Audience, id=request.data.get("audience_id"))
    comps = compute_component_scores(creative, audience_obj)
    weights = get_active_weights()
    composite, contributions = compute_composite_score(comps, weights)
    with transaction.atomic():
        scorecard, _ = Scorecard.objects.update_or_create(
            creative=creative,
            audience=audience_obj,
            defaults={
                "brand_lift": comps.brand_lift,
                "performance": comps.performance,
                "attention": comps.attention,
                "composite": composite,
                "weights_snapshot": weights,
                "breakdown_labels": contributions,
            },
        )
        # ensure recommendations
        scorecard.recommendations.all().delete()
        recs_data = generate_recommendations(comps)
        for r in recs_data:
            Recommendation.objects.create(
                scorecard=scorecard,
                text=r["text"],
                priority=r["priority"],
                category=r.get("category", ""),
            )
    serialized = ScorecardSerializer(scorecard)
    data = serialized.data
    data["recommendations"] = RecommendationSerializer(scorecard.recommendations.all(), many=True).data
    return Response(data)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='get',
    operation_id="get_recommendations",
    operation_summary="Get recommendations for a scorecard",
    operation_description="Return top 3 diagnostic recommendations for a creative and audience.",
    manual_parameters=[
        openapi.Parameter("creative_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
        openapi.Parameter("audience_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
    ],
    responses={200: RecommendationSerializer(many=True)},
    tags=["recommendations"],
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recommendations(request):
    """Return recommendations associated with a scorecard."""
    creative = get_object_or_404(Creative, id=request.GET.get("creative_id"))
    audience_obj = get_object_or_404(Audience, id=request.GET.get("audience_id"))
    scorecard = get_object_or_404(Scorecard, creative=creative, audience=audience_obj)
    recs = scorecard.recommendations.order_by("priority")
    return Response(RecommendationSerializer(recs, many=True).data)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_id="comparative_test",
    operation_summary="Comparative creative testing",
    operation_description="Compare two creatives for the same audience and return relative lift projections and summary.",
    request_body=ComparativeTestCreateSerializer,
    responses={200: ComparativeTestSerializer},
    tags=["comparative_test"],
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def comparative_test(request):
    """Compare two creatives by their composite scores and compute relative lift projections."""
    cdata = ComparativeTestCreateSerializer(data=request.data)
    cdata.is_valid(raise_exception=True)
    creative_a = get_object_or_404(Creative, id=cdata.validated_data["creative_a_id"])
    creative_b = get_object_or_404(Creative, id=cdata.validated_data["creative_b_id"])
    audience_obj = get_object_or_404(Audience, id=cdata.validated_data["audience_id"])

    # Ensure scorecards exist
    def ensure_score(creative):
        comps = compute_component_scores(creative, audience_obj)
        weights = get_active_weights()
        composite, _ = compute_composite_score(comps, weights)
        sc, _ = Scorecard.objects.update_or_create(
            creative=creative,
            audience=audience_obj,
            defaults={
                "brand_lift": comps.brand_lift,
                "performance": comps.performance,
                "attention": comps.attention,
                "composite": composite,
                "weights_snapshot": weights,
            },
        )
        return sc

    sc_a = ensure_score(creative_a)
    sc_b = ensure_score(creative_b)

    # Simple lift projection: relative delta percent
    if sc_b.composite > 0:
        lift = (sc_a.composite - sc_b.composite) / sc_b.composite * 100.0
    else:
        lift = 0.0
    result_summary = f"Creative A ({creative_a.title}) is projected to deliver {lift:.1f}% lift vs Creative B ({creative_b.title})."
    test = ComparativeTest.objects.create(
        owner=request.user,
        audience=audience_obj,
        creative_a=creative_a,
        creative_b=creative_b,
        lift_projection={"lift_percent": round(lift, 2), "composite_a": sc_a.composite, "composite_b": sc_b.composite},
        result_summary=result_summary,
    )
    return Response(ComparativeTestSerializer(test).data)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='get',
    operation_id="export_scorecard",
    operation_summary="Export scorecard",
    operation_description="Export a scorecard as PDF or CSV for a given creative and audience.",
    manual_parameters=[
        openapi.Parameter("creative_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
        openapi.Parameter("audience_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
        openapi.Parameter("format", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False, description="pdf or csv"),
    ],
    tags=["export"],
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export(request):
    """Export scorecard as PDF or CSV."""
    creative = get_object_or_404(Creative, id=request.GET.get("creative_id"))
    audience_obj = get_object_or_404(Audience, id=request.GET.get("audience_id"))
    fmt = request.GET.get("format", "pdf").lower()
    scorecard = get_object_or_404(Scorecard, creative=creative, audience=audience_obj)
    recs = [{"text": r.text, "category": r.category, "priority": r.priority} for r in scorecard.recommendations.all()]
    base_payload = {
        "creative_title": creative.title,
        "audience_name": audience_obj.name,
        "brand_lift": scorecard.brand_lift,
        "performance": scorecard.performance,
        "attention": scorecard.attention,
        "composite": scorecard.composite,
        "recommendations": recs,
    }
    if fmt == "pdf":
        pdf = render_scorecard_pdf(base_payload)
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="scorecard_{creative.id}_{audience_obj.id}.pdf"'
        return resp
    elif fmt == "csv":
        rows = [base_payload]
        csv_str = render_scorecard_csv(rows)
        resp = HttpResponse(csv_str, content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="scorecard_{creative.id}_{audience_obj.id}.csv"'
        return resp
    return Response({"detail": "Unsupported format"}, status=400)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='get',
    operation_id="list_weightings",
    operation_summary="List score weightings",
    operation_description="List all weighting configurations.",
    responses={200: ScoreWeightingSerializer(many=True)},
    tags=["admin"],
)
@swagger_auto_schema(
    method='post',
    operation_id="create_weighting",
    operation_summary="Create weighting configuration",
    operation_description="Create a weighting config. Set is_active to true to activate.",
    request_body=ScoreWeightingSerializer,
    responses={201: ScoreWeightingSerializer},
    tags=["admin"],
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAdminUser])
def admin_weightings(request):
    """Admin endpoint to list and create weighting configurations."""
    if request.method == 'GET':
        qs = ScoreWeighting.objects.all().order_by('-is_active', 'name')
        return Response(ScoreWeightingSerializer(qs, many=True).data)
    data = request.data
    serializer = ScoreWeightingSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    obj = serializer.save()
    if obj.is_active:
        ScoreWeighting.objects.exclude(id=obj.id).update(is_active=False)
    return Response(ScoreWeightingSerializer(obj).data, status=201)


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='get',
    operation_id="list_creatives",
    operation_summary="List creatives",
    operation_description="List creatives owned by the authenticated user.",
    tags=["upload"],
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_creatives(request):
    """List creatives for the current user."""
    qs = Creative.objects.filter(owner=request.user).order_by('-created_at')
    return Response(CreativeSerializer(qs, many=True, context={"request": request}).data)
