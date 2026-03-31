import json
from pathlib import Path

from state import MenuState

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "menu_data.json"


def _load_menus() -> list[dict]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def search_restricted(state: MenuState) -> dict:
    print("🍲 식이 제한을 고려하여 메뉴를 탐색하고 있습니다...")
    menus = _load_menus()
    restrictions = state["dietary_restrictions"]
    tastes = state["preferred_taste"]
    mood = state["mood"]

    # 1차: dietary_tags 매칭 — 사용자 제한 항목이 메뉴 태그에 모두 포함
    filtered = [
        m for m in menus
        if all(r in m.get("dietary_tags", []) for r in restrictions)
    ]

    # 2차: allergens 제외 — 사용자 알레르기 항목이 메뉴에 있으면 제외
    allergens_to_avoid = [
        r.replace("없음", "") for r in restrictions
    ]
    filtered = [
        m for m in filtered
        if not any(a in m.get("allergens", []) for a in allergens_to_avoid if a)
    ]

    # 3차: 관련도 점수 계산
    def score(m):
        taste_score = sum(1 for t in tastes if t in m.get("taste", [])) * 2
        mood_score = 1 if mood in m.get("mood_tags", []) else 0
        return taste_score + mood_score

    scored = sorted(filtered, key=score, reverse=True)

    # 폴백: 결과 0개면 taste만으로 재필터링
    if not scored:
        scored = sorted(menus, key=score, reverse=True)

    return {"menu_candidates": scored[:10]}
