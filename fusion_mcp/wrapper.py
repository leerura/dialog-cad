import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

FUSION_URL = os.getenv("FUSION_URL")
FUSION_TOKEN = os.getenv("FUSION_TOKEN")
FUSION_AUTH = os.getenv("FUSION_AUTH")


@tool
async def fusion360_run_script(code: str) -> str:
    """
    Fusion 360에서 Python 스크립트를 실행합니다.
    code: 실행할 Fusion 360 API Python 코드 (전체 스크립트)
    """
    client = MultiServerMCPClient(
        {
            "fusion360": {
                "transport": "sse",
                "url": FUSION_URL,
                "headers": {"Authorization": FUSION_AUTH},
            }
        }
    )

    tools = await client.get_tools()
    fusion_tool = next(t for t in tools if t.name == "fusion360")

    try:
        result = await fusion_tool.ainvoke({
            "operation": "execute_python",
            "code": code,
            "tool_unlock_token": FUSION_TOKEN,
        })
        return str(result)
    except Exception as e:
        return f"실행 오류: {e}\n코드를 수정해서 다시 시도하세요."
