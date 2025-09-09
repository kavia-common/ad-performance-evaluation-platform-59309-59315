import io
import csv
from dataclasses import dataclass
from typing import Dict, List, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .models import ScoreWeighting, Creative, Audience


@dataclass
class ScoreComponents:
    brand_lift: float
    performance: float
    attention: float


# PUBLIC_INTERFACE
def get_active_weights() -> Dict[str, float]:
    """Return the active weighting configuration, defaulting if none active."""
    active = ScoreWeighting.objects.filter(is_active=True).order_by('-updated_at').first()
    if active:
        return {
            "brand_lift": active.brand_lift_weight,
            "performance": active.performance_weight,
            "attention": active.attention_weight,
        }
    # default distribution
    return {"brand_lift": 0.34, "performance": 0.33, "attention": 0.33}


def _normalize_score(v: float) -> float:
    return max(0.0, min(100.0, float(v)))


# PUBLIC_INTERFACE
def compute_component_scores(creative: Creative, audience: Audience) -> ScoreComponents:
    """Compute component scores using simple deterministic heuristics for demo purposes."""
    base = len(creative.title) % 50 + 25  # 25..74
    brand_lift = _normalize_score(base + (audience.size % 10) - 5)
    performance = _normalize_score(base * 0.9)
    attention = _normalize_score(100 - (audience.size % 30))
    return ScoreComponents(brand_lift=brand_lift, performance=performance, attention=attention)


# PUBLIC_INTERFACE
def compute_composite_score(components: ScoreComponents, weights: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    """Compute composite score as weighted average and return per-component contributions."""
    w_brand = weights.get("brand_lift", 0.34)
    w_perf = weights.get("performance", 0.33)
    w_att = weights.get("attention", 0.33)
    total = w_brand + w_perf + w_att or 1.0
    w_brand /= total
    w_perf /= total
    w_att /= total

    composite = components.brand_lift * w_brand + components.performance * w_perf + components.attention * w_att
    contributions = {
        "brand_lift": round(components.brand_lift * w_brand, 2),
        "performance": round(components.performance * w_perf, 2),
        "attention": round(components.attention * w_att, 2),
    }
    return round(composite, 2), contributions


# PUBLIC_INTERFACE
def generate_recommendations(components: ScoreComponents) -> List[Dict]:
    """Return top diagnostics based on weakest components."""
    pairs = [
        ("Brand cues unclear. Strengthen mnemonic devices.", components.brand_lift, "Brand"),
        ("Clarify CTA and align with landing page intent.", components.performance, "Performance"),
        ("Front-load key frames to capture attention in 1s.", components.attention, "Attention"),
    ]
    sorted_pairs = sorted(pairs, key=lambda p: p[1])[:3]
    recs = []
    for idx, (text, _, category) in enumerate(sorted_pairs, start=1):
        recs.append({"text": text, "priority": idx, "category": category})
    return recs


# PUBLIC_INTERFACE
def render_scorecard_pdf(data: Dict) -> bytes:
    """Render a simple PDF scorecard using reportlab and return its bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, "Creative Scorecard")
    y -= 24
    c.setFont("Helvetica", 12)
    for k in ["creative_title", "audience_name", "composite", "brand_lift", "performance", "attention"]:
        v = data.get(k, "")
        c.drawString(72, y, f"{k.replace('_',' ').title()}: {v}")
        y -= 18
    y -= 12
    c.drawString(72, y, "Recommendations:")
    y -= 18
    for rec in data.get("recommendations", []):
        c.drawString(86, y, f"- ({rec.get('category')}) {rec.get('text')}")
        y -= 16
        if y < 72:
            c.showPage()
            y = height - 72
    c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


# PUBLIC_INTERFACE
def render_scorecard_csv(rows: List[Dict]) -> str:
    """Render CSV string for scorecards."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else [])
    if rows:
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return buf.getvalue()
