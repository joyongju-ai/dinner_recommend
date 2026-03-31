# from pathlib import Path

# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# from state import MenuState

# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# prompt_text = Path(__file__).resolve().parent.parent / "prompts" / "recommend_prompt.txt"
# system_prompt = prompt_text.read_text(encoding="utf-8")

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", "위 정보를 바탕으로 최적의 메뉴를 추천해주세요."),
# ])

# POSITIVE = ["만족", "네", "좋아", "응", "그래", "yes", "좋아요", "괜찮"]


# def generate_recommendation(state: MenuState) -> dict:
#     top3 = state["menu_candidates"][:3]
#     candidates_str = "\n".join(
#         f"- {c['name']}: {c.get('description', '')} ({c.get('taste', '')})"
#         for c in top3
#     )
#     restrictions = ", ".join(state["dietary_restrictions"]) if state["dietary_restrictions"] else "없음"

#     chain = prompt | llm
#     result = chain.invoke({
#         "mood": state["mood"],
#         "preferred_taste": ", ".join(state["preferred_taste"]),
#         "cooking_difficulty": state["cooking_difficulty"],
#         "dietary_restrictions": restrictions,
#         "menu_candidates": candidates_str,
#     })

#     recommendation = result.content
#     #print(f"\n 추천 메뉴:\n{recommendation}")

#     #user_answer = input("\n이 추천이 마음에 드시나요? (만족/불만족)\n> ").strip()
#     feedback = "satisfied" if any(p in user_answer for p in POSITIVE) else "unsatisfied"

#     return {
#         "recommendation": recommendation,
#         "feedback": feedback,
#         "iteration_count": state["iteration_count"] + 1,
#     }


from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import MenuState
import random

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt_text = Path(__file__).resolve().parent.parent / "prompts" / "recommend_prompt.txt"
system_prompt = prompt_text.read_text(encoding="utf-8")

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "위 정보를 바탕으로 최적의 메뉴를 추천해주세요."),
])

# 웹 UI에서는 버튼으로 처리하므로 POSITIVE 리스트는 더 이상 필요 없지만 두셔도 무방합니다.

# def generate_recommendation(state: MenuState) -> dict:
#     top3 = state["menu_candidates"][:3]
#     candidates_str = "\n".join(
#         f"- {c['name']}: {c.get('description', '')} ({c.get('taste', '')})"
#         for c in top3
#     )
#     restrictions = ", ".join(state["dietary_restrictions"]) if state["dietary_restrictions"] else "없음"

#     chain = prompt | llm
#     result = chain.invoke({
#         "mood": state["mood"],
#         "preferred_taste": ", ".join(state["preferred_taste"]),
#         "cooking_difficulty": state["cooking_difficulty"],
#         "dietary_restrictions": restrictions,
#         "menu_candidates": candidates_str,
#     })

#     # 터미널 출력(print)과 입력(input) 로직을 모두 제거하고 바로 반환합니다.
#     recommendation = result.content

#     return {
#         "recommendation": recommendation,
#         "feedback": "", # 피드백은 app.py에서 버튼을 누를 때 갱신되므로 여기선 빈 문자열로 둡니다.
#         "iteration_count": state["iteration_count"] + 1,
#     }

def generate_recommendation(state: MenuState) -> dict:
    # 💡 1. 핵심: 원본 상태(state)를 훼손하지 않기 위해 list()로 복사본을 만듭니다.
    candidates_copy = list(state["menu_candidates"])
    
    # 💡 2. 복사본을 마구 섞습니다. (이제 LangGraph의 원본 데이터는 안전합니다!)
    random.shuffle(candidates_copy)
    
    # 💡 3. 섞인 복사본에서 상위 3개를 안전하게 뽑아냅니다.
    top3 = candidates_copy[:3]
    
    candidates_str = "\n".join(
        f"- {c['name']}: {c.get('description', '')} ({c.get('taste', '')})"
        for c in top3
    )

    restrictions = ", ".join(state["dietary_restrictions"]) if state["dietary_restrictions"] else "없음"
    history_str = ", ".join(state.get("history", [])) if state.get("history") else "없음"

    # 💡 이전 추천 기록 가져오기
    old_history = state.get("history", [])
    history_str = ", ".join(old_history) if old_history else "없음"
    
    chain = prompt | llm
    result = chain.invoke({
        "mood": state["mood"],
        "preferred_taste": ", ".join(state["preferred_taste"]),
        "cooking_difficulty": state["cooking_difficulty"],
        "dietary_restrictions": restrictions,
        "menu_candidates": candidates_str,
        "iteration_count": state["iteration_count"],
        "history": history_str
    })

     # 터미널 출력(print)과 입력(input) 로직을 모두 제거하고 바로 반환합니다.
    recommendation = result.content

    # 💡 [핵심 추가] 이번에 추천한 3개 메뉴 이름을 히스토리에 추가
    current_names = [c['name'] for c in top3]
    new_history = old_history + current_names

    return {
        "recommendation": recommendation,
        "feedback": "", # 피드백은 app.py에서 버튼을 누를 때 갱신되므로 여기선 빈 문자열로 둡니다.
        "iteration_count": state["iteration_count"] + 1,
    }