# 랭그래프를 이용한 저녁 메뉴 추천

주소: https://dinnerrecommend-6zpfjo3fxvzjuvkv8pfmg5.streamlit.app/

# 저녁 메뉴 추천 시스템

LangGraph + Streamlit 기반의 저녁 메뉴 추천 웹 애플리케이션.
사용자의 기분, 선호 맛, 식이 제한을 분석하여 최적의 메뉴를 추천합니다.

## 프로젝트 구조

```
langgraph-pjt2/
├── app.py                      # Streamlit 웹 UI 진입점
├── main.py                     # 터미널 실행용 (보관)
├── graph.py                    # LangGraph 워크플로우 정의
├── state.py                    # MenuState 타입 스키마
├── requirements.txt
├── .env                        # OPENAI_API_KEY 설정
├── data/
│   └── menu_data.json          # 85개 메뉴 데이터 (7개 카테고리)
├── nodes/
│   ├── collect_input.py        # 사용자 입력 수집 (state 전달 방식)
│   ├── analyze.py              # GPT-4o-mini로 선호도 분석
│   ├── search_restricted.py    # 식이 제한 메뉴 필터링 (JSON 기반)
│   ├── search_general.py       # 일반 메뉴 필터링 (JSON 기반)
│   └── recommend.py            # LLM 추천 생성 (전체 메뉴 폴백 + 중복 제거)
├── edges/
│   ├── check_restriction.py    # 식이 제한 유무 분기
│   └── check_feedback.py       # 만족/불만족 분기 (최대 3회)
└── prompts/
    ├── analyze_prompt.txt       # 선호도 분석 프롬프트 (상황별 mood 매핑)
    └── recommend_prompt.txt     # 메뉴 추천 프롬프트 (원본 요청 기반 보정)
```

## 그래프 흐름

```
[START]
  → collect_input
  → analyze_preferences (GPT-4o-mini)
  → check_restriction (조건부 분기)
      ├─ restricted → search_restricted (JSON 필터링)
      └─ general   → search_general (JSON 필터링)
  → generate_recommendation (GPT-4o-mini)
  → [interrupt] 사용자 피드백 대기
      ├─ satisfied   → [END]
      └─ unsatisfied → analyze_preferences (재추천, 최대 3회)
```

## 핵심 기술

| 구성 요소 | 기술 |
|-----------|------|
| 워크플로우 | LangGraph (StateGraph + MemorySaver + interrupt_after) |
| LLM | OpenAI GPT-4o-mini (분석 + 추천) |
| 메뉴 탐색 | JSON 파일 기반 필터링 (dietary_tags, allergens, taste, mood 점수) |
| 웹 UI | Streamlit (session_state로 화면 전환 관리) |
| 상태 관리 | LangGraph checkpointer로 대화 상태 유지 |

## 주요 기능

### 상황 인식 추천
- 사용자의 자연어 입력을 분석하여 기분/상황을 파악
- "술안주", "해장", "데이트", "비오는 날" 등 상황별 키워드를 mood로 매핑
- 분석 결과가 부정확할 경우, LLM이 사용자 원본 요청을 직접 참고하여 보정

### 전체 메뉴 폴백
- 점수 기반 필터링 후보가 사용자 요청과 맞지 않을 경우, 전체 메뉴 리스트에서 LLM이 직접 선택
- 필터링 노드의 한계를 LLM 판단으로 보완하는 구조

### 중복 추천 방지
- history에 이전 추천 메뉴명을 누적 기록
- 후보 리스트와 전체 메뉴 리스트 모두에서 이미 추천한 메뉴를 제외
- LLM 응답에서 실제 추천된 메뉴명을 추출하여 정확한 히스토리 관리
- 최대 3회 재추천 시 총 9개의 서로 다른 메뉴 추천 보장

## 메뉴 데이터

`data/menu_data.json`에 85개 메뉴가 7개 카테고리로 구성되어 있습니다.

- **카테고리**: 찌개, 밥류, 면류, 국물, 고기, 반찬/간식, 건강식
- **필드**: name, category, description, taste, mood_tags, dietary_tags, allergens, cooking_difficulty
- **식이 태그**: 유제품없음, 글루텐프리, 채식가능, 저칼로리

## 설치 및 실행

```bash
# 1. 가상환경 생성 및 활성화
python3.11 -m venv .venv
source .venv/bin/activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
# .env 파일에 OPENAI_API_KEY=sk-... 작성

# 4. 웹 UI 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속.

## 화면 구성

1. **입력 화면**: 텍스트로 원하는 메뉴 조건 입력 → "추천받기" 버튼
2. **추천 화면**: 3개 메뉴 추천 결과 → "만족해요!" / "다시 추천해줘" 버튼
3. **종료 화면**: 최종 추천 결과 표시 → "처음부터 다시" 버튼

재추천은 최대 3회까지 가능하며, 매회 이전에 추천한 메뉴를 제외하고 새로운 조합을 제안합니다.
