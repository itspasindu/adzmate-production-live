"""Seed demo campaigns for judging walkthrough.

Usage:
  python -m app.seed           # skip if already seeded
  python -m app.seed --force   # wipe campaigns in demo workspace and reseed
"""
from __future__ import annotations

import asyncio
import sys
import uuid

from PIL import Image, ImageDraw
from sqlalchemy import delete, select

from app.agents.strategy import load_base_ads
from app.config import settings
from app.db import SessionLocal, init_db
from app.models import ActionEvent, AgentRun, Campaign, Recommendation, SignalSnapshot, Workspace, WorkspaceMember
from app.services.orchestrator import run_pipeline


def _make_product_image(path, primary: str, accent: str, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (800, 800), (245, 240, 232))
    draw = ImageDraw.Draw(img)

    def hex_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    draw.rounded_rectangle([140, 140, 660, 660], radius=40, fill=hex_rgb(primary))
    draw.ellipse([250, 250, 550, 550], fill=hex_rgb(accent))
    draw.rectangle([330, 330, 470, 520], fill=(255, 255, 255))
    img.save(path)


SEEDS = [
    {
        "name": "Aurora Bottle Launch",
        "client_name": "Northwave Agency",
        "brand_name": "Lumen",
        "product_name": "Aurora Bottle",
        "product_description": "Premium insulated bottle that stays cold 24 hours. Soft-touch finish for urban professionals.",
        "product_url": "https://example.com/aurora-bottle",
        "brief": "Launch a premium insulated bottle for urban professionals. Emphasize all-day cold and refined design.",
        "scenario": "healthy",
        "objective": "sales",
        "brand_primary": "#0B3D2E",
        "brand_accent": "#C45C26",
        "daily_budget": 80,
        "duration_days": 14,
        "target_country": "United States",
        "target_location": "New York",
        "age_min": 25,
        "age_max": 44,
        "gender": "all",
        "budget": 8000,
    },
    {
        "name": "Pulse Buds Rescue",
        "client_name": "Beacon Media",
        "brand_name": "Nexo",
        "product_name": "Pulse Buds",
        "product_description": "Wireless earbuds with ANC. Campaign is burning budget with weak ROAS across Meta and TikTok.",
        "product_url": "https://example.com/pulse-buds",
        "brief": "Recover performance on wireless earbuds after ROAS collapse across Meta and TikTok.",
        "scenario": "poor_roas",
        "objective": "sales",
        "brand_primary": "#1B2A4A",
        "brand_accent": "#E8B86D",
        "daily_budget": 120,
        "duration_days": 10,
        "target_country": "United States",
        "target_location": "California",
        "age_min": 18,
        "age_max": 34,
        "gender": "all",
        "budget": 12000,
    },
    {
        "name": "Cedar Desk Mixed",
        "client_name": "Harbor Collective",
        "brand_name": "Forma",
        "product_name": "Cedar Desk",
        "product_description": "Modular standing desk in cedar finish. Creatives look strong but social sentiment is mixed.",
        "product_url": "https://example.com/cedar-desk",
        "brief": "Promote a modular standing desk. Creative is strong but social sentiment is mixed — needs manager call.",
        "scenario": "mixed_sentiment",
        "objective": "traffic",
        "brand_primary": "#3D2914",
        "brand_accent": "#D97706",
        "daily_budget": 55,
        "duration_days": 21,
        "target_country": "United Kingdom",
        "target_location": "London",
        "age_min": 28,
        "age_max": 50,
        "gender": "all",
        "budget": 6500,
    },
    {
        "name": "TrailRun Shoes Sprint",
        "client_name": "Northwave Agency",
        "brand_name": "Peakline",
        "product_name": "TrailRun Shoes",
        "product_description": "Lightweight trail running shoes for marathon training. Grip on wet rock, all-day cushion.",
        "product_url": "https://example.com/trailrun",
        "brief": "Scale a healthy trail-shoe launch with $20/day creative tests and auto-optimization story.",
        "scenario": "healthy",
        "objective": "sales",
        "brand_primary": "#1877F2",
        "brand_accent": "#0866FF",
        "daily_budget": 20,
        "duration_days": 14,
        "target_country": "United States",
        "target_location": "Colorado",
        "age_min": 22,
        "age_max": 45,
        "gender": "all",
        "budget": 280,
    },
]


