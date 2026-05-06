"""
CSG 플랜을 분석하여 필요한 Fusion 360 API 문서를 사전 fetch합니다.
get_online_documentation으로 공식 파라미터 명세 + 예제 코드까지 포함.
동일 클래스 문서는 모듈 레벨로 캐싱하여 반복 호출 시 즉시 반환합니다.
"""

import asyncio
import json
import os
import re

import httpx
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# ── CSG operation → (class_name, member_name) 매핑 ────────────────────
# get_online_documentation 기준: 메서드가 정의된 컬렉션 클래스 + 메서드명
_PRIMITIVE_TO_CLASSES: dict[str, list[tuple[str, str | None]]] = {
    "box":      [("ExtrudeFeatures", "createInput"), ("SketchLines", None)],
    "cylinder": [("ExtrudeFeatures", "createInput"), ("SketchCircles", None)],
    "cone":     [("ExtrudeFeatures", "createInput"), ("SketchCircles", None)],
    "sphere":   [("ExtrudeFeatures", "createInput")],
    "wedge":    [("ExtrudeFeatures", "createInput"), ("SketchLines", None)],
    "prism":    [("ExtrudeFeatures", "createInput"), ("SketchLines", None)],
    "torus":    [("ExtrudeFeatures", "createInput"), ("SketchCircles", None)],
}

_BOOLEAN_CLASSES  = [("CombineFeatures", "createInput")]
_ROTATION_CLASSES = [("MoveFeatures", "createInput"), ("Matrix3D", None)]
_POSITION_CLASSES = [("ConstructionPlanes", "createInput"), ("OffsetStartDefinition", "create")]

# ── 문서 캐시 ──────────────────────────────────────────────────────────
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


async def _fetch_sample_code(url: str) -> str:
    """Autodesk cloudhelp 샘플 페이지에서 Python 코드 블록을 추출합니다."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            html = resp.text
        matches = re.findall(r"<pre[^>]*>(.*?)</pre>", html, re.DOTALL)
        if not matches:
            return ""
        code = max(matches, key=len)
        code = (
            code.replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
                .replace("&#39;", "'")
                .replace("&quot;", '"')
        )
        code = re.sub(r"<[^>]+>", "", code)
        return code.strip()
    except Exception as e:
        print(f"[API_DOCS] 샘플 fetch 실패: {url} — {e}")
        return ""


async def _fetch_class_doc(fusion_tool, class_name: str, member_name: str | None) -> str:
    """get_online_documentation으로 파라미터 명세 + 예제 코드를 fetch합니다."""
    cache_key = f"{class_name}.{member_name or '*'}"
    if cache_key in _cache:
        return _cache[cache_key]

    invoke_args: dict = {
        "operation": "get_online_documentation",
        "class_name": class_name,
        "tool_unlock_token": os.getenv("FUSION_TOKEN"),
    }
    if member_name:
        invoke_args["member_name"] = member_name

    try:
        result = await fusion_tool.ainvoke(invoke_args)
    except Exception as e:
        print(f"[API_DOCS] fetch 실패: {cache_key} — {e}")
        _cache[cache_key] = ""
        return ""

    # MCP 응답 파싱
    if isinstance(result, list):
        result = result[0] if result else {}
        if isinstance(result, dict) and "text" in result:
            try:
                result = json.loads(result["text"])
            except Exception:
                result = {}
    if not isinstance(result, dict):
        _cache[cache_key] = ""
        return ""

    lines = [f"#### {class_name}" + (f".{member_name}" if member_name else "")]

    # 파라미터 명세 (타입 포함)
    params = result.get("parameters", [])
    if params:
        lines.append("Parameters:")
        for p in params:
            lines.append(f"  - {p['name']} ({p.get('type', '?')}): {p.get('description', '')}")

    ret = result.get("return_type")
    if ret:
        lines.append(f"Returns: {ret}")

    # 예제 코드 — 공식 샘플 URL에서 직접 fetch
    samples = result.get("samples", [])
    if samples:
        sample_url = samples[0].get("url", "")
        if sample_url:
            code = await _fetch_sample_code(sample_url)
            if code:
                lines.append(f"Example:\n```python\n{code}\n```")

    text = "\n".join(lines)
    _cache[cache_key] = text
    return text


def _collect_classes(csg_plan: dict) -> list[tuple[str, str | None]]:
    """CSG 플랜에서 필요한 (class_name, member_name) 쌍을 중복 없이 추출합니다."""
    needed: set[tuple[str, str | None]] = set()

    for step in csg_plan.get("steps", []):
        op        = step.get("op", "")
        step_type = step.get("type", "")

        if op == "primitive":
            needed.update(
                _PRIMITIVE_TO_CLASSES.get(step_type, [("ExtrudeFeatures", "createInput")])
            )
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

    uncached = [(c, m) for c, m in classes if f"{c}.{m or '*'}" not in _cache]
    if uncached:
        fusion_tool = await _make_fusion_tool()
        results = await asyncio.gather(
            *[_fetch_class_doc(fusion_tool, c, m) for c, m in uncached],
            return_exceptions=True,
        )
        for (cls, mem), res in zip(uncached, results):
            cache_key = f"{cls}.{mem or '*'}"
            if isinstance(res, Exception):
                print(f"[API_DOCS] fetch 실패: {cache_key} — {res}")
                _cache[cache_key] = ""

    sections = [
        _cache[f"{cls}.{mem or '*'}"]
        for cls, mem in classes
        if _cache.get(f"{cls}.{mem or '*'}")
    ]
    return "\n\n".join(sections)
