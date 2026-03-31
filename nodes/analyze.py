import json
from pathlib import Path

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import MenuState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt_text = Path(__file__).resolve().parent.parent / "prompts" / "analyze_prompt.txt"
system_prompt = prompt_text.read_text(encoding="utf-8")

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", "{user_input}"),
# ])

# 튜플 방식("system", ...) 대신 SystemMessage 객체로 감싸줍니다.
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt), # 👈 변수 취급하지 말고 원본 그대로 쓰라는 뜻!
    ("human", "{user_input}"),
])

def _parse_response(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]
    return json.loads(content)


def analyze_preferences(state: MenuState) -> dict:
    print("\n🔍 선호도를 분석하고 있습니다...")
    chain = prompt | llm
    result = chain.invoke({"user_input": state["user_input"]})
    parsed = _parse_response(result.content)

    return {
        "mood": parsed.get("mood", "보통"),
        "preferred_taste": parsed.get("preferred_taste", []),
        "cooking_difficulty": parsed.get("cooking_difficulty", "보통"),
        "dietary_restrictions": parsed.get("dietary_restrictions", []),
        "has_restrictions": len(parsed.get("dietary_restrictions", [])) > 0,
    }
