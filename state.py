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
    history: list[str]
