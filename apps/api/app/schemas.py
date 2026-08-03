from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str
    client_name: str = "AdzMate Client"
    brand_name: str
    product_name: str
    brief: str = ""
    product_description: str = ""
    product_url: Optional[str] = None
    goal: str = "conversions"
    objective: str = "sales"  # sales | leads | traffic | engagement
    budget: float = 5000.0
    daily_budget: float = 50.0
    duration_days: int = 14
    target_country: str = ""
    target_location: str = ""
    age_min: int = 18
    age_max: int = 65
    gender: str = "all"  # all | male | female
    language: str = "en"
    platforms: list[str] = Field(default_factory=lambda: ["meta", "google", "tiktok"])
    brand_primary: str = "#1877F2"
    brand_accent: str = "#0866FF"
    scenario: str = "healthy"


class CampaignOut(BaseModel):
    id: str
    workspace_id: str | None = None
    name: str
    client_name: str
    brand_name: str
    product_name: str
    brief: str
    product_description: str = ""
    product_url: Optional[str] = None
    goal: str
    objective: str = "sales"
    budget: float
    daily_budget: float = 50.0
    duration_days: int = 14
    target_country: str = ""
    target_location: str = ""
    age_min: int = 18
    age_max: int = 65
    gender: str = "all"
    language: str = "en"
    platforms: list[str]
    brand_primary: str
    brand_accent: str
    scenario: str
    status: str
    product_image_url: Optional[str] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_confidence: Optional[float] = None
    landing_page_url: Optional[str] = None
    cloudfront_url: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    publish_status: str = "none"
    auto_pause_enabled: bool = True
    meta_structure: dict[str, Any] = Field(default_factory=dict)
    audiences: dict[str, Any] = Field(default_factory=dict)
    optimization: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class WorkspaceOut(BaseModel):
    id: str
    name: str
    role: str
    created_at: datetime


class MeOut(BaseModel):
    id: str
    email: Optional[str] = None
    auth_enabled: bool
    workspaces: list[WorkspaceOut]


class WorkspaceCreate(BaseModel):
    name: str = "My Workspace"


class BusinessCreate(BaseModel):
    name: str
    legal_name: str | None = None
    website: str | None = None
    industry: str | None = None
    country: str | None = None
    timezone: str = "UTC"
    contact_email: str | None = None
    notes: str | None = None


class BusinessUpdate(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    website: str | None = None
    industry: str | None = None
    country: str | None = None
    timezone: str | None = None
    contact_email: str | None = None
    notes: str | None = None


class BusinessOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    legal_name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    timezone: str = "UTC"
    contact_email: Optional[str] = None
    logo_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    meta_status: Optional[str] = None
    selected_page_id: Optional[str] = None
    selected_instagram_id: Optional[str] = None
    selected_ad_account_id: Optional[str] = None


class MetaPageOut(BaseModel):
    page_id: str
    name: str
    category: Optional[str] = None
    picture_url: Optional[str] = None
    selected: bool = False


class MetaInstagramOut(BaseModel):
    ig_user_id: str
    username: str
    name: Optional[str] = None
    page_id: Optional[str] = None
    profile_picture_url: Optional[str] = None
    selected: bool = False


class MetaAdAccountOut(BaseModel):
    ad_account_id: str
    name: str
    currency: Optional[str] = None
    timezone_name: Optional[str] = None
    account_status: Optional[str] = None
    selected: bool = False


class MetaConnectionOut(BaseModel):
    id: str
    business_id: str
    status: str
    meta_user_id: Optional[str] = None
    meta_user_name: Optional[str] = None
    scopes: str = ""
    oauth_configured: bool = False
    selected_page_id: Optional[str] = None
    selected_instagram_id: Optional[str] = None
    selected_ad_account_id: Optional[str] = None
    pages: list[MetaPageOut] = Field(default_factory=list)
    instagram_accounts: list[MetaInstagramOut] = Field(default_factory=list)
    ad_accounts: list[MetaAdAccountOut] = Field(default_factory=list)
    connected_at: datetime
    updated_at: datetime


class MetaSelectionUpdate(BaseModel):
    page_id: str | None = None
    instagram_id: str | None = None
    ad_account_id: str | None = None


class AgentRunOut(BaseModel):
    id: str
    campaign_id: str
    agent: str
    health: str
    payload: dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class SignalOut(BaseModel):
    campaign_id: str
    creative_ready: float
    brand_sentiment: float
    roas: float
    spend_burn: float
    spend: float
    updated_at: datetime


class RecommendationOut(BaseModel):
    id: str
    campaign_id: str
    type: str
    status: str
    title: str
    detail: str
    created_at: datetime


class ApprovalAction(BaseModel):
    action: str


class DemoTickRequest(BaseModel):
    event: str = "negative_flood"


class AudienceSelectRequest(BaseModel):
    selected_ids: list[str] = Field(default_factory=list)


class OptimizationUpdateRequest(BaseModel):
    rules: list[dict[str, Any]] | None = None
    targets: dict[str, float] | None = None
    enabled: bool | None = None


class OptimizationTickRequest(BaseModel):
    scenario: str = "mixed"  # mixed | decline | healthy
    days: int = 1


class AutoPauseUpdate(BaseModel):
    enabled: bool = True


class ActionEventOut(BaseModel):
    id: str
    campaign_id: str
    actor: str
    action: str
    summary: str
    detail: Optional[str] = None
    level: str = "info"
    created_at: datetime


class CampaignDetail(BaseModel):
    campaign: CampaignOut
    agents: list[AgentRunOut]
    signals: Optional[SignalOut] = None
    recommendations: list[RecommendationOut]
    timeline: list[ActionEventOut] = Field(default_factory=list)