async def _ensure_workspace(db, workspace_id: str, name: str, user_id: str = "local-demo") -> None:
    ws = (await db.execute(select(Workspace).where(Workspace.id == workspace_id))).scalar_one_or_none()
    if not ws:
        db.add(Workspace(id=workspace_id, name=name, created_by=user_id))
        db.add(
            WorkspaceMember(
                id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                user_id=user_id,
                role="owner",
            )
        )
        await db.commit()


async def _clear_workspace_campaigns(db, workspace_id: str) -> None:
    ids = (
        await db.execute(select(Campaign.id).where(Campaign.workspace_id == workspace_id))
    ).scalars().all()
    if not ids:
        return
    for model in (ActionEvent, AgentRun, Recommendation, SignalSnapshot):
        await db.execute(delete(model).where(model.campaign_id.in_(ids)))
    await db.execute(delete(Campaign).where(Campaign.workspace_id == workspace_id))
    await db.commit()
    print(f"Cleared {len(ids)} campaigns from workspace {workspace_id}")


async def _clear_all_campaigns(db) -> None:
    """Wipe every campaign (all workspaces) so judging list is only the seed set."""
    ids = (await db.execute(select(Campaign.id))).scalars().all()
    if not ids:
        print("No existing campaigns to clear")
        return
    for model in (ActionEvent, AgentRun, Recommendation, SignalSnapshot):
        await db.execute(delete(model).where(model.campaign_id.in_(ids)))
    await db.execute(delete(Campaign))
    await db.commit()
    print(f"Cleared {len(ids)} campaigns across all workspaces")


async def seed(force: bool = False) -> None:
    await init_db()
    async with SessionLocal() as db:
        workspace_id = settings.demo_workspace_id
        await _ensure_workspace(db, workspace_id, "Local Demo — Agency HQ")

        # Second client workspace for multi-agency story
        client_ws = "00000000-0000-4000-8000-000000000002"
        await _ensure_workspace(db, client_ws, "Beacon Media (client)", user_id="local-demo")

        existing = (
            await db.execute(select(Campaign).where(Campaign.workspace_id == workspace_id))
        ).scalars().first()
        if existing and not force:
            print("Database already seeded — skipping (use --force to reseed)")
            return

        if force:
            # Clears leftover personal-workspace demos too (not only Local Demo / Beacon)
            await _clear_all_campaigns(db)

        for item in SEEDS:
            wid = client_ws if item["client_name"] == "Beacon Media" else workspace_id
            cid = str(uuid.uuid4())
            img_path = settings.uploads_dir / cid / "product.png"
            _make_product_image(img_path, item["brand_primary"], item["brand_accent"], item["product_name"])
            campaign = Campaign(
                id=cid,
                workspace_id=wid,
                name=item["name"],
                client_name=item["client_name"],
                brand_name=item["brand_name"],
                product_name=item["product_name"],
                brief=item["brief"],
                product_description=item.get("product_description") or item["brief"],
                product_url=item.get("product_url"),
                goal="conversions" if item.get("objective") == "sales" else item.get("objective", "conversions"),
                objective=item.get("objective") or "sales",
                budget=item["budget"],
                daily_budget=item.get("daily_budget") or 50,
                duration_days=item.get("duration_days") or 14,
                target_country=item.get("target_country") or "",
                target_location=item.get("target_location") or "",
                age_min=item.get("age_min") or 18,
                age_max=item.get("age_max") or 65,
                gender=item.get("gender") or "all",
                language="en",
                brand_primary=item["brand_primary"],
                brand_accent=item["brand_accent"],
                scenario=item["scenario"],
                status="received",
                product_image_path=str(img_path),
                mock_ads=load_base_ads(item["scenario"]),
                auto_pause_enabled=True,
            )
            campaign.platforms = ["meta", "google", "tiktok"]
            db.add(campaign)
            await db.commit()
            await db.refresh(campaign)
            print(f"Running pipeline for {campaign.name} ({campaign.scenario}) in {wid[-4:]}...")
            await run_pipeline(db, campaign)
            print(f"  -> decision={campaign.decision} status={campaign.status}")

    print("Seed complete. Tip: switch workspaces in the sidebar to see multi-client demos.")


if __name__ == "__main__":
    force = "--force" in sys.argv
    asyncio.run(seed(force=force))
