from app.integrations.meta.metrics_sync import _is_simulated_meta_id


def test_simulated_meta_ids():
    assert _is_simulated_meta_id("meta_camp_abc123") is True
    assert _is_simulated_meta_id("draft_camp_xyz") is True
    assert _is_simulated_meta_id("120330000000000") is False
    assert _is_simulated_meta_id(None) is True
