from typing import Annotated
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class DialogCADState(TypedDict):
    # ── 메시지 ──────────────────────────────────────────────
    messages: Annotated[list, add_messages]

    # ── 입력 ────────────────────────────────────────────────
    image_path: str | None

    # ── Stage 1: 치수 추출 ──────────────────────────────────
    extracted_dims: dict | None       # 뷰별 치수 원본
    named_params: dict | None         # {"base_width_mm": 20, ...}
    shape_tags: list[str] | None      # RAG 검색용 형상 태그

    # ── Stage 2: CSG 플랜 ────────────────────────────────────
    retrieved_examples: str | None    # RAG로 검색된 예시 코드
    csg_plan: dict | None             # CSG 오퍼레이션 시퀀스
    execution_plan: str | None        # execute 노드에 전달할 완성 지시문

    # ── Stage 3: 코드 실행 ──────────────────────────────────
    execution_result: str | None      # Fusion 360 실행 결과 (ToolMessage)
    tool_called: bool | None

    # ── Stage 4: 검증 ───────────────────────────────────────
    verified: bool | None
    retry_count: int

    # ── HITL 공통 ───────────────────────────────────────────
    hitl_stage: str | None            # "dims_confirm" | "plan_confirm" | "result_confirm"
    user_approved: bool | None
    user_feedback: str | None
    dims_feedback_history: list[str] | None   # 치수 피드백 누적 목록

    # ── HITL 플래그 ─────────────────────────────────────────
    dims_confirmed: bool | None
    plan_confirmed: bool | None
    result_confirmed: bool | None
