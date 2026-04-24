from langgraph.graph import END

from agent.state import DialogCADState


def route_after_confirm_dims(state: DialogCADState) -> str:
    confirmed = state.get("dims_confirmed")
    approved = state.get("user_approved")
    print(f"[ROUTE_DIMS] confirmed={confirmed}, approved={approved}")

    if confirmed:
        return "csg_plan"
    return "parse_drawing"


def route_after_confirm_plan(state: DialogCADState) -> str:
    confirmed = state.get("plan_confirmed")
    print(f"[ROUTE_PLAN] confirmed={confirmed}")

    if confirmed:
        return "execute"
    return "csg_plan"


def route_after_execute(state: DialogCADState) -> str:
    if state.get("tool_called"):
        return "verify"
    return END


def route_after_verify(state: DialogCADState) -> str:
    verified = state.get("verified")
    retry_count = state.get("retry_count", 0)
    print(f"[ROUTE_VERIFY] verified={verified}, retry={retry_count}")

    if verified:
        return "confirm_result"

    if retry_count >= 3:
        return "confirm_result"

    return "execute"


def route_after_confirm_result(state: DialogCADState) -> str:
    confirmed = state.get("result_confirmed")
    print(f"[ROUTE_RESULT] result_confirmed={confirmed}")

    if confirmed:
        return END
    return "parse_drawing"
