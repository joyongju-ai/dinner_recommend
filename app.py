# import streamlit as st
# from dotenv import load_dotenv
# load_dotenv()

# from graph import app as langgraph_app

# # --- 세션 상태 초기화 (앱 최초 실행 시 1번만) ---
# if "stage" not in st.session_state:
#     st.session_state.stage = "input"        # 현재 화면 단계
#     st.session_state.result = None          # 그래프 실행 결과
#     st.session_state.history = []           # 추천 히스토리
#     st.session_state.iteration = 0          # 재추천 횟수

# # --- 1. 입력 화면 ---
# if st.session_state.stage == "input":
#     st.title(" 저녁 메뉴 추천")
#     user_input = st.text_input(
#         "오늘 저녁 뭐 먹고 싶으세요?",
#         placeholder="예: 오늘 피곤한데 매콤한 거 먹고 싶어. 유제품은 빼줘"
#     )

#     if st.button("추천받기") and user_input:
#         initial_state = {
#             "user_input": user_input,
#             "mood": "",
#             "preferred_taste": [],
#             "cooking_difficulty": "",
#             "dietary_restrictions": [],
#             "has_restrictions": False,
#             "menu_candidates": [],
#             "recommendation": "",
#             "feedback": "",
#             "iteration_count": 0,
#         }

#         with st.spinner("메뉴를 분석하고 있어요..."):
#             result = langgraph_app.invoke(initial_state)

#         st.session_state.result = result
#         st.session_state.stage = "recommend"
#         st.rerun()

# # --- 2. 추천 화면 ---
# elif st.session_state.stage == "recommend":
#     st.title(" 추천 결과")
#     st.markdown(st.session_state.result["recommendation"])

#     col1, col2 = st.columns(2)

#     with col1:
#         if st.button(" 만족해요!"):
#             st.session_state.stage = "done"
#             st.rerun()

#     with col2:
#         if st.button(" 다시 추천해줘"):
#             if st.session_state.result["iteration_count"] >= 3:
#                 st.warning("최대 재추천 횟수(3회)를 초과했어요.")
#                 st.session_state.stage = "done"
#                 st.rerun()
#             else:
#                 # 기존 state를 이어받아 재실행
#                 prev = st.session_state.result
#                 prev["feedback"] = "unsatisfied"

#                 with st.spinner("다른 메뉴를 찾고 있어요..."):
#                     result = langgraph_app.invoke(prev)

#                 st.session_state.result = result
#                 st.rerun()

# # --- 3. 종료 화면 ---
# elif st.session_state.stage == "done":
#     st.title(" 추천 완료")
#     st.markdown(st.session_state.result["recommendation"])
#     st.success("맛있는 저녁 되세요! ")

#     if st.button("처음부터 다시"):
#         for key in list(st.session_state.keys()):
#             del st.session_state[key]
#         st.rerun()


import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from graph import app as langgraph_app

# 💡 [수정 포인트 1] LangGraph가 대화를 기억하도록 고유 ID(config) 설정
config = {"configurable": {"thread_id": "user_session_1"}}

# --- 세션 상태 초기화 (앱 최초 실행 시 1번만) ---
if "stage" not in st.session_state:
    st.session_state.stage = "input"        # 현재 화면 단계
    st.session_state.result = None          # 그래프 실행 결과
    st.session_state.history = []           # 추천 히스토리
    st.session_state.iteration = 0          # 재추천 횟수

# --- 1. 입력 화면 ---
if st.session_state.stage == "input":
    st.title(" 저녁 메뉴 추천")
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
            # 💡 [수정 포인트 2] config를 넣어서 실행하고, '멈춘 시점'의 상태를 가져옵니다.
            langgraph_app.invoke(initial_state, config)
            result = langgraph_app.get_state(config).values

        st.session_state.result = result
        st.session_state.stage = "recommend"
        st.rerun()

# --- 2. 추천 화면 ---
elif st.session_state.stage == "recommend":
    st.title(" 추천 결과")
    st.markdown(st.session_state.result["recommendation"])

    col1, col2 = st.columns(2)

    with col1:
        if st.button(" 만족해요!"):
            # 💡 여기를 수정합니다!
            langgraph_app.update_state(
                config, 
                {"feedback": "satisfied"}, 
                as_node="generate_recommendation" # 👈 여기!
            )
            langgraph_app.invoke(None, config)
            
            st.session_state.stage = "done"
            st.rerun()

    with col2:
        if st.button(" 다시 추천해줘"):
            if st.session_state.result["iteration_count"] >= 3:
                st.warning("최대 재추천 횟수(3회)를 초과했어요.")
                st.session_state.stage = "done"
                st.rerun()
            else:
                # 💡 여기도 수정합니다!
                langgraph_app.update_state(
                    config, 
                    {"feedback": "unsatisfied"}, 
                    as_node="generate_recommendation" # 👈 여기!
                )
                
                with st.spinner("다른 메뉴를 찾고 있어요..."):
                    langgraph_app.invoke(None, config)
                
                st.session_state.result = langgraph_app.get_state(config).values
                st.rerun()

# --- 3. 종료 화면 ---
elif st.session_state.stage == "done":
    st.title(" 추천 완료")
    st.markdown(st.session_state.result["recommendation"])
    
    # 💡 [핵심 수정 부분] 재추천 횟수를 확인하여 메시지를 분기합니다.
    if st.session_state.result.get("iteration_count", 0) >= 3:
        st.warning(" 최대 재추천 횟수(3회)에 도달하여 추천을 종료합니다. 위 메뉴 중에서 골라보시는 건 어떨까요?")
    else:
        st.success("맛있는 저녁 되세요!")

    if st.button("처음부터 다시"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()