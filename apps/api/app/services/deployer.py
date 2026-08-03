from __future__ import annotations

from pathlib import Path

from jinja2 import Template

from app.config import settings

LANDING_TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{ brand }} — {{ product }}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    :root {
      --primary: {{ primary }};
      --accent: {{ accent }};
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Outfit", system-ui, sans-serif;
      color: #f7f3ec;
      min-height: 100vh;
      background:
        radial-gradient(1200px 600px at 10% -10%, color-mix(in srgb, var(--accent) 35%, transparent), transparent),
        linear-gradient(155deg, var(--primary) 0%, #061912 55%, #0a1f18 100%);
    }
    .hero {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 2rem;
      align-items: center;
      padding: 4rem clamp(1.5rem, 5vw, 5rem);
    }
    @media (max-width: 860px) {
      .hero { grid-template-columns: 1fr; padding-top: 2.5rem; }
    }
    .brand {
      font-family: "Fraunces", Georgia, serif;
      font-size: clamp(2.8rem, 7vw, 5rem);
      line-height: 0.95;
      letter-spacing: -0.03em;
      margin-bottom: 1rem;
    }
    .headline {
      font-size: clamp(1.15rem, 2.4vw, 1.55rem);
      font-weight: 500;
      max-width: 28ch;
      margin-bottom: 0.85rem;
    }
    .sub {
      opacity: 0.82;
      max-width: 42ch;
      line-height: 1.55;
      margin-bottom: 1.75rem;
    }
    .cta {
      display: inline-block;
      background: var(--accent);
      color: #1a1208;
      text-decoration: none;
      font-weight: 600;
      padding: 0.9rem 1.4rem;
      border-radius: 6px;
      transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .cta:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(0,0,0,0.25); }
    .visual {
      position: relative;
      min-height: 420px;
      border-radius: 0;
      overflow: hidden;
      background: color-mix(in srgb, var(--primary) 70%, black);
      animation: rise 0.9s ease both;
    }
    .visual img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      min-height: 420px;
    }
    .copy { animation: fade 0.8s ease 0.15s both; }
    @keyframes rise {
      from { opacity: 0; transform: translateY(24px) scale(1.02); }
      to { opacity: 1; transform: none; }
    }
    @keyframes fade {
      from { opacity: 0; transform: translateY(12px); }
      to { opacity: 1; transform: none; }
    }
    .meta {
      margin-top: 2rem;
      font-size: 0.8rem;
      opacity: 0.55;
    }
  </style>
</head>
<body>
  <main class="hero">
    <section class="copy">
      <p class="brand">{{ brand }}</p>
      <h1 class="headline">{{ headline }}</h1>
      <p class="sub">{{ sub }}</p>
      <a class="cta" href="#offer">{{ cta }}</a>
      <p class="meta">Auto-deployed by AdzMate · Campaign {{ campaign_id }}</p>
    </section>
    <section class="visual">
      {% if image_url %}
      <img src="{{ image_url }}" alt="{{ product }}" />
      {% endif %}
    </section>
  </main>
</body>
</html>
"""
)


def deploy_landing_page(
    campaign_id: str,
    brand_name: str,
    product_name: str,
    brief: str,
    headline: str | None,
    cta: str | None,
    primary: str,
    accent: str,
    creative_image_url: str | None,
) -> dict:
    out_dir = settings.previews_dir / campaign_id
    out_dir.mkdir(parents=True, exist_ok=True)
    html = LANDING_TEMPLATE.render(
        brand=brand_name,
        product=product_name,
        headline=headline or f"Meet {product_name}",
        sub=brief[:220],
        cta=cta or "Shop Now",
        primary=primary,
        accent=accent,
        image_url=creative_image_url,
        campaign_id=campaign_id,
    )
    index = out_dir / "index.html"
    index.write_text(html, encoding="utf-8")

    preview_url = f"{settings.public_base_url}/previews/{campaign_id}/"
    cloudfront_url = f"https://d{campaign_id[:8]}.cloudfront.net/{campaign_id}"

    return {
        "path": str(index),
        "preview_url": preview_url,
        "cloudfront_url": cloudfront_url,
        "status": "deployed",
    }
