import uuid

import gradio as gr
from langchain_core.messages import AIMessage, ToolMessage

from agent.graph import create_agent
from agent.utils.token_tracker import tracker
from fusion_mcp.wrapper import fusion360_run_script

agent = create_agent(tools=[fusion360_run_script])

INITIAL_STATE = {
    "image_path": None,
    "extracted_dims": None,
    "named_params": None,
    "shape_tags": None,
    "retrieved_examples": None,
    "csg_plan": None,
    "execution_plan": None,
    "execution_result": None,
    "tool_called": None,
    "verified": None,
    "retry_count": 0,
    "hitl_stage": None,
    "user_approved": None,
    "user_feedback": None,
    "dims_confirmed": None,
    "plan_confirmed": None,
    "result_confirmed": None,
    "dims_feedback_history": [],
    "messages": [],
}


def get_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


async def run_graph(input_data, config: dict) -> tuple[list[str], bool]:
    collected = []
    tool_logs = []
    interrupted = False

    async for chunk in agent.astream(input_data, config=config, stream_mode="updates"):
        if "__interrupt__" in chunk:
            interrupted = True
            break

        for _, node_output in chunk.items():
            if not isinstance(node_output, dict):
                continue
            for msg in node_output.get("messages", []):
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_logs.append(f"🔧 툴 호출: `{tc['name']}`")
                elif isinstance(msg, ToolMessage):
                    tool_logs.append(f"📦 {str(msg.content)[:300]}")
                elif isinstance(msg, AIMessage) and msg.content:
                    content = msg.content
                    if isinstance(content, list):
                        content = " ".join(
                            item.get("text", "") if isinstance(item, dict) else str(item)
                            for item in content
                        )
                    collected.append(content)

    if tool_logs:
        collected = ["```\n" + "\n".join(tool_logs) + "\n```"] + collected

    return collected, interrupted


def append(history, role, content):
    history.append({"role": role, "content": content})
    return history


# ── 이미지 업로드 ────────────────────────────────────────────────────

async def upload_drawing(image, history, thread_id):
    if image is None:
        yield history, gr.update(visible=False), gr.update(visible=False), thread_id
        return

    history = history or []
    history = append(history, "user", "📎 도면을 업로드했어요.")
    history = append(history, "assistant", "🔄 도면 분석 중...")
    yield history, gr.update(visible=False), gr.update(visible=False), thread_id

    config = get_config(thread_id)
    init_state = {**INITIAL_STATE, "image_path": image}
    messages, interrupted = await run_graph(init_state, config)

    history.pop()
    for msg in messages:
        history = append(history, "assistant", msg)

    yield history, gr.update(visible=interrupted), gr.update(visible=False), thread_id


# ── 확인 버튼 ────────────────────────────────────────────────────────

async def handle_approve(history, thread_id):
    history = append(history, "user", "✅ 확인")
    history = append(history, "assistant", "🔄 처리 중...")
    yield history, gr.update(visible=False), gr.update(visible=False)

    config = get_config(thread_id)
    agent.update_state(config, {"user_approved": True, "user_feedback": None})
    messages, interrupted = await run_graph(None, config)

    history.pop()
    for msg in messages:
        history = append(history, "assistant", msg)

    yield history, gr.update(visible=interrupted), gr.update(visible=False)


# ── 수정 버튼 ────────────────────────────────────────────────────────

async def handle_reject(history):
    return history, gr.update(visible=True)


# ── 피드백 전송 ──────────────────────────────────────────────────────

async def handle_feedback(feedback, history, thread_id):
    if not feedback.strip():
        yield history, gr.update(visible=True), gr.update(visible=False), ""
        return

    history = append(history, "user", feedback)
    history = append(history, "assistant", "🔄 피드백 반영 중...")
    yield history, gr.update(visible=False), gr.update(visible=False), ""

    config = get_config(thread_id)
    agent.update_state(config, {"user_approved": False, "user_feedback": feedback})
    messages, interrupted = await run_graph(None, config)

    history.pop()
    for msg in messages:
        history = append(history, "assistant", msg)

    yield history, gr.update(visible=interrupted), gr.update(visible=False), ""


# ── 토큰 요약 ────────────────────────────────────────────────────────

def get_token_summary():
    if not tracker.records:
        return "아직 요청 없음"
    lines = [
        f"**{r.node_name}**: in={r.input_tokens} out={r.output_tokens} total={r.total_tokens}"
        for r in tracker.records
    ]
    total = sum(r.total_tokens for r in tracker.records)
    lines.append(f"\n**TOTAL: {total}**")
    return "\n".join(lines)


# ── UI ───────────────────────────────────────────────────────────────

with gr.Blocks(title="DialogCAD Agent") as demo:
    gr.Markdown("# ✏️ DialogCAD — 대화형 CAD 에이전트")
    gr.Markdown("도면을 업로드하면 치수 추출 → CSG 플랜 → Fusion 360 실행까지 자동으로 진행됩니다.")

    thread_id = gr.State(str(uuid.uuid4()))

    with gr.Row():
        with gr.Column(scale=3):
            image_input = gr.Image(type="filepath", label="📎 도면 업로드", height=180)

            chatbot = gr.Chatbot(label="대화", height=460, show_label=False)

            with gr.Row(visible=False) as confirm_row:
                approve_btn = gr.Button("✅ 확인", variant="primary", scale=1)
                reject_btn  = gr.Button("❌ 수정", variant="secondary", scale=1)

            with gr.Row(visible=False) as feedback_row:
                feedback_input = gr.Textbox(placeholder="어떤 부분이 틀렸나요?", show_label=False, scale=4)
                feedback_submit = gr.Button("전송", scale=1)

        with gr.Column(scale=1):
            gr.Markdown("### 📊 토큰 사용량")
            token_display = gr.Markdown("아직 요청 없음")
            refresh_btn = gr.Button("새로고침", size="sm")
            refresh_btn.click(fn=get_token_summary, outputs=token_display)

    image_input.change(
        fn=upload_drawing,
        inputs=[image_input, chatbot, thread_id],
        outputs=[chatbot, confirm_row, feedback_row, thread_id],
    )

    approve_btn.click(
        fn=handle_approve,
        inputs=[chatbot, thread_id],
        outputs=[chatbot, confirm_row, feedback_row],
    )

    reject_btn.click(
        fn=handle_reject,
        inputs=[chatbot],
        outputs=[chatbot, feedback_row],
    )

    feedback_submit.click(
        fn=handle_feedback,
        inputs=[feedback_input, chatbot, thread_id],
        outputs=[chatbot, confirm_row, feedback_row, feedback_input],
    )
    feedback_input.submit(
        fn=handle_feedback,
        inputs=[feedback_input, chatbot, thread_id],
        outputs=[chatbot, confirm_row, feedback_row, feedback_input],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
