from state import MenuState

MAX_ITERATIONS = 3


def check_feedback(state: MenuState) -> str:
    if state["feedback"] == "satisfied":
        return "satisfied"
    if state["iteration_count"] >= MAX_ITERATIONS:
        return "satisfied"
    return "unsatisfied"
