#!/usr/bin/env python3
"""
parse_drawing 단계를 건너뛰고 named_params를 직접 주입하여
CSG 플랜 → Execute 단계부터 테스트하는 스크립트.

사용법:
    python test_inject.py

흐름:
    1. 이미지 없이 그래프 시작 → parse_drawing 에러 → confirm_dims interrupt
    2. named_params 직접 주입 + user_approved=True 설정
    3. confirm_dims 통과 → csg_plan 실행 → confirm_plan interrupt
    4. 플랜 확인/피드백 → execute → verify → 완료
"""

import asyncio
import uuid

from langchain_core.messages import AIMessage, ToolMessage

from agent.graph import create_agent
from fusion_mcp.wrapper import fusion360_run_script


# ══════════════════════════════════════════════════════════════════════
# ✏️  여기를 수정하세요
# ══════════════════════════════════════════════════════════════════════

NAMED_PARAMS = {
    "base_width_mm": 100,
    "base_depth_mm": 60,
    "base_thickness_mm": 13,
    "boss_outer_r_mm": 25,
    "boss_depth_mm": 40,
    "boss_hole_r_mm": 15,
    "mounting_hole_r_mm": 5,
    "mounting_hole_count": 2,
    "center_height_mm": 100,
}

SHAPE_TAGS = ["bracket", "plate", "boss", "through_hole"]

# ══════════════════════════════════════════════════════════════════════

INITIAL_STATE = {
    "image_path": None,          # 일부러 비워서 parse_drawing 스킵
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


def print_sep(title: str = ""):
    width = 60
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'─' * pad} {title} {'─' * pad}")
    else:
        print(f"\n{'─' * width}")


async def run_graph(agent, input_data, config) -> tuple[list[str], bool]:
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
                        tool_logs.append(f"🔧 툴 호출: {tc['name']}")
                elif isinstance(msg, ToolMessage):
                    tool_logs.append(f"📦 {str(msg.content)[:500]}")
                elif isinstance(msg, AIMessage) and msg.content:
                    content = msg.content
                    if isinstance(content, list):
                        content = " ".join(
                            item.get("text", "") if isinstance(item, dict) else str(item)
                            for item in content
                        )
                    collected.append(content)

    if tool_logs:
        collected = ["\n".join(tool_logs)] + collected

    return collected, interrupted


async def main():
    agent = create_agent(tools=[fusion360_run_script])
    thread_id = str(uuid.uuid4())
    config = get_config(thread_id)

    print(f"\n{'═' * 60}")
    print(f"  DialogCAD — 직접 주입 테스트")
    print(f"  Thread: {thread_id}")
    print(f"{'═' * 60}")
    print(f"\n주입할 params:")
    for k, v in NAMED_PARAMS.items():
        print(f"  {k}: {v}")
    print(f"  shape_tags: {SHAPE_TAGS}")

    # ── 1단계: parse_drawing 실행 (이미지 없어서 에러) ─────────────────
    print_sep("1단계: parse_drawing 스킵")
    messages, interrupted = await run_graph(agent, INITIAL_STATE, config)
    for msg in messages:
        print(f"\n{msg}")

    if not interrupted:
        print("\n❌ confirm_dims interrupt가 발생하지 않았습니다. 그래프 구조를 확인하세요.")
        return

    # ── 2단계: named_params 직접 주입 ─────────────────────────────────
    print_sep("2단계: named_params 주입")
    agent.update_state(config, {
        "named_params": NAMED_PARAMS,
        "shape_tags": SHAPE_TAGS,
        "extracted_dims": {"front": NAMED_PARAMS},  # 포맷 맞추기용
        "user_approved": True,
        "user_feedback": None,
        "dims_confirmed": True,
    })
    print("✅ 주입 완료 → confirm_dims 통과 → csg_plan 진행")

    # ── 3단계: CSG 플랜 생성 ───────────────────────────────────────────
    print_sep("3단계: CSG 플랜 생성")
    messages, interrupted = await run_graph(agent, None, config)
    for msg in messages:
        print(f"\n{msg}")

    if not interrupted:
        print("\n❌ confirm_plan interrupt가 발생하지 않았습니다.")
        return

    # ── 4단계: 플랜 확인 루프 ─────────────────────────────────────────
    while True:
        print_sep("플랜 확인")
        user_input = input("Enter=확인 / 수정 내용 입력: ").strip()

        if user_input == "":
            agent.update_state(config, {"user_approved": True, "user_feedback": None})
            break
        else:
            agent.update_state(config, {"user_approved": False, "user_feedback": user_input})
            print("\n▶ 피드백 반영 중...")
            messages, interrupted = await run_graph(agent, None, config)
            for msg in messages:
                print(f"\n{msg}")
            if not interrupted:
                print("\n⚠️  interrupt 없이 종료됨")
                return

    # ── 5단계: Execute ─────────────────────────────────────────────────
    print_sep("5단계: Fusion 360 실행")
    messages, interrupted = await run_graph(agent, None, config)
    for msg in messages:
        print(f"\n{msg}")

    # ── 6단계: 결과 확인 ───────────────────────────────────────────────
    if interrupted:
        print_sep("결과 확인")
        user_input = input("Enter=확인 / 피드백 입력: ").strip()
        if user_input == "":
            agent.update_state(config, {"user_approved": True, "user_feedback": None})
        else:
            agent.update_state(config, {"user_approved": False, "user_feedback": user_input})

        messages, _ = await run_graph(agent, None, config)
        for msg in messages:
            print(f"\n{msg}")

    print(f"\n{'═' * 60}")
    print("  완료!")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())
