# 구현 가이드: LangGraph 저녁 메뉴 추천 시스템

## 현재 진행 상황

| 항목 | 상태 | 비고 |
|------|------|------|
| 시스템 플로우차트 설계 | ✅ 완료 | 7개 노드, 2개 조건 분기, 피드백 루프 |
| README.md | ✅ 완료 | 프로젝트 개요, 아키텍처, 코드 예시 포함 |
| menu_data.json | ✅ 완료 | 45개 메뉴, 7개 카테고리, data/ 폴더에 배치 |
| 프로젝트 폴더 구조 | ✅ 완료 | nodes/, edges/, prompts/, data/ 생성 완료 |
| 코드 파일 | 🔧 일부 완료 | 아래 체크리스트로 확인 |

---

## 코드 파일 체크리스트

아래 항목을 하나씩 확인하고, 미완성인 파일만 작업하세요.

### 환경 설정

- [ ] **requirements.txt**에 `langgraph`, `langchain`, `langchain-openai`, `python-dotenv` 포함 여부
- [ ] `pip install -r requirements.txt` 실행 여부
- [ ] **.env** 파일에 `OPENAI_API_KEY` 설정 여부

### state.py

아래 10개 필드가 모두 정의되어 있는지 확인하세요.

```python
from typing import TypedDict, Literal

class MenuState(TypedDict):
    user_input: str
    mood: str
    preferred_taste: list[str]
    cooking_difficulty: str
    dietary_restrictions: list[str]
    has_restrictions: bool
    menu_candidates: list[dict]
    recommendation: str
    feedback: Literal["satisfied", "unsatisfied", ""]
    iteration_count: int
```

> 필드가 빠져 있으면 이후 노드에서 KeyError가 발생합니다.

---

## 남은 작업 상세

아래 내용은 각 파일에 반드시 들어가야 할 핵심 로직입니다.
이미 작성된 파일은 아래 요구사항과 비교하여 빠진 부분만 보완하세요.

---

### nodes/collect_input.py

```python
def collect_input(state: MenuState) -> dict:
```

**필수 동작**:
- `input()`으로 사용자에게 질문
- 반환: `{"user_input": 입력값}`

간단한 파일이므로 빠르게 확인 후 넘어가세요.

---

### nodes/analyze.py

**필수 동작**:
1. `state["user_input"]`을 `ChatOpenAI`에 전달
2. `prompts/analyze_prompt.txt`를 시스템 프롬프트로 사용
3. LLM 응답을 JSON 파싱

**반환해야 할 필드** (6개):
```python
return {
    "mood": "...",
    "preferred_taste": [...],
    "cooking_difficulty": "...",
    "dietary_restrictions": [...],
    "has_restrictions": True/False,  # dietary_restrictions가 비어있지 않으면 True
}
```

**자주 빠뜨리는 부분**:
- `has_restrictions` 계산을 빼먹으면 조건 분기가 항상 `general`로 빠짐
- LLM 응답에 ```json 마크다운이 섞일 수 있으므로 제거 처리 필요:
```python
text = result.content.replace("```json", "").replace("```", "").strip()
parsed = json.loads(text)
```

---

### nodes/search_restricted.py

**필수 동작**:
1. `data/menu_data.json` 로드 (`encoding="utf-8"` 명시)
2. 3단계 필터링:

```
1차: dietary_tags 매칭
     → 사용자의 dietary_restrictions 항목이 메뉴의 dietary_tags에 모두 포함되어야 통과
     → 예: 사용자 ["유제품없음"] → 순두부찌개(유제품없음 ✓) 통과, 카르보나라(없음 ✗) 제외

2차: allergens 제외
     → 사용자 알레르기 항목이 메뉴의 allergens에 포함되면 제외

3차: taste + mood_tags 매칭으로 관련도 점수 계산
     → 점수 = (taste 매칭 수 × 2) + (mood_tags 매칭 수 × 1)
     → 상위 5~10개 선택
```

**반환**: `{"menu_candidates": [필터링된 메뉴 리스트]}`

**주의**: 필터 결과가 0개일 때 폴백 처리 필요 → taste 조건만으로 재필터링

---

### nodes/search_general.py

**필수 동작**:
1. `data/menu_data.json` 로드
2. 2단계 필터링 (dietary 필터 없음):

```
1차: taste + mood_tags 관련도 점수 계산
     → 점수 = (taste 매칭 수 × 2) + (mood_tags 매칭 수 × 1)

2차: cooking_difficulty 조건이 있으면 추가 필터링
     → 사용자가 "쉬움"을 원하면 "쉬움"인 메뉴 우선
```

**반환**: `{"menu_candidates": [점수순 정렬된 메뉴 리스트]}`

> `search_restricted`와 JSON 로드 로직이 동일하므로, 공통 유틸 함수로 분리해도 좋습니다.

---

### nodes/recommend.py

**필수 동작**:
1. `state["menu_candidates"]`에서 상위 3개 추출
2. 메뉴 정보 + 사용자 mood를 LLM에 전달
3. `prompts/recommend_prompt.txt`를 시스템 프롬프트로 사용
4. 추천 결과 `print()` 출력
5. `input()`으로 만족/불만족 피드백 수집

**반환해야 할 필드** (3개):
```python
return {
    "recommendation": "LLM이 생성한 추천 문구",
    "feedback": "satisfied" 또는 "unsatisfied",
    "iteration_count": state["iteration_count"] + 1,
}
```

**자주 빠뜨리는 부분**:
- `iteration_count + 1`을 안 하면 최대 재시도 제한이 작동하지 않음
- 사용자 입력이 "만족", "네", "좋아" 등 다양할 수 있으므로 유연한 매칭 필요:
```python
positive = ["만족", "네", "좋아", "응", "그래", "yes"]
feedback = "satisfied" if any(p in user_answer for p in positive) else "unsatisfied"
```

---

### edges/check_restriction.py

```python
def check_restriction(state: MenuState) -> str:
    return "restricted" if state["has_restrictions"] else "general"
