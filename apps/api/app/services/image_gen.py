"""Free AI image generation helpers for Creative Agent.

Providers (in order):
1. Pollinations.ai — free, no API key
2. Hugging Face Inference API — free tier with HF_TOKEN
3. Procedural Pillow scene — always available offline
"""
from __future__ import annotations

import io
import logging
from urllib.parse import quote

import httpx
from PIL import Image, ImageDraw, ImageFilter

from app.config import settings

logger = logging.getLogger(__name__)

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


async def generate_scene(
    prompt: str,
    *,
    width: int,
    height: int,
    seed: int = 42,
) -> tuple[Image.Image | None, str]:
    """Return (image, engine_label). Image may be None only if all providers fail."""
    if settings.use_ai_images:
        img = await _pollinations(prompt, width=width, height=height, seed=seed)
        if img is not None:
            return img, "pollinations.ai"

        if settings.hf_token:
            img = await _huggingface(prompt, width=width, height=height)
            if img is not None:
                return img, "huggingface"

    return _procedural_scene(width, height, prompt), "procedural"


async def _pollinations(prompt: str, *, width: int, height: int, seed: int) -> Image.Image | None:
    # Keep prompts concise for URL length
    clean = " ".join(prompt.split())[:280]
    url = (
        f"{POLLINATIONS_BASE}/{quote(clean)}"
        f"?width={width}&height={height}&seed={seed}&nologo=true&enhance=true"
    )
    try:
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            res = await client.get(url)
            res.raise_for_status()
            content_type = res.headers.get("content-type", "")
            if "image" not in content_type and len(res.content) < 1000:
                logger.warning("Pollinations returned non-image: %s", content_type)
                return None
            return Image.open(io.BytesIO(res.content)).convert("RGB")
    except Exception as exc:
        logger.warning("Pollinations failed: %s", exc)
        return None


async def _huggingface(prompt: str, *, width: int, height: int) -> Image.Image | None:
    """HF free Inference API (Stable Diffusion). Requires HF_TOKEN."""
    model = settings.hf_image_model
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {settings.hf_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {"width": min(width, 1024), "height": min(height, 1024)},
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code == 503:
                # Model loading — give up quickly for demo latency
                logger.warning("HF model loading (503)")
                return None
            res.raise_for_status()
            img = Image.open(io.BytesIO(res.content)).convert("RGB")
            return img.resize((width, height), Image.Resampling.LANCZOS)
    except Exception as exc:
        logger.warning("Hugging Face image gen failed: %s", exc)
        return None


def _procedural_scene(width: int, height: int, prompt: str) -> Image.Image:
    """Offline gradient + soft light blobs — no network."""
    canvas = Image.new("RGB", (width, height), (24, 32, 48))
    draw = ImageDraw.Draw(canvas)
    # Vertical gradient
    for y in range(height):
        t = y / max(height - 1, 1)
        color = (
            int(30 + 40 * t),
            int(45 + 55 * t),
            int(70 + 80 * (1 - t)),
        )
        draw.line([(0, y), (width, y)], fill=color)

    # Soft accent orbs
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for cx, cy, r, col in (
        (int(width * 0.2), int(height * 0.25), int(min(width, height) * 0.35), (80, 140, 255, 70)),
        (int(width * 0.8), int(height * 0.7), int(min(width, height) * 0.4), (255, 140, 80, 55)),
        (int(width * 0.55), int(height * 0.35), int(min(width, height) * 0.25), (255, 255, 255, 35)),
    ):
        od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=40))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    # Tiny prompt fingerprint so scenes differ
    seed_bits = sum(ord(c) for c in prompt) % 40
    tint = Image.new("RGB", (width, height), (seed_bits, 20, 60 - seed_bits // 2))
    return Image.blend(canvas, tint, 0.08)


def soft_cutout(product: Image.Image) -> Image.Image:
    """Make near-white / light studio backgrounds transparent (free, local)."""
    rgba = product.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            # Near-white / light gray studio backdrop
            if r > 235 and g > 235 and b > 235:
                pixels[x, y] = (r, g, b, 0)
            elif r > 220 and g > 220 and b > 220 and abs(r - g) < 12 and abs(g - b) < 12:
                alpha = int(max(0, 255 - ((r + g + b) / 3 - 200) * 4))
                pixels[x, y] = (r, g, b, alpha)
    return rgba


def try_rembg(product: Image.Image) -> Image.Image | None:
    """Optional rembg background removal if installed + enabled."""
    if not settings.use_rembg:
        return None
    try:
        from rembg import remove

        buf = io.BytesIO()
        product.convert("RGBA").save(buf, format="PNG")
        out = remove(buf.getvalue())
        return Image.open(io.BytesIO(out)).convert("RGBA")
    except Exception as exc:
        logger.warning("rembg unavailable: %s", exc)
        return None
