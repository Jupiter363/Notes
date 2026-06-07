from typing import Literal
from app.graph.state import TravelState


def route_after_check(state: TravelState) -> Literal["ask_clarification", "decide_tools"]:
    if state.get("is_info_complete"):
        return "decide_tools"
    return "ask_clarification"


def route_after_reflection(state: TravelState) -> Literal["revise_plan", "final_output"]:
    reflection = state.get("reflection", {})
    need_revision = reflection.get("need_revision", False)
    accepted_as_final = reflection.get("accepted_as_final", False)

    revision_count = state.get("revision_count", 0)
    max_revision_count = state.get("max_revision_count", 2)

    if accepted_as_final:
        return "final_output"

    if need_revision and revision_count < max_revision_count:
        return "revise_plan"

    return "final_output"
