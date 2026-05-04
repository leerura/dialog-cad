import base64

from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI

from agent.prompts.parse import PARSE_PROMPT
from agent.state import DialogCADState
from agent.utils.json_utils import extract_text_content, parse_json_response
from agent.utils.token_tracker import track_tokens


# TODO: GEMINI 예외 처리
@track_tokens("parse_drawing")
def parse_drawing_node(state: DialogCADState, model: ChatVertexAI) -> dict:
    image_path = state.get("image_path")
    if not image_path:
        return {"messages": [AIMessage(content="❌ 도면 이미지가 없어요. 이미지를 업로드해주세요.")]}

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = image_path.split(".")[-1].lower()
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    mime_type = mime_map.get(ext, "image/png")

    # 피드백 히스토리 전체를 프롬프트에 추가
    feedback_history = state.get("dims_feedback_history") or []
    user_feedback = state.get("user_feedback")
    # 최신 피드백이 히스토리에 없으면 포함
    if user_feedback and (not feedback_history or feedback_history[-1] != user_feedback):
        feedback_history = feedback_history + [user_feedback]

    prompt_text = PARSE_PROMPT
    if feedback_history:
        items = "\n".join(f"  {i+1}. {fb}" for i, fb in enumerate(feedback_history))
        prompt_text += (
            f"\n\n## ⚠️ 이전 추출의 누적 오류 — 반드시 모두 반영하세요\n"
            f"{items}\n\n"
            "위 항목들을 도면에서 다시 확인하여 JSON에 정확히 반영하세요. "
            "특히 회전 각도, 관통 여부, 지름/반지름 구분에 주의하세요."
        )
        print(f"[PARSE] 피드백 히스토리 반영 ({len(feedback_history)}개): {feedback_history}")

    message = HumanMessage(content=[
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
        {"type": "text", "text": prompt_text},
    ])

    response = model.invoke([message])
    raw_text = extract_text_content(response.content)

    meta = getattr(response, "usage_metadata", None)
    usage = {}
    if meta:
        usage = {
            "input_tokens": meta.get("input_tokens", 0) if isinstance(meta, dict) else getattr(meta, "input_tokens", 0),
            "output_tokens": meta.get("output_tokens", 0) if isinstance(meta, dict) else getattr(meta, "output_tokens", 0),
        }

    try:
        data = parse_json_response(raw_text)
    except Exception:
        return {
            "messages": [AIMessage(content=f"❌ 치수 추출 실패. Gemini 응답:\n{raw_text}\n\n도면을 다시 업로드해주세요.")],
            "last_token_usage": usage,
        }

    extracted_dims = data.get("views", data)
    named_params = data.get("named_params", {})
    shape_tags = data.get("shape_tags", [])

    confirm_msg = AIMessage(content=(
        f"## 📐 추출된 치수\n\n"
        f"{_format_dims(extracted_dims)}\n\n"
        f"**파라미터**: {named_params}\n\n"
        f"**형상 태그**: {', '.join(shape_tags)}\n\n"
        "치수가 맞나요? 맞으면 **'확인'**, 틀리면 수정 내용을 알려주세요."
    ))

    return {
        "extracted_dims": extracted_dims,
        "named_params": named_params,
        "shape_tags": shape_tags,
        "hitl_stage": "dims_confirm",
        "dims_confirmed": False,
        "messages": [confirm_msg],
        "last_token_usage": usage,
    }


def _format_dims(dims: dict) -> str:
    lines = []
    for view_name, view_data in dims.items():
        lines.append(f"**{view_name}**")
        if isinstance(view_data, dict):
            for k, v in view_data.items():
                lines.append(f"  - {k}: {v}")
        else:
            lines.append(f"  {view_data}")
    return "\n".join(lines)
