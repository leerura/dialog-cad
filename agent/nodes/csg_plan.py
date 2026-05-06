from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI

from agent.prompts.csg_plan import build_csg_plan_modify_prompt, build_csg_plan_prompt
from agent.state import DialogCADState
from agent.utils.json_utils import extract_text_content, parse_json_response
from agent.utils.rag import retrieve_examples
from agent.utils.token_tracker import track_tokens


@track_tokens("csg_plan")
def csg_plan_node(state: DialogCADState, model: ChatVertexAI) -> dict:
    named_params = state.get("named_params") or {}
    shape_tags = state.get("shape_tags") or []
    user_feedback = state.get("user_feedback")

    retrieved = retrieve_examples(shape_tags, top_k=3)
    current_plan = state.get("csg_plan")

    if user_feedback and current_plan:
        prompt_text = build_csg_plan_modify_prompt(current_plan, user_feedback)
    else:
        prompt_text = build_csg_plan_prompt(named_params, retrieved)

    response = model.invoke([HumanMessage(content=prompt_text)])
    raw_text = extract_text_content(response.content)

    meta = getattr(response, "usage_metadata", None)
    usage = {}
    if meta:
        usage = {
            "input_tokens": meta.get("input_tokens", 0) if isinstance(meta, dict) else getattr(meta, "input_tokens", 0),
            "output_tokens": meta.get("output_tokens", 0) if isinstance(meta, dict) else getattr(meta, "output_tokens", 0),
        }

    try:
        csg_plan = parse_json_response(raw_text)
    except Exception:
        return {
            "messages": [AIMessage(content=f"❌ CSG 플랜 파싱 실패:\n{raw_text}")],
            "last_token_usage": usage,
        }

    plan_summary = _format_plan(csg_plan)
    confirm_msg = AIMessage(content=(
        f"## 🔧 CSG 모델링 플랜\n\n{plan_summary}\n\n"
        "이 플랜대로 진행할까요? 맞으면 **'확인'**, 수정이 필요하면 알려주세요."
    ))

    return {
        "csg_plan": csg_plan,
        "retrieved_examples": retrieved,
        "hitl_stage": "plan_confirm",
        "plan_confirmed": False,
        "user_feedback": None,
        "messages": [confirm_msg],
        "last_token_usage": usage,
    }


def _format_plan(plan: dict) -> str:
    steps = plan.get("steps", [])
    lines = []
    for step in steps:
        sid = step.get("id", "?")
        desc = step.get("desc", "")
        op = step.get("op", "")
        stype = step.get("type", "")
        lines.append(f"{sid}. [{op}/{stype}] {desc}")
    if plan.get("notes"):
        lines.append(f"\n> {plan['notes']}")
    return "\n".join(lines)
