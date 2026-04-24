from langchain_core.messages import AIMessage

from agent.state import DialogCADState


def confirm_plan_node(state: DialogCADState) -> dict:
    """interrupt_before로 일시정지 후, user_approved/user_feedback으로 분기."""
    approved = state.get("user_approved")
    feedback = state.get("user_feedback")

    if approved:
        return {
            "plan_confirmed": True,
            "user_approved": None,
            "user_feedback": None,
            "hitl_stage": None,
            "messages": [AIMessage(content="✅ 플랜 확인 완료. Fusion 360에서 모델링을 시작할게요.")],
        }
    else:
        return {
            "plan_confirmed": False,
            "user_approved": None,
            "user_feedback": feedback,
            "hitl_stage": "plan_confirm",
            "messages": [AIMessage(content="피드백을 반영하여 플랜을 다시 작성할게요.")],
        }
