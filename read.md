# 🍽️ LangGraph 저녁 메뉴 추천 시스템

LangGraph를 활용하여 사용자의 선호도, 식이 제한, 기분 등을 종합적으로 분석해 최적의 저녁 메뉴를 추천하는 AI 에이전트입니다.

## 프로젝트 개요

단순한 랜덤 추천이 아닌, LLM 기반의 대화형 메뉴 추천 시스템입니다. LangGraph의 상태 관리와 조건부 라우팅을 활용하여 사용자 맞춤형 추천을 제공하고, 피드백 루프를 통해 만족할 때까지 재추천이 가능합니다.

## 시스템 아키텍처

```
START
  │
  ▼
사용자 입력 수집 (collect_input)
  │
  ▼
선호도 분석 (analyze_preferences)
  │
  ▼
식이 제한 확인 (conditional_edge)
  ├── 있음 → 제한식 메뉴 탐색 (search_restricted)
  └── 없음 → 일반 메뉴 탐색 (search_general)
  │
  ▼
추천 생성 (generate_recommendation)
  │
  ▼
피드백 확인 (check_satisfaction)
  ├── 만족 → END
  └── 불만족 → 선호도 분석으로 복귀
```

## 주요 기능

- **대화형 입력 수집**: 자연어로 기분, 원하는 맛, 조리 난이도 등을 입력
- **LLM 기반 선호도 분석**: 사용자 입력을 구조화된 선호도 데이터로 변환
- **조건부 라우팅**: 식이 제한(채식, 알레르기, 종교 등) 여부에 따른 분기 처리
- **피드백 루프**: 추천 결과에 불만족 시 선호도를 재분석하여 새로운 메뉴 추천

## 기술 스택

- **Python** 3.10+
- **LangGraph** - 워크플로우 오케스트레이션
- **LangChain** - LLM 체인 구성
- **OpenAI API** (또는 다른 LLM 프로바이더)

## 설치

```bash
pip install langgraph langchain langchain-openai python-dotenv
```

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
OPENAI_API_KEY=your_api_key_here
```

## 프로젝트 구조

```
dinner-recommender/
├── README.md
├── .env
├── requirements.txt
├── main.py                  # 진입점
├── graph.py                 # LangGraph 워크플로우 정의
├── state.py                 # 상태(State) 스키마 정의
├── nodes/
│   ├── __init__.py
│   ├── collect_input.py     # 사용자 입력 수집 노드
│   ├── analyze.py           # 선호도 분석 노드
│   ├── search_restricted.py # 제한식 메뉴 탐색 노드
│   ├── search_general.py    # 일반 메뉴 탐색 노드
│   └── recommend.py         # 추천 생성 노드
├── edges/
│   ├── __init__.py
│   ├── check_restriction.py # 식이 제한 조건 분기
│   └── check_feedback.py    # 피드백 조건 분기
└── prompts/
    ├── analyze_prompt.txt   # 선호도 분석용 프롬프트
    └── recommend_prompt.txt # 추천 생성용 프롬프트
```

## 핵심 구현

### 1. 상태 정의 (state.py)

LangGraph에서 모든 노드가 공유하는 상태 객체를 정의합니다.

```python
from typing import TypedDict, Literal

class MenuState(TypedDict):
    user_input: str                          # 사용자 원본 입력
    mood: str                                # 기분 (피곤함, 기쁨, 스트레스 등)
    preferred_taste: list[str]               # 선호 맛 (매운맛, 단맛 등)
    cooking_difficulty: str                  # 조리 난이도 (쉬움, 보통, 어려움)
    dietary_restrictions: list[str]          # 식이 제한 목록
    has_restrictions: bool                   # 식이 제한 존재 여부
    menu_candidates: list[dict]              # 메뉴 후보 목록
    recommendation: str                      # 최종 추천 결과
    feedback: Literal["satisfied", "unsatisfied", ""]  # 피드백
    iteration_count: int                     # 재추천 횟수
```

### 2. 그래프 구성 (graph.py)

LangGraph의 StateGraph를 사용하여 워크플로우를 구성합니다.

```python
from langgraph.graph import StateGraph, START, END
from state import MenuState
from nodes.collect_input import collect_input
from nodes.analyze import analyze_preferences
from nodes.search_restricted import search_restricted
from nodes.search_general import search_general
from nodes.recommend import generate_recommendation
from edges.check_restriction import check_restriction
from edges.check_feedback import check_feedback

