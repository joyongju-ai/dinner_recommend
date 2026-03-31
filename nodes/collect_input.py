from state import MenuState


# def collect_input(state: MenuState) -> dict:
#     user_input = input(
#         "\n오늘 저녁 뭐 먹고 싶으세요? "
#         "기분, 원하는 맛, 제한사항 등을 자유롭게 말씀해주세요.\n\n> "
#     )
#     return {"user_input": user_input, "iteration_count": 0, "feedback": ""}

def collect_input(state):
    # input()을 쓰지 않음 — app.py에서 이미 user_input을 state에 넣어줌
    return {"user_input": state["user_input"]}