from state import MenuState


def check_restriction(state: MenuState) -> str:
    if state["has_restrictions"]:
        return "restricted"
    return "general"
