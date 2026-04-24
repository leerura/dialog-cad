import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent.state import DialogCADState
from agent.utils.token_tracker import track_tokens


@track_tokens("execute")
async def execute_node(state: DialogCADState, agent) -> dict:
    csg_plan = state.get("csg_plan") or {}
    named_params = state.get("named_params") or {}

    plan_text = json.dumps(csg_plan, ensure_ascii=False, indent=2)
    params_text = json.dumps(named_params, ensure_ascii=False, indent=2)

    instruction = (
        f"아래 CSG 플랜과 파라미터를 사용하여 Fusion 360 스크립트를 작성하고 실행하세요.\n\n"
        f"## Named Parameters\n```json\n{params_text}\n```\n\n"
        f"## CSG Plan\n```json\n{plan_text}\n```\n\n"
        "fusion360_run_script 툴을 호출하여 스크립트를 실행하세요."
    )

    plan_message = HumanMessage(content=instruction)
    print(f"[EXECUTE] 지시문 전달 (첫 100자): {instruction[:100]}")

    for attempt in range(3):
        result = await agent.ainvoke({"messages": [plan_message]})
        has_tool_call = any(
            isinstance(m, AIMessage) and getattr(m, "tool_calls", None)
            for m in result.get("messages", [])
        )
        if has_tool_call:
            break
        if attempt < 2:
            print(f"[EXECUTE] ⚠️ 빈 응답, 재시도 {attempt + 1}/2...")

    tool_called = False
    tool_result_content = ""
    for msg in result["messages"]:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            print(f"[EXECUTE] ✅ 툴 호출됨: {[tc['name'] for tc in msg.tool_calls]}")
            for tc in msg.tool_calls:
                script = tc.get("args", {}).get("code", "")
                if script:
                    print(f"[EXECUTE] ── 전달 스크립트 ──────────────────\n{script}\n────────────────────────────────────")
            tool_called = True
        if isinstance(msg, ToolMessage):
            tool_result_content = str(msg.content)
            print(f"[EXECUTE] 툴 결과: {tool_result_content[:400]}")

    if not tool_called:
        print("[EXECUTE] ❌ 툴 호출 없음")

    execution_result = tool_result_content or str(result["messages"][-1].content)

    usage = {}
    for msg in reversed(result["messages"]):
        meta = getattr(msg, "usage_metadata", None)
        if meta:
            usage = {
                "input_tokens": meta.get("input_tokens", 0) if isinstance(meta, dict) else getattr(meta, "input_tokens", 0),
                "output_tokens": meta.get("output_tokens", 0) if isinstance(meta, dict) else getattr(meta, "output_tokens", 0),
            }
            break

    return {
        **result,
        "execution_result": execution_result,
        "tool_called": tool_called,
        "last_token_usage": usage,
    }
