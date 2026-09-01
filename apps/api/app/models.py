from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(20), default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), index=True, default="")
    name: Mapped[str] = mapped_column(String(200))
    client_name: Mapped[str] = mapped_column(String(200))
    brand_name: Mapped[str] = mapped_column(String(200))
    product_name: Mapped[str] = mapped_column(String(200))
    brief: Mapped[str] = mapped_column(Text)
    product_description: Mapped[str] = mapped_column(Text, default="")
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    goal: Mapped[str] = mapped_column(String(100), default="conversions")
    objective: Mapped[str] = mapped_column(String(40), default="sales")
    budget: Mapped[float] = mapped_column(Float, default=5000.0)
    daily_budget: Mapped[float] = mapped_column(Float, default=50.0)
    duration_days: Mapped[int] = mapped_column(Integer, default=14)
    target_country: Mapped[str] = mapped_column(String(120), default="")
    target_location: Mapped[str] = mapped_column(String(200), default="")
    age_min: Mapped[int] = mapped_column(Integer, default=18)
    age_max: Mapped[int] = mapped_column(Integer, default=65)
    gender: Mapped[str] = mapped_column(String(20), default="all")
    language: Mapped[str] = mapped_column(String(40), default="en")
    platforms_json: Mapped[str] = mapped_column(Text, default="[]")
    brand_primary: Mapped[str] = mapped_column(String(20), default="#0B3D2E")
    brand_accent: Mapped[str] = mapped_column(String(20), default="#F4A261")
    scenario: Mapped[str] = mapped_column(String(40), default="healthy")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    product_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    landing_page_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cloudfront_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    mock_ads_json: Mapped[str] = mapped_column(Text, default="{}")
    meta_structure_json: Mapped[str] = mapped_column(Text, default="{}")
    audiences_json: Mapped[str] = mapped_column(Text, default="{}")
    optimization_json: Mapped[str] = mapped_column(Text, default="{}")
    publish_status: Mapped[str] = mapped_column(String(40), default="none")
    auto_pause_enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    @property
    def platforms(self) -> list[str]:
        return json.loads(self.platforms_json or "[]")

    @platforms.setter
    def platforms(self, value: list[str]) -> None:
        self.platforms_json = json.dumps(value)

    @property
    def warnings(self) -> list[str]:
        return json.loads(self.warnings_json or "[]")

    @warnings.setter
    def warnings(self, value: list[str]) -> None:
        self.warnings_json = json.dumps(value)

    @property
    def mock_ads(self) -> dict:
        return json.loads(self.mock_ads_json or "{}")

    @mock_ads.setter
    def mock_ads(self, value: dict) -> None:
        self.mock_ads_json = json.dumps(value)

    @property
    def meta_structure(self) -> dict:
        return json.loads(self.meta_structure_json or "{}")

    @meta_structure.setter
    def meta_structure(self, value: dict) -> None:
        self.meta_structure_json = json.dumps(value)

    @property
    def audiences(self) -> dict:
        return json.loads(self.audiences_json or "{}")

    @audiences.setter
    def audiences(self, value: dict) -> None:
        self.audiences_json = json.dumps(value)

    @property
    def optimization(self) -> dict:
        return json.loads(self.optimization_json or "{}")

    @optimization.setter
    def optimization(self, value: dict) -> None:
        self.optimization_json = json.dumps(value)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(36), index=True)
    agent: Mapped[str] = mapped_column(String(40))
    health: Mapped[str] = mapped_column(String(20), default="pending")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def payload(self) -> dict:
        return json.loads(self.payload_json or "{}")

    @payload.setter
    def payload(self, value: dict) -> None:
        self.payload_json = json.dumps(value)


class SignalSnapshot(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    creative_ready: Mapped[float] = mapped_column(Float, default=0.0)
    brand_sentiment: Mapped[float] = mapped_column(Float, default=0.5)
    roas: Mapped[float] = mapped_column(Float, default=0.0)
    spend_burn: Mapped[float] = mapped_column(Float, default=0.0)
    spend: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(36), index=True)
    type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    title: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ActionEvent(Base):
    """Audit trail: agent decisions and system actions for a campaign."""

    __tablename__ = "action_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(36), index=True)
    actor: Mapped[str] = mapped_column(String(40))  # creative|sentiment|strategy|aggregator|system|manager
    action: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(String(280))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[str] = mapped_column(String(20), default="info")  # info|success|warning|action
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Business(Base):
    """Company / brand profile inside a workspace."""

    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(200))
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    website: Mapped[str | None] = mapped_column(String(300), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MetaConnection(Base):
    """OAuth connection from a business to Meta (Facebook)."""

    __tablename__ = "meta_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    business_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    workspace_id: Mapped[str] = mapped_column(String(36), index=True)
    meta_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta_user_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str] = mapped_column(String(40), default="bearer")
    scopes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="connected")
    selected_page_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_instagram_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_ad_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MetaPage(Base):
    __tablename__ = "meta_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    connection_id: Mapped[str] = mapped_column(String(36), index=True)
    page_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    page_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    picture_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MetaInstagramAccount(Base):
    __tablename__ = "meta_instagram_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    connection_id: Mapped[str] = mapped_column(String(36), index=True)
    ig_user_id: Mapped[str] = mapped_column(String(64), index=True)
    username: Mapped[str] = mapped_column(String(200))
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    page_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MetaAdAccount(Base):
    __tablename__ = "meta_ad_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    connection_id: Mapped[str] = mapped_column(String(36), index=True)
    ad_account_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(200))
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    timezone_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    account_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
