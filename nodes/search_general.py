import json
from pathlib import Path

from state import MenuState

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "menu_data.json"


def _load_menus() -> list[dict]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def search_general(state: MenuState) -> dict:
    print("🍲 메뉴를 탐색하고 있습니다...")
    menus = _load_menus()
    tastes = state["preferred_taste"]
    mood = state["mood"]
    difficulty = state["cooking_difficulty"]

    # 1차: taste + mood_tags 관련도 점수
    def score(m):
        taste_score = sum(1 for t in tastes if t in m.get("taste", [])) * 2
        mood_score = 1 if mood in m.get("mood_tags", []) else 0
        return taste_score + mood_score

    scored = sorted(menus, key=score, reverse=True)

    # 2차: cooking_difficulty 필터 — 해당 난이도 우선, 없으면 전체
    if difficulty:
        difficulty_filtered = [m for m in scored if m.get("cooking_difficulty") == difficulty]
        if difficulty_filtered:
            scored = difficulty_filtered

    return {"menu_candidates": scored[:10]}
