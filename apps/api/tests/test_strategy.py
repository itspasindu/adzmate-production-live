from app.agents.strategy import apply_demo_tick, apply_pause, compute_metrics, load_base_ads


def test_compute_metrics_healthy():
    ads = load_base_ads("healthy")
    metrics = compute_metrics(ads)
    assert metrics["roas"] >= 1.5
    assert metrics["spend"] > 0


def test_compute_metrics_poor_roas():
    ads = load_base_ads("poor_roas")
    metrics = compute_metrics(ads)
    assert metrics["roas"] < 1.5


def test_apply_pause_marks_platforms():
    ads = load_base_ads("healthy")
    paused = apply_pause(ads)
    assert paused["meta"]["status"] == "paused"


def test_demo_tick_spend_spike():
    ads = load_base_ads("healthy")
    spiked = apply_demo_tick(ads, "spend_spike")
    after = compute_metrics(spiked)
    assert after["roas"] < compute_metrics(ads)["roas"]
