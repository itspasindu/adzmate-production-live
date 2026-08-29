from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.config import settings
from app.services.image_gen import generate_scene, soft_cutout, try_rembg
from app.services.llm import chat_json, llm_enabled
from app.storage import read_image_bytes


FORMATS = {
    "meta_feed": (1080, 1080),
    "tiktok": (1080, 1920),
    "google_display": (1200, 628),
}

SCENE_HINTS = {
    "meta_feed": "square social ad, lifestyle product photography, soft daylight, premium ecommerce look",
    "tiktok": "vertical 9:16 mobile video thumbnail background, trendy lifestyle, bokeh lights",
    "google_display": "wide banner advertising backdrop, clean modern gradient, commercial photography",
}

OBJECTIVE_CTA = {
    "sales": "Shop Now",
    "leads": "Get Offer",
    "traffic": "Learn More",
    "engagement": "See More",
}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _mock_rekognition_tags(image: Image.Image) -> list[str]:
    """Local stand-in for AWS Rekognition labels."""
    pixels = list(image.resize((32, 32)).getdata())
    avg = tuple(sum(c[i] for c in pixels) / len(pixels) for i in range(3))
    brightness = sum(avg) / 3
    tags = ["Product", "Merchandise"]
    if brightness > 160:
        tags.append("Bright")
    elif brightness > 80:
        tags.append("Neutral")
    else:
        tags.append("Dark")
    r, g, b = avg
    if r > g and r > b:
        tags.append("WarmTone")
    elif b > r and b > g:
        tags.append("CoolTone")
    else:
        tags.append("NaturalTone")
    tags.append("StudioShot" if brightness > 120 else "Lifestyle")
    return tags


def _load_font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "Arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _prepare_product(product: Image.Image) -> tuple[Image.Image, str]:
    """Return product cutout + cutout engine label."""
    rembg = try_rembg(product)
    if rembg is not None:
        return rembg, "rembg"
    return soft_cutout(product), "soft-cutout"


def _drop_shadow(size: tuple[int, int], product: Image.Image, offset: tuple[int, int]) -> Image.Image:
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    alpha = product.split()[-1] if product.mode == "RGBA" else None
    blob = Image.new("RGBA", product.size, (0, 0, 0, 110))
    if alpha:
        blob.putalpha(alpha)
    shadow.paste(blob, offset, blob)
    return shadow.filter(ImageFilter.GaussianBlur(18))


