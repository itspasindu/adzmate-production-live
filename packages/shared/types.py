from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    RECEIVED = "received"
    AGENTS_RUNNING = "agents_running"
    AGGREGATING = "aggregating"
    AWAITING_APPROVAL = "awaiting_approval"
    DEPLOYING = "deploying"
    LIVE = "live"
    HALTED = "halted"
    FAILED = "failed"
    DEGRADED = "degraded"


class DecisionType(str, Enum):
    LAUNCH = "LAUNCH"
    HALT = "HALT"
    HOLD = "HOLD"


class AgentName(str, Enum):
    CREATIVE = "creative"
    SENTIMENT = "sentiment"
    STRATEGY = "strategy"


class AgentHealth(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"
    PENDING = "pending"
    RUNNING = "running"


class RecommendationType(str, Enum):
    LAUNCH = "launch"
    HALT = "halt"
    PAUSE_ADS = "pause_ads"
    RESUME_ADS = "resume_ads"
    DEPLOY = "deploy"


class RecommendationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CampaignCreate(BaseModel):
    name: str
    client_name: str = "AdzMate Client"
    brand_name: str
    product_name: str
    brief: str = ""
    product_description: str = ""
    product_url: Optional[str] = None
    goal: str = "conversions"
    objective: str = "sales"
    budget: float = 5000.0
    daily_budget: float = 50.0
    duration_days: int = 14
    target_country: str = ""
    target_location: str = ""
    age_min: int = 18
    age_max: int = 65
    gender: str = "all"
    language: str = "en"
    platforms: list[str] = Field(default_factory=lambda: ["meta", "google", "tiktok"])
    brand_primary: str = "#1877F2"
    brand_accent: str = "#0866FF"
    scenario: str = "healthy"  # healthy | poor_roas | mixed_sentiment


class CampaignOut(BaseModel):
    id: str
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
    status: CampaignStatus
    product_image_url: Optional[str] = None
    decision: Optional[DecisionType] = None
    decision_reason: Optional[str] = None
    decision_confidence: Optional[float] = None
    landing_page_url: Optional[str] = None
    cloudfront_url: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentRunOut(BaseModel):
    id: str
    campaign_id: str
    agent: AgentName
    health: AgentHealth
    payload: dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


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
    type: RecommendationType
    status: RecommendationStatus
    title: str
    detail: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalAction(BaseModel):
    action: str  # approve | reject


class DemoTickRequest(BaseModel):
    event: str = "negative_flood"  # negative_flood | spend_spike | recover


class CampaignDetail(BaseModel):
    campaign: CampaignOut
    agents: list[AgentRunOut]
    signals: Optional[SignalOut] = None
    recommendations: list[RecommendationOut]
