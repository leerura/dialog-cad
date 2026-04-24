from langchain_core.messages import AIMessage

from agent.state import DialogCADState


def confirm_result_node(state: DialogCADState) -> dict:
    """interrupt_before로 일시정지 후, user_approved/user_feedback으로 분기."""
    approved = state.get("user_approved")
    feedback = state.get("user_feedback")

    if approved:
        return {
            "result_confirmed": True,   # 라우터가 이 플래그를 읽음
            "user_approved": None,
            "user_feedback": None,
            "hitl_stage": None,
            "messages": [AIMessage(content="🎉 모델링이 완료됐습니다! 다른 도면을 업로드하거나 수정 사항을 알려주세요.")],
        }
    else:
        return {
            "result_confirmed": False,
            "user_approved": None,
            "user_feedback": feedback,
            "hitl_stage": "result_confirm",
            "verified": False,
            "messages": [AIMessage(content="피드백을 반영하여 다시 실행할게요.")],
        }
