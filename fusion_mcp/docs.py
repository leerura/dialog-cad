import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

_cache: str | None = None


async def get_fusion_best_practices() -> str:
    """
    MCP에서 Fusion 360 베스트 프랙티스 문서를 가져옵니다.
    첫 호출 시 fetch 후 모듈 레벨로 캐싱 — 이후 호출은 즉시 반환.
    """
    global _cache
    if _cache is not None:
        return _cache

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
    fusion_tool = next(t for t in tools if t.name == "fusion360")

    result = await fusion_tool.ainvoke({
        "operation": "get_best_practices",
        "tool_unlock_token": os.getenv("FUSION_TOKEN"),
    })

    # MCP 응답은 [{'type': 'text', 'text': '...'}] 형태일 수 있음 — 텍스트만 추출
    if isinstance(result, list):
        _cache = "\n".join(
            item["text"] if isinstance(item, dict) and "text" in item else str(item)
            for item in result
        )
    elif isinstance(result, dict) and "text" in result:
        _cache = result["text"]
    else:
        _cache = str(result)

    return _cache
