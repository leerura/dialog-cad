import os
from functools import partial

from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import create_react_agent

from agent.nodes.csg_plan import csg_plan_node
from agent.nodes.confirm_dims import confirm_dims_node
from agent.nodes.confirm_plan import confirm_plan_node
from agent.nodes.confirm_result import confirm_result_node
from agent.nodes.execute import execute_node
from agent.nodes.parse_drawing import parse_drawing_node
from agent.nodes.verify import verify_node
from agent.prompts.system import EXECUTE_SYSTEM_PROMPT
from agent.routers import (
    route_after_confirm_dims,
    route_after_confirm_plan,
    route_after_confirm_result,
    route_after_execute,
    route_after_verify,
)
from agent.state import DialogCADState

load_dotenv()


def create_agent(tools: list):
    # 계획·추론 노드용: thinking 허용 (parse, csg_plan, verify)
    planning_model = ChatVertexAI(
        model="gemini-2.5-flash",
        project=os.getenv("GCP_PROJECT_ID"),
        location="us-central1",
        thinking_budget=2048,
    )

    # execute 에이전트용: thinking=0으로 완전히 끔 → 빈 응답 방지
    execute_model = ChatVertexAI(
        model="gemini-2.5-flash",
        project=os.getenv("GCP_PROJECT_ID"),
        location="us-central1",
        thinking_budget=0,
    )

    react_agent = create_react_agent(
        model=execute_model,
        tools=tools,
        prompt=EXECUTE_SYSTEM_PROMPT,
        checkpointer=False,
    )

    graph = StateGraph(DialogCADState)

    # ── 노드 등록 ────────────────────────────────────────────
    graph.add_node("parse_drawing",  partial(parse_drawing_node, model=planning_model))
    graph.add_node("confirm_dims",   confirm_dims_node)
    graph.add_node("csg_plan",       partial(csg_plan_node, model=planning_model))
    graph.add_node("confirm_plan",   confirm_plan_node)
    graph.add_node("execute",        partial(execute_node, agent=react_agent))
    graph.add_node("verify",         partial(verify_node, model=planning_model))
    graph.add_node("confirm_result", confirm_result_node)

    # ── 진입점 ──────────────────────────────────────────────
    graph.set_entry_point("parse_drawing")

    # ── 엣지 ────────────────────────────────────────────────
    graph.add_edge("parse_drawing", "confirm_dims")

    graph.add_conditional_edges("confirm_dims", route_after_confirm_dims, {
        "csg_plan":      "csg_plan",
        "parse_drawing": "parse_drawing",
    })

    graph.add_edge("csg_plan", "confirm_plan")

    graph.add_conditional_edges("confirm_plan", route_after_confirm_plan, {
        "execute":  "execute",
        "csg_plan": "csg_plan",
    })

    graph.add_conditional_edges("execute", route_after_execute, {
        "verify": "verify",
        END:      END,
    })

    graph.add_conditional_edges("verify", route_after_verify, {
        "confirm_result": "confirm_result",
        "execute":        "execute",
    })

    graph.add_conditional_edges("confirm_result", route_after_confirm_result, {
        END:             END,
        "parse_drawing": "parse_drawing",
    })

    return graph.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["confirm_dims", "confirm_plan", "confirm_result"],
    )