# 그래프 생성
graph = StateGraph(MenuState)

# 노드 등록
graph.add_node("collect_input", collect_input)
graph.add_node("analyze_preferences", analyze_preferences)
graph.add_node("search_restricted", search_restricted)
graph.add_node("search_general", search_general)
graph.add_node("generate_recommendation", generate_recommendation)

# 엣지 연결
graph.add_edge(START, "collect_input")
graph.add_edge("collect_input", "analyze_preferences")

# 조건부 엣지: 식이 제한 확인
graph.add_conditional_edges(
    "analyze_preferences",
    check_restriction,
    {
        "restricted": "search_restricted",
        "general": "search_general",
    }
)

# 검색 결과 → 추천 생성
graph.add_edge("search_restricted", "generate_recommendation")
graph.add_edge("search_general", "generate_recommendation")

# 조건부 엣지: 피드백 확인
graph.add_conditional_edges(
    "generate_recommendation",
    check_feedback,
    {
        "satisfied": END,
        "unsatisfied": "analyze_preferences",
    }
)

# 컴파일
app = graph.compile()
```

### 3. 노드 구현 예시

**선호도 분석 노드 (nodes/analyze.py)**

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import MenuState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", """사용자의 입력을 분석하여 다음 정보를 추출하세요:
    - mood: 현재 기분
    - preferred_taste: 선호하는 맛 (리스트)
    - cooking_difficulty: 원하는 조리 난이도
    - dietary_restrictions: 식이 제한 사항 (리스트)
    JSON 형식으로 응답하세요."""),
    ("human", "{user_input}")
])

def analyze_preferences(state: MenuState) -> MenuState:
    chain = prompt | llm
    result = chain.invoke({"user_input": state["user_input"]})
    parsed = parse_llm_response(result.content)

    return {
        **state,
        "mood": parsed["mood"],
        "preferred_taste": parsed["preferred_taste"],
        "cooking_difficulty": parsed["cooking_difficulty"],
        "dietary_restrictions": parsed["dietary_restrictions"],
        "has_restrictions": len(parsed["dietary_restrictions"]) > 0,
    }
```

### 4. 조건부 엣지 구현 예시

**식이 제한 확인 (edges/check_restriction.py)**

```python
from state import MenuState

def check_restriction(state: MenuState) -> str:
    if state["has_restrictions"]:
        return "restricted"
    return "general"
```

**피드백 확인 (edges/check_feedback.py)**

```python
from state import MenuState

MAX_ITERATIONS = 3

def check_feedback(state: MenuState) -> str:
    if state["feedback"] == "satisfied":
        return "satisfied"
    if state["iteration_count"] >= MAX_ITERATIONS:
        return "satisfied"  # 최대 재시도 초과 시 종료
    return "unsatisfied"
```

## 실행

```bash
python main.py
```

```
🍽️ 저녁 메뉴 추천 시스템
오늘 저녁 뭐 먹고 싶으세요? 기분, 원하는 맛, 제한사항 등을 자유롭게 말씀해주세요.

> 오늘 좀 피곤한데 매콤하고 따뜻한 거 먹고 싶어. 유제품은 빼줘.

🔍 선호도를 분석하고 있습니다...
🍲 메뉴를 탐색하고 있습니다...

📋 추천 메뉴:
1. 순두부찌개 - 매콤하고 속이 따뜻해지는 한 그릇
2. 김치찌개 - 잘 익은 김치로 깊은 맛
3. 육개장 - 얼큰한 국물로 피로 회복

이 추천이 마음에 드시나요? (만족/불만족)
> 불만족

🔄 다시 분석 중입니다...
```

## 확장 아이디어

- **외부 API 연동**: 레시피 API, 배달 앱 API와 연결하여 실제 주문까지 연동
- **날씨 반영**: 날씨 API를 활용하여 날씨에 맞는 메뉴 추천
- **이전 기록 활용**: 최근 먹은 메뉴를 기억하여 중복 추천 방지
- **영양 정보 제공**: 추천 메뉴의 칼로리, 영양소 정보 함께 제공
- **다중 사용자 지원**: 여러 명의 선호도를 종합하여 그룹 메뉴 추천

## 라이선스

MIT License