def _compose_creative(
    product: Image.Image,
    background: Image.Image,
    size: tuple[int, int],
    brand: str,
    headline: str,
    cta: str,
    primary: str,
    accent: str,
    out_path: Path,
) -> None:
    w, h = size
    canvas = background.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)

    wash = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    for y in range(int(h * 0.55), h):
        t = (y - int(h * 0.55)) / max(h - int(h * 0.55), 1)
        alpha = int(40 + 150 * t)
        r, g, b = _hex_to_rgb(primary)
        wd.line([(0, y), (w, y)], fill=(r, g, b, alpha))
    canvas = Image.alpha_composite(canvas, wash)

    max_side = int(min(w, h) * 0.58)
    product_rgba = product.convert("RGBA")
    product_rgba.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    pw, ph = product_rgba.size
    px = (w - pw) // 2
    py = int(h * 0.18)

    shadow = _drop_shadow((w, h), product_rgba, (px + 10, py + 18))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.paste(product_rgba, (px, py), product_rgba)

    draw = ImageDraw.Draw(canvas)
    title_font = _load_font(max(28, w // 18))
    brand_font = _load_font(max(20, w // 28))
    cta_font = _load_font(max(18, w // 32))

    draw.text((40, 36), brand.upper(), fill=(255, 255, 255), font=brand_font)
    draw.text((40, int(h * 0.78)), headline[:42], fill=(255, 255, 255), font=title_font)

    cta_box = [40, int(h * 0.88), 40 + max(180, w // 4), int(h * 0.88) + 56]
    draw.rounded_rectangle(cta_box, radius=8, fill=_hex_to_rgb(accent) + (255,))
    draw.text((cta_box[0] + 24, cta_box[1] + 14), cta, fill=(20, 20, 20), font=cta_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "PNG")


def _ctx_value(ctx: dict[str, Any], key: str, default: Any = "") -> Any:
    val = ctx.get(key, default)
    return default if val is None else val


def _template_copy(ctx: dict[str, Any]) -> list[dict]:
    product_name = str(_ctx_value(ctx, "product_name", "Product"))
    brand = str(_ctx_value(ctx, "brand_name", "Brand"))
    brief = str(_ctx_value(ctx, "brief") or _ctx_value(ctx, "product_description") or "")
    objective = str(_ctx_value(ctx, "objective", "sales")).lower()
    cta = OBJECTIVE_CTA.get(objective, "Shop Now")
    short = brief.strip().split(".")[0][:90] or f"Discover {product_name}"
    description = brief.strip()[:160] or f"{product_name} by {brand} — built for results."
    return [
        {
            "format": "meta_feed",
            "headline": f"{product_name}: Built for impact",
            "primary_text": f"{short}. Discover {product_name} by {brand}.",
            "description": description,
            "cta": cta,
            "scene_prompt": None,
        },
        {
            "format": "tiktok",
            "headline": f"Why everyone wants {product_name}",
            "primary_text": f"POV: you finally found {product_name}. {brand} just dropped it.",
            "description": description,
            "cta": "Learn More" if objective == "traffic" else cta,
            "scene_prompt": None,
        },
        {
            "format": "google_display",
            "headline": f"{brand} · {product_name}",
            "primary_text": f"{short}. Start today.",
            "description": description,
            "cta": cta,
            "scene_prompt": None,
        },
    ]


def _template_copy_variations(ctx: dict[str, Any]) -> list[dict]:
    product_name = str(_ctx_value(ctx, "product_name", "Product"))
    brand = str(_ctx_value(ctx, "brand_name", "Brand"))
    brief = str(_ctx_value(ctx, "brief") or _ctx_value(ctx, "product_description") or "")
    objective = str(_ctx_value(ctx, "objective", "sales")).lower()
    cta = OBJECTIVE_CTA.get(objective, "Shop Now")
    short = brief.strip().split(".")[0][:80] or product_name
    return [
        {
            "angle": "benefit",
            "headline": f"{product_name} that delivers",
            "primary_text": f"{short}. See why {brand} customers upgrade.",
            "description": f"Benefit-led {objective} creative for {product_name}.",
            "cta": cta,
        },
        {
            "angle": "urgency",
            "headline": f"Limited: {product_name}",
            "primary_text": f"Don't wait — {product_name} by {brand} is moving fast.",
            "description": f"Urgency-led {objective} creative for {product_name}.",
            "cta": cta,
        },
        {
            "angle": "social_proof",
            "headline": f"Loved by early fans",
            "primary_text": f"Join people choosing {product_name}. {short}.",
            "description": f"Social-proof {objective} creative for {product_name}.",
            "cta": cta,
        },
        {
            "angle": "problem_solution",
            "headline": f"Solve it with {product_name}",
            "primary_text": f"{brand} made {product_name} for people who want results — not fluff.",
            "description": f"Problem/solution {objective} creative for {product_name}.",
            "cta": cta,
        },
    ]


def _template_audiences(ctx: dict[str, Any]) -> list[dict]:
    product_name = str(_ctx_value(ctx, "product_name", "Product"))
    country = str(_ctx_value(ctx, "target_country") or "your market")
    location = str(_ctx_value(ctx, "target_location") or "")
    place = f"{location}, {country}" if location else country
    age_min = int(_ctx_value(ctx, "age_min", 18))
    age_max = int(_ctx_value(ctx, "age_max", 65))
    gender = str(_ctx_value(ctx, "gender", "all"))
    language = str(_ctx_value(ctx, "language", "en"))
    objective = str(_ctx_value(ctx, "objective", "sales"))
    return [
        {
            "name": f"{product_name} core buyers",
            "type": "interest",
            "rationale": f"Matches your brief targeting for {objective} in {place}.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "interests": [product_name, "Online shopping", "Brand discovery"],
            "estimated_reach": "medium",
        },
        {
            "name": "1% Lookalike — engagers",
            "type": "lookalike",
            "rationale": "People similar to visitors who engage with product content and ads.",
            "age_min": max(18, age_min - 2),
            "age_max": min(65, age_max + 2),
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "interests": ["Early adopters", "Social commerce"],
            "lookalikes": ["LAL 1% engagers"],
            "estimated_reach": "broad",
        },
        {
            "name": "Website + cart retargeting",
            "type": "retargeting",
            "rationale": f"Prior {objective} converters and site visitors for {product_name}.",
            "age_min": age_min,
            "age_max": age_max,
            "gender": gender,
            "locations": [place],
            "languages": [language],
            "retargeting": ["Cart abandoners", "Landing page visitors", "Video viewers"],
            "estimated_reach": "narrow",
        },
    ]


def _default_scene_prompt(fmt: str, ctx: dict[str, Any], tags: list[str]) -> str:
    hint = SCENE_HINTS.get(fmt, "premium advertising background")
    product_name = str(_ctx_value(ctx, "product_name", "product"))
    brand = str(_ctx_value(ctx, "brand_name", "brand"))
    brief = str(_ctx_value(ctx, "brief") or _ctx_value(ctx, "product_description") or "")
    short = brief.strip().split(".")[0][:80]
    return (
        f"{hint}, empty scene without text, no logos, space for product in center, "
        f"for {product_name} by {brand}, mood: {short}, visual cues: {', '.join(tags[:4])}"
    )


def _normalize_variants(data: dict | list | None, fallback: list[dict]) -> list[dict]:
    if not data:
        return fallback
    items = data.get("variants") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return fallback

    by_format = {v["format"]: dict(v) for v in fallback}
    for item in items:
        if not isinstance(item, dict):
            continue
        fmt = item.get("format")
        if fmt not in FORMATS:
            continue
        by_format[fmt] = {
            "format": fmt,
            "headline": str(item.get("headline") or by_format[fmt]["headline"])[:80],
            "primary_text": str(item.get("primary_text") or by_format[fmt]["primary_text"])[:220],
            "description": str(item.get("description") or by_format[fmt].get("description") or "")[:200],
            "cta": str(item.get("cta") or by_format[fmt]["cta"])[:24],
            "scene_prompt": item.get("scene_prompt") or by_format[fmt].get("scene_prompt"),
        }
    return [by_format[f] for f in FORMATS]


def _normalize_variations(data: dict | None, fallback: list[dict]) -> list[dict]:
    if not data or not isinstance(data, dict):
        return fallback
    items = data.get("copy_variations") or data.get("variations")
    if not isinstance(items, list) or not items:
        return fallback
    out: list[dict] = []
    for item in items[:6]:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "angle": str(item.get("angle") or "variant")[:40],
                "headline": str(item.get("headline") or "")[:80],
                "primary_text": str(item.get("primary_text") or "")[:220],
                "description": str(item.get("description") or "")[:200],
                "cta": str(item.get("cta") or "Shop Now")[:24],
            }
        )
    return out or fallback


def _normalize_audiences(data: dict | None, fallback: list[dict]) -> list[dict]:
    if not data or not isinstance(data, dict):
        return fallback
    items = data.get("audience_suggestions") or data.get("audiences")
    if not isinstance(items, list) or not items:
        return fallback
    out: list[dict] = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        interests = item.get("interests") or []
        if not isinstance(interests, list):
            interests = [str(interests)]
        locations = item.get("locations") or []
        if not isinstance(locations, list):
            locations = [str(locations)]
        languages = item.get("languages") or []
        if not isinstance(languages, list):
            languages = [str(languages)]
        out.append(
            {
                "name": str(item.get("name") or "Audience")[:80],
                "rationale": str(item.get("rationale") or "")[:240],
                "age_min": int(item.get("age_min") or fallback[0]["age_min"]),
                "age_max": int(item.get("age_max") or fallback[0]["age_max"]),
                "gender": str(item.get("gender") or "all"),
                "locations": [str(x) for x in locations][:4],
                "languages": [str(x) for x in languages][:3],
                "interests": [str(x) for x in interests][:8],
                "estimated_reach": str(item.get("estimated_reach") or "medium"),
            }
        )
    return out or fallback


async def _llm_generate_copy_pack(ctx: dict[str, Any], vision_tags: list[str]) -> dict | None:
    system = (
        "You are an expert performance-marketing creative strategist. "
        "Write Meta/TikTok/Google ad copy, extra copy variations, and audience suggestions. "
        "Return JSON only."
    )
    user = (
        f"Brand: {_ctx_value(ctx, 'brand_name')}\n"
        f"Product title: {_ctx_value(ctx, 'product_name')}\n"
        f"Product description: {_ctx_value(ctx, 'product_description') or _ctx_value(ctx, 'brief')}\n"
        f"Product URL: {_ctx_value(ctx, 'product_url') or 'n/a'}\n"
        f"Objective: {_ctx_value(ctx, 'objective', 'sales')}\n"
        f"Daily budget: {_ctx_value(ctx, 'daily_budget')}\n"
        f"Duration days: {_ctx_value(ctx, 'duration_days')}\n"
        f"Country: {_ctx_value(ctx, 'target_country')}\n"
        f"Location: {_ctx_value(ctx, 'target_location')}\n"
        f"Age: {_ctx_value(ctx, 'age_min')}-{_ctx_value(ctx, 'age_max')}\n"
        f"Gender: {_ctx_value(ctx, 'gender')}\n"
        f"Language: {_ctx_value(ctx, 'language')}\n"
        f"Vision tags: {', '.join(vision_tags)}\n\n"
        "Produce JSON with:\n"
        "1) variants — exactly 3 objects with keys: format "
        '(meta_feed|tiktok|google_display), headline (max 42), primary_text (max 120), '
        "description (max 90), cta (short), scene_prompt (empty lifestyle background, no text/logos).\n"
        "2) copy_variations — 4 objects with keys: angle, headline, primary_text, description, cta.\n"
        "3) audience_suggestions — 3 objects with keys: name, rationale, age_min, age_max, gender, "
        "locations (array), languages (array), interests (array), estimated_reach (narrow|medium|broad).\n"
        "Write ad copy in the campaign language when possible."
    )
    return await chat_json(system, user, temperature=0.55, max_tokens=1600)


async def run_creative_agent(
    campaign_id: str,
    product_image_path: str | None,
    brand_name: str,
    product_name: str,
    brief: str,
    brand_primary: str,
    brand_accent: str,
    context: dict[str, Any] | None = None,
) -> dict:
    await asyncio.sleep(0.2)

    if settings.force_fail_agent == "creative":
        raise RuntimeError("Creative agent forced failure (demo)")

    ctx: dict[str, Any] = {
        "brand_name": brand_name,
        "product_name": product_name,
        "brief": brief,
        "brand_primary": brand_primary,
        "brand_accent": brand_accent,
        **(context or {}),
    }

    out_dir = settings.generated_dir / campaign_id / "creatives"
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_upload = await read_image_bytes(product_image_path)
    if raw_upload is not None:
        product = Image.open(BytesIO(raw_upload)).convert("RGBA")
        used_upload = True
    elif product_image_path and Path(product_image_path).exists():
        product = Image.open(product_image_path).convert("RGBA")
        used_upload = True
    else:
        used_upload = False
        product = Image.new("RGBA", (640, 640), (240, 240, 235, 255))
        draw = ImageDraw.Draw(product)
        draw.ellipse([120, 120, 520, 520], fill=_hex_to_rgb(brand_accent) + (255,))
        draw.rectangle([220, 260, 420, 460], fill=_hex_to_rgb(brand_primary) + (255,))

    product, cutout_engine = _prepare_product(product)
    tags = _mock_rekognition_tags(product.convert("RGB"))
    fallback = _template_copy(ctx)
    fallback_variations = _template_copy_variations(ctx)
    fallback_audiences = _template_audiences(ctx)
    copy_engine = "template"

    variants = fallback
    copy_variations = fallback_variations
    audience_suggestions = fallback_audiences

    if llm_enabled():
        pack = await _llm_generate_copy_pack(ctx, tags)
        if pack:
            variants = _normalize_variants(pack, fallback)
            copy_variations = _normalize_variations(pack, fallback_variations)
            audience_suggestions = _normalize_audiences(pack, fallback_audiences)
            copy_engine = f"llm:{settings.llm_model}"

    assets = []
    image_engines: list[str] = []

    for idx, variant in enumerate(variants):
        fmt = variant["format"]
        size = FORMATS[fmt]
        path = out_dir / f"{fmt}.png"
        scene_prompt = variant.get("scene_prompt") or _default_scene_prompt(fmt, ctx, tags)
        background, img_engine = await generate_scene(
            scene_prompt,
            width=size[0],
            height=size[1],
            seed=1000 + idx * 17 + sum(ord(c) for c in product_name) % 97,
        )
        assert background is not None
        image_engines.append(img_engine)

        _compose_creative(
            product,
            background,
            size,
            brand_name,
            variant["headline"][:42],
            variant["cta"],
            brand_primary,
            brand_accent,
            path,
        )
        assets.append(
            {
                "format": fmt,
                "headline": variant["headline"],
                "primary_text": variant["primary_text"],
                "description": variant.get("description") or "",
                "cta": variant["cta"],
                "scene_prompt": scene_prompt,
                "image_engine": img_engine,
                "width": size[0],
                "height": size[1],
                "url": f"{settings.public_base_url}/generated/{campaign_id}/creatives/{fmt}.png",
            }
        )

    primary_image_engine = max(set(image_engines), key=image_engines.count) if image_engines else "none"
    engine = f"{copy_engine}+{primary_image_engine}+{cutout_engine}"

    creative_ready = 0.0
    if assets:
        creative_ready = 0.72
        if used_upload:
            creative_ready += 0.12
        if brief and len(brief.strip()) > 40:
            creative_ready += 0.05
        if copy_engine.startswith("llm"):
            creative_ready += 0.04
        if primary_image_engine in {"pollinations.ai", "huggingface"}:
            creative_ready += 0.05
        creative_ready = min(0.99, creative_ready)

    return {
        "creative_ready": round(creative_ready, 3),
        "vision_tags": tags,
        "assets": assets,
        "copy_variations": copy_variations,
        "audience_suggestions": audience_suggestions,
        "templates_matched": list(FORMATS.keys()),
        "product_upload": used_upload,
        "cutout_engine": cutout_engine,
        "image_engine": primary_image_engine,
        "engine": engine,
        "message": (
            f"Built {len(assets)} ads + {len(copy_variations)} copy variants + "
            f"{len(audience_suggestions)} audience ideas from "
            f"{'uploaded product photo' if used_upload else 'placeholder'} "
            f"using {primary_image_engine} scenes + {copy_engine} copy"
        ),
    }
