# 웹 UI 전환 가이드 (Streamlit)

> 기존 터미널 기반 구조에서 Streamlit 웹 UI로 전환하기 위해 변경해야 할 부분만 다룹니다.
> graph.py, state.py, edges/, prompts/는 그대로 유지합니다.

---

## 변경 요약

| 파일 | 변경 내용 |
|------|----------|
| requirements.txt | `streamlit` 추가 |
| nodes/collect_input.py | `input()` 제거 → state에서 값만 읽도록 수정 |
| nodes/recommend.py | `input()`, `print()` 제거 → 결과만 반환하도록 수정 |
| main.py | 더 이상 사용하지 않음 (터미널 실행용으로 보관 가능) |
| app.py | **신규 생성** — Streamlit 웹 UI 진입점 |

> graph.py, state.py, edges/, prompts/, search 노드들은 수정 불필요

---

## 1. requirements.txt에 추가

```
streamlit
```

설치:
```bash
pip install streamlit
```

---

## 2. nodes/collect_input.py 수정

**변경 전 (터미널)**:
```python
def collect_input(state):
    user_input = input("오늘 저녁 뭐 먹고 싶으세요?\n> ")
    return {"user_input": user_input}
```

**변경 후 (웹 UI)**:
```python
def collect_input(state):
    # input()을 쓰지 않음 — app.py에서 이미 user_input을 state에 넣어줌
    return {"user_input": state["user_input"]}
```

> Streamlit에서는 `input()`을 쓸 수 없습니다. 사용자 입력은 app.py의 텍스트 필드에서 받아 초기 state에 넣어주는 방식으로 바뀝니다.

---

## 3. nodes/recommend.py 수정

**변경 전 (터미널)**:
```python
def generate_recommendation(state):
    # ... LLM 호출 ...
    print(llm_result)
    user_answer = input("만족하시나요? (만족/불만족)\n> ")
    feedback = "satisfied" if any(p in user_answer for p in positive) else "unsatisfied"
    return {
        "recommendation": llm_result,
        "feedback": feedback,
        "iteration_count": state["iteration_count"] + 1,
    }
```

**변경 후 (웹 UI)**:
```python
def generate_recommendation(state):
    # ... LLM 호출 ...
    # print()와 input()을 쓰지 않음 — 결과만 반환
    return {
        "recommendation": llm_result,
        "feedback": "",  # 피드백은 app.py에서 버튼으로 처리
        "iteration_count": state["iteration_count"] + 1,
    }
```

> `print()`와 `input()`을 모두 제거합니다. 추천 결과 표시와 피드백 수집은 app.py가 담당합니다.

---

## 4. app.py 신규 생성

프로젝트 루트에 `app.py`를 생성합니다.

```
langgraph-pjt2/
  ├── app.py          ← 신규
  ├── main.py         ← 터미널용 (보관)
  ├── graph.py
  └── ...
```

### app.py의 핵심 구조

```python
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from graph import app as langgraph_app
```

### 페이지 구성

app.py는 3가지 화면 상태를 관리합니다:

```
1. 입력 화면: 텍스트 입력 + 제출 버튼
2. 추천 화면: 추천 결과 + 만족/불만족 버튼
3. 종료 화면: 최종 결과 표시
```

### session_state 활용

Streamlit은 버튼을 누를 때마다 스크립트가 처음부터 다시 실행되므로,
`st.session_state`에 상태를 저장해야 합니다.

```python
# 초기화 (앱 최초 실행 시 1번만)
if "stage" not in st.session_state:
    st.session_state.stage = "input"        # 현재 화면 단계
    st.session_state.result = None          # 그래프 실행 결과
    st.session_state.history = []           # 추천 히스토리
    st.session_state.iteration = 0          # 재추천 횟수
```

### 입력 화면

```python
if st.session_state.stage == "input":
    st.title("🍽️ 저녁 메뉴 추천")
    user_input = st.text_input(
        "오늘 저녁 뭐 먹고 싶으세요?",
        placeholder="예: 오늘 피곤한데 매콤한 거 먹고 싶어. 유제품은 빼줘"
    )

    if st.button("추천받기") and user_input:
        initial_state = {
            "user_input": user_input,
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

        with st.spinner("메뉴를 분석하고 있어요..."):
            result = langgraph_app.invoke(initial_state)

        st.session_state.result = result
        st.session_state.stage = "recommend"
        st.rerun()
```

### 추천 화면

```python
elif st.session_state.stage == "recommend":
    st.title("📋 추천 결과")
    st.markdown(st.session_state.result["recommendation"])

    col1, col2 = st.columns(2)

    with col1:
        if st.button("😊 만족해요!"):
            st.session_state.stage = "done"
            st.rerun()

    with col2:
        if st.button("🔄 다시 추천해줘"):
            if st.session_state.result["iteration_count"] >= 3:
                st.warning("최대 재추천 횟수(3회)를 초과했어요.")
                st.session_state.stage = "done"
                st.rerun()
            else:
                # 기존 state를 이어받아 재실행
                prev = st.session_state.result
                prev["feedback"] = "unsatisfied"

                with st.spinner("다른 메뉴를 찾고 있어요..."):
                    result = langgraph_app.invoke(prev)

                st.session_state.result = result
                st.rerun()
```

### 종료 화면

```python
elif st.session_state.stage == "done":
    st.title("✅ 추천 완료")
    st.markdown(st.session_state.result["recommendation"])
    st.success("맛있는 저녁 되세요! 🍽️")

    if st.button("처음부터 다시"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
```

---

## 5. 실행 방법

```bash
cd /home/ssafy/work/langgraph-pjt2
streamlit run app.py
```

실행하면 터미널에 아래처럼 뜹니다:
```
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

브라우저에서 `http://localhost:8501`을 열면 웹 UI가 나타납니다.

---

## 주의사항

| 항목 | 설명 |
|------|------|
| `input()` 사용 금지 | Streamlit에서 `input()`을 쓰면 앱이 멈춤. 반드시 `st.text_input()` 사용 |
| `print()` 대신 `st.write()` | 터미널 출력은 웹에 안 보임. `st.markdown()` 또는 `st.write()` 사용 |
| `st.rerun()` | 화면 전환 시 반드시 호출해야 새 상태가 반영됨 |
| 이전 버전 Streamlit | `st.rerun()`이 없으면 `st.experimental_rerun()` 사용 |
