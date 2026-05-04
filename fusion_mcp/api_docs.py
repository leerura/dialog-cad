"""
CSG 플랜을 분석하여 필요한 Fusion 360 API 문서를 사전 fetch합니다.
동일 클래스 문서는 모듈 레벨로 캐싱하여 반복 호출 시 즉시 반환합니다.
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# ── CSG operation → 필요한 Fusion 360 API 클래스 매핑 ─────────────────
# Input 클래스를 우선 조회 — 메서드 시그니처가 가장 유용함

_PRIMITIVE_TO_CLASSES: dict[str, list[str]] = {
    "box":      ["ExtrudeFeatureInput", "SketchLines"],
    "cylinder": ["ExtrudeFeatureInput", "SketchCircles"],
    "cone":     ["ExtrudeFeatureInput", "SketchCircles"],
    "sphere":   ["ExtrudeFeatureInput"],
    "wedge":    ["ExtrudeFeatureInput", "SketchLines"],
    "prism":    ["ExtrudeFeatureInput", "SketchLines"],
    "torus":    ["ExtrudeFeatureInput", "SketchCircles"],
}

_BOOLEAN_CLASSES   = ["CombineFeatureInput"]
_ROTATION_CLASSES  = ["MoveFeatureInput", "Matrix3D"]
_POSITION_CLASSES  = ["ConstructionPlaneInput", "OffsetStartDefinition"]

# ── 문서 캐시 ─────────────────────────────────────────────────────────
_cache: dict[str, str] = {}


async def _make_fusion_tool():
    client = MultiServerMCPClient(
        {
            "fusion360": {
                "transport": "sse",
                "url": os.getenv("FUSION_URL"),
                "headers": {"Authorization": os.getenv("FUSION_AUTH")},
            }
        }
    )
    tools = await client.get_tools()
    return next(t for t in tools if t.name == "fusion360")


async def _fetch_class_doc(fusion_tool, class_name: str) -> str:
    """단일 클래스의 API 문서를 fetch하고 읽기 좋은 텍스트로 변환합니다."""
    if class_name in _cache:
        return _cache[class_name]

    result = await fusion_tool.ainvoke({
        "operation": "get_api_documentation",
        "search_term": class_name,
        "category": "class_name",
        "max_results": 1,
        "tool_unlock_token": os.getenv("FUSION_TOKEN"),
    })

    # MCP 응답 파싱
    raw = result
    if isinstance(raw, list):
        raw = raw[0] if raw else {}
        if isinstance(raw, dict) and "text" in raw:
            try:
                raw = json.loads(raw["text"])[0]
            except Exception:
                raw = {}
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            raw = parsed[0] if isinstance(parsed, list) else parsed
        except Exception:
            _cache[class_name] = raw
            return raw

    # 사람이 읽기 좋은 포맷으로 변환
    lines = [f"**{raw.get('name', class_name)}** ({raw.get('namespace', '')})"]
    if raw.get("doc"):
        lines.append(raw["doc"].strip())

    props = raw.get("properties", [])
    if props:
        lines.append("Properties: " + ", ".join(p["name"] for p in props))

    funcs = raw.get("functions", [])
    if funcs:
        lines.append("Methods: " + ", ".join(f["name"] for f in funcs))

    text = "\n".join(lines)
    _cache[class_name] = text
    return text


def _collect_classes(csg_plan: dict) -> list[str]:
    """CSG 플랜에서 필요한 API 클래스명을 중복 없이 추출합니다."""
    needed: set[str] = set()

    for step in csg_plan.get("steps", []):
        op        = step.get("op", "")
        step_type = step.get("type", "")

        if op == "primitive":
            needed.update(_PRIMITIVE_TO_CLASSES.get(step_type, ["ExtrudeFeatureInput"]))

            if step.get("rotation"):
                needed.update(_ROTATION_CLASSES)

            position = step.get("position", {})
            if isinstance(position, dict) and position.get("y", 0) != 0:
                needed.update(_POSITION_CLASSES)

        elif op == "boolean":
            needed.update(_BOOLEAN_CLASSES)

    return list(needed)


async def get_api_docs_for_plan(csg_plan: dict) -> str:
    """
    CSG 플랜을 분석하여 필요한 Fusion 360 API 문서를 병렬로 fetch합니다.
    반환값은 execute_node의 instruction에 주입할 마크다운 텍스트입니다.
    """
    classes = _collect_classes(csg_plan)
    if not classes:
        return ""

    # 캐시 미스 항목만 병렬 fetch
    uncached = [c for c in classes if c not in _cache]
    if uncached:
        fusion_tool = await _make_fusion_tool()
        results = await asyncio.gather(
            *[_fetch_class_doc(fusion_tool, c) for c in uncached],
            return_exceptions=True,
        )
        for cls, res in zip(uncached, results):
            if not isinstance(res, Exception):
                _cache[cls] = res
            else:
                print(f"[API_DOCS] fetch 실패: {cls} — {res}")

    sections = [
        f"#### {cls}\n{_cache[cls]}"
        for cls in classes
        if cls in _cache and _cache[cls]
    ]
    return "\n\n".join(sections)
