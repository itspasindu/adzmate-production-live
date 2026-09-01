"""Deep links into Meta Ads Manager."""

from __future__ import annotations


def _act_digits(ad_account_id: str) -> str:
    return ad_account_id.removeprefix("act_")


def campaign_url(ad_account_id: str, campaign_id: str) -> str:
    act = _act_digits(ad_account_id)
    return (
        "https://www.facebook.com/adsmanager/manage/campaigns"
        f"?act={act}&selected_campaign_ids={campaign_id}"
    )


def ad_account_url(ad_account_id: str) -> str:
    act = _act_digits(ad_account_id)
    return f"https://www.facebook.com/adsmanager/manage/campaigns?act={act}"
