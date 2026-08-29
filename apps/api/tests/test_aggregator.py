from app.config import settings
from app.services.aggregator import aggregate_signals


def test_aggregate_launch():
    result = aggregate_signals(
        creative={"creative_ready": 0.85},
        sentiment={"brand_sentiment": 0.7},
        strategy={"roas": 2.0, "spend": 100, "spend_burn": 0.2},
        warnings=[],
    )
    assert result["decision"] == "LAUNCH"
    assert result["decision_confidence"] >= 0.78


def test_aggregate_halt_low_roas():
    result = aggregate_signals(
        creative={"creative_ready": 0.9},
        sentiment={"brand_sentiment": 0.8},
        strategy={"roas": 0.8, "spend": 500, "spend_burn": 0.6},
        warnings=[],
    )
    assert result["decision"] == "HALT"
    assert settings.roas_floor in (1.5,)


def test_aggregate_hold_soft_sentiment():
    result = aggregate_signals(
        creative={"creative_ready": 0.85},
        sentiment={"brand_sentiment": 0.45},
        strategy={"roas": 2.5, "spend": 200, "spend_burn": 0.3},
        warnings=[],
    )
    assert result["decision"] == "HOLD"
