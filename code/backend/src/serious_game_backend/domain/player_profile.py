"""Fixed player identities and cosmetic signing milestones."""
from __future__ import annotations

import re

SIGNING_MILESTONES = (1, 3, 10, 18, 30, 36)
SIGNING_REWARD_TITLES = {
    1: "新官上任试试水~",
    3: "新手村毕业",
    10: "先天签约圣体",
    18: "优势即将在我",
    30: "来都来了，再签六户",
    36: "县长so easy！",
}

FEMALE_TEXT_REWRITES = (
    (
        "县长和嫂夫人",
        "县长",
    ),
    (
        "赵建国拍着你的肩膀叫兄弟。",
        "赵建国拍了拍你的肩膀，叫了一声李县长。",
    ),
)


def player_profile(session) -> dict:
    female = getattr(session, "player_gender", "male") == "female"
    return {
        "gender": "female" if female else "male",
        "name": "李琳" if female else "李致远",
        "character_id": "player_li_lin" if female else "player_li_zhiyuan",
        "role": "云溪县县长、县委副书记",
        "portrait_path": "/characters/player_li_lin.png" if female else "/characters/player_li_zhiyuan.png",
    }


def player_identity(session) -> str:
    profile = player_profile(session)
    return f"云溪县县长{profile['name']}（{'女' if profile['gender'] == 'female' else '男'}）"


def player_gender_from_identity_text(identity_text: str | None) -> str | None:
    """Read the explicit gender marker included in model-facing player identity."""
    value = identity_text or ""
    match = re.search(r"云溪县县长[^（\r\n]{0,20}（([男女])）", value)
    return {"女": "female", "男": "male"}.get(match.group(1)) if match else None


def player_text_for_gender(text: str | None, gender: str | None) -> str | None:
    """Resolve gender-specific player wording without changing package source."""
    if text is None or gender != "female":
        return text
    resolved = text.replace("李致远", "李琳")
    # Only resolve reviewed player-address forms; idioms such as “宁静致远” must remain intact.
    for source, replacement in (
        ("致远同志", "李琳同志"),
        ("“致远”", "“李琳”"),
        ("‘致远’", "‘李琳’"),
    ):
        resolved = resolved.replace(source, replacement)
    resolved = re.sub(r"(?<!宁静)致远，", "李琳，", resolved)
    for source, replacement in FEMALE_TEXT_REWRITES:
        resolved = resolved.replace(source, replacement)
    return resolved


def player_display_text(session, text: str | None) -> str | None:
    # Presentation only: never rewrite package source, identifiers, or hashes.
    return player_text_for_gender(
        text,
        getattr(session, "player_gender", "male"),
    )


def player_display_value(session, value):
    """Apply the player-gender presentation layer to a player-facing DTO."""
    if isinstance(value, str):
        return player_display_text(session, value)
    if isinstance(value, list):
        return [player_display_value(session, item) for item in value]
    if isinstance(value, tuple):
        return tuple(player_display_value(session, item) for item in value)
    if isinstance(value, dict):
        return {
            key: player_display_value(session, item)
            for key, item in value.items()
        }
    return value


def signing_rewards(session) -> list[dict]:
    signed = session.audited_signed_households()
    return [{
        "reward_id": f"signing_{threshold}",
        "threshold": threshold,
        "title": SIGNING_REWARD_TITLES[threshold],
        "earned": signed >= threshold,
        "acknowledged": str(threshold) in session.signing_reward_receipts,
        "received_day": session.signing_reward_receipts.get(str(threshold), {}).get("received_day"),
    } for threshold in SIGNING_MILESTONES]
