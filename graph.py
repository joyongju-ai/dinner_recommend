from langgraph.graph import StateGraph, START, END
from state import MenuState
from nodes.collect_input import collect_input
from nodes.analyze import analyze_preferences
from nodes.search_restricted import search_restricted
from nodes.search_general import search_general
from nodes.recommend import generate_recommendation
from edges.check_restriction import check_restriction
from edges.check_feedback import check_feedback

from langgraph.checkpoint.memory import MemorySaver

graph = StateGraph(MenuState)

graph.add_node("collect_input", collect_input)
graph.add_node("analyze_preferences", analyze_preferences)
graph.add_node("search_restricted", search_restricted)
graph.add_node("search_general", search_general)
graph.add_node("generate_recommendation", generate_recommendation)

graph.add_edge(START, "collect_input")
graph.add_edge("collect_input", "analyze_preferences")

graph.add_conditional_edges(
    "analyze_preferences",
    check_restriction,
    {
        "restricted": "search_restricted",
        "general": "search_general",
    },
)

graph.add_edge("search_restricted", "generate_recommendation")
graph.add_edge("search_general", "generate_recommendation")

graph.add_conditional_edges(
    "generate_recommendation",
    check_feedback,
    {
        "satisfied": END,
        "unsatisfied": "analyze_preferences",
    },
)

#app = graph.compile()

memory = MemorySaver()

app = graph.compile(
    checkpointer=memory,
    interrupt_after=["generate_recommendation"]  # 👈 등록하신 노드 이름과 정확히 일치해야 합니다!
)