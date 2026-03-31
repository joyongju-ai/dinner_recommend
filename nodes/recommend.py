import json
from pathlib import Path
import random

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import MenuState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "recommend_prompt.txt"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "menu_data.json"

system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "위 정보를 바탕으로 최적의 메뉴를 추천해주세요."),
])


def _load_all_menus() -> list[dict]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _format_menu(m: dict) -> str:
    return f"- {m['name']}: {m.get('description', '')} ({m.get('taste', '')})"


def generate_recommendation(state: MenuState) -> dict:
    old_history = state.get("history", [])
    candidates = [c for c in state["menu_candidates"] if c["name"] not in old_history]
    random.shuffle(candidates)
    top = candidates[:5]

    candidates_str = "\n".join(_format_menu(c) for c in top)

    all_menus = _load_all_menus()
    all_menus = [m for m in all_menus if m["name"] not in old_history]
    all_menus_str = "\n".join(_format_menu(m) for m in all_menus)

    restrictions = ", ".join(state["dietary_restrictions"]) if state["dietary_restrictions"] else "없음"
    history_str = ", ".join(old_history) if old_history else "없음"

    chain = prompt | llm
    result = chain.invoke({
        "user_input": state["user_input"],
        "mood": state["mood"],
        "preferred_taste": ", ".join(state["preferred_taste"]),
        "cooking_difficulty": state["cooking_difficulty"],
        "dietary_restrictions": restrictions,
        "menu_candidates": candidates_str,
        "all_menus": all_menus_str,
        "iteration_count": state["iteration_count"],
        "history": history_str,
    })

    recommendation = result.content
    all_menu_names = [m["name"] for m in _load_all_menus()]
    recommended = [n for n in all_menu_names if n in recommendation]
    new_history = old_history + recommended

    return {
        "recommendation": recommendation,
        "feedback": "",
        "iteration_count": state["iteration_count"] + 1,
        "history": new_history,
    }