```

> 그대로 사용하면 됩니다. graph.py의 매핑 딕셔너리 키와 일치하는지만 확인하세요.

---

### edges/check_feedback.py

```python
MAX_ITERATIONS = 3

def check_feedback(state: MenuState) -> str:
    if state["feedback"] == "satisfied":
        return "satisfied"
    if state["iteration_count"] >= MAX_ITERATIONS:
        return "satisfied"
    return "unsatisfied"
```

> `MAX_ITERATIONS`를 반드시 설정하세요. 없으면 불만족 루프가 무한히 돕니다.

---

### prompts/analyze_prompt.txt

아래 내용이 포함되어야 합니다:

```
역할: 사용자의 음식 선호도를 분석하는 전문가

추출할 필드:
- mood: 현재 기분 (피곤함, 기쁨, 스트레스, 편안함 등)
- preferred_taste: 선호하는 맛 리스트
  허용값: 매운맛, 단맛, 짠맛, 신맛, 감칠맛, 고소한맛, 구수한맛
- cooking_difficulty: 원하는 조리 난이도
  허용값: 쉬움, 보통, 어려움
- dietary_restrictions: 식이 제한 사항 리스트
  허용값: 유제품없음, 글루텐프리, 채식가능, 저칼로리

규칙:
- 언급되지 않은 항목은 빈 리스트 [] 또는 빈 문자열 ""로 처리
- JSON만 반환하고, 마크다운이나 설명은 절대 포함하지 마세요
```

---

### prompts/recommend_prompt.txt

아래 내용이 포함되어야 합니다:

```
역할: 친근한 저녁 메뉴 추천 도우미

입력: 사용자 기분, 선호도, 메뉴 후보 리스트

규칙:
- 상위 3개 메뉴를 추천
- 각 메뉴마다 추천 이유를 1줄로 설명
- 따뜻하고 캐주얼한 말투 사용
- 재추천인 경우, 이전과 다른 관점으로 추천
```

---

### graph.py

**필수 구조**:
```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(MenuState)

# 노드 등록 (5개)
graph.add_node("collect_input", collect_input)
graph.add_node("analyze_preferences", analyze_preferences)
graph.add_node("search_restricted", search_restricted)
graph.add_node("search_general", search_general)
graph.add_node("generate_recommendation", generate_recommendation)

# 순차 엣지 (3개)
graph.add_edge(START, "collect_input")
graph.add_edge("collect_input", "analyze_preferences")
graph.add_edge("search_restricted", "generate_recommendation")
graph.add_edge("search_general", "generate_recommendation")

# 조건부 엣지 (2개)
graph.add_conditional_edges("analyze_preferences", check_restriction, {
    "restricted": "search_restricted",
    "general": "search_general",
})
graph.add_conditional_edges("generate_recommendation", check_feedback, {
    "satisfied": END,
    "unsatisfied": "analyze_preferences",
})

app = graph.compile()
```

**확인 포인트**:
- 노드 이름 문자열이 `add_node`와 `add_conditional_edges`에서 정확히 일치하는지
- 엣지 함수의 반환값이 매핑 딕셔너리의 키와 일치하는지
- `END`를 import 했는지

---

### main.py

**필수 구조**:
```python
from dotenv import load_dotenv
load_dotenv()  # 반드시 최상단에서 호출

from graph import app

initial_state = {
    "user_input": "",
    "mood": "",
    "preferred_taste": [],
    "cooking_difficulty": "",
    "dietary_restrictions": [],
    "has_restrictions": False,
    "menu_candidates": [],
    "recommendation": "",
    "feedback": "",
    "iteration_count": 0,
}

result = app.invoke(initial_state)
```

> `load_dotenv()`를 import 아래 첫 줄에 호출해야 이후 LangChain이 API 키를 인식합니다.

---

## 테스트 시나리오

구현이 끝나면 아래 3가지를 순서대로 테스트하세요.

**1. 일반 추천 테스트**
```
입력: "오늘 기분 좋은데 뭐 맛있는 거 먹고 싶어"
확인: search_general 경로로 빠지는지, 추천이 출력되는지
```

**2. 식이 제한 테스트**
```
입력: "유제품 못 먹는데 매콤한 거 추천해줘"
확인: search_restricted 경로로 빠지는지, 유제품 메뉴가 제외되는지
```

**3. 피드백 루프 테스트**
```
입력: 아무 메뉴 요청 → 불만족 3회 입력
확인: 최대 3회 후 자동 종료되는지
```

---

## 자주 발생하는 문제

| 문제 | 원인 | 해결 |
|------|------|------|
| LLM 응답 파싱 실패 | JSON 외 텍스트 포함 | ```json 블록 제거 후 파싱 |
| 메뉴 후보가 0개 | 필터 조건이 너무 엄격 | taste만으로 재필터링하는 폴백 추가 |
| 무한 루프 | iteration_count 미증가 | recommend.py에서 +1 반환 확인 |
| API 키 에러 | .env 미로드 | main.py 첫 줄에 load_dotenv() 확인 |
| 한글 깨짐 | 파일 인코딩 | json.load 시 encoding="utf-8" 명시 |
| 노드 연결 에러 | 이름 불일치 | add_node의 이름과 엣지 매핑 키 대조 |
