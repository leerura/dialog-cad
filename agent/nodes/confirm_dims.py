from langchain_core.messages import AIMessage

from agent.state import DialogCADState


def confirm_dims_node(state: DialogCADState) -> dict:
    """interrupt_before로 일시정지 후, user_approved/user_feedback으로 분기."""
    approved = state.get("user_approved")
    feedback = state.get("user_feedback")

    if approved:
        return {
            "dims_confirmed": True,
            "user_approved": None,
            "user_feedback": None,
            "dims_feedback_history": [],   # 확인 완료 → 히스토리 초기화
            "hitl_stage": None,
            "messages": [AIMessage(content="✅ 치수 확인 완료. CSG 플랜을 작성할게요.")],
        }
    else:
        # 피드백 누적
        history = list(state.get("dims_feedback_history") or [])
        if feedback:
            history.append(feedback)
        return {
            "dims_confirmed": False,
            "user_approved": None,
            "user_feedback": feedback,
            "dims_feedback_history": history,
            "hitl_stage": "dims_confirm",
            "messages": [AIMessage(content="수정 사항을 반영하여 치수를 다시 추출할게요.")],
        }
