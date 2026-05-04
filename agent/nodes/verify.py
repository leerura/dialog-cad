from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI

from agent.state import DialogCADState
from agent.utils.json_utils import extract_text_content
from agent.utils.token_tracker import track_tokens

VERIFY_PROMPT = """
아래 Fusion 360 실행 결과를 검증하세요.

확인 항목:
1. error 필드가 없거나 비어 있는가?
2. stderr가 없거나 비어 있는가?
3. 실행이 정상 완료됐는가?
4. stdout에 "DONE: N bodies" 형태의 문자열이 있는가? (없으면 스크립트가 실제로 실행되지 않은 것)

실행 결과:
{result}

다음 형식으로만 답하세요:
RESULT: pass | fail
REASON: (실패 이유, pass면 생략)
"""


@track_tokens("verify")
def verify_node(state: DialogCADState, model: ChatVertexAI) -> dict:
    execution_result = state.get("execution_result", "")

    response = model.invoke([HumanMessage(content=VERIFY_PROMPT.format(result=execution_result))])
    content = extract_text_content(response.content)

    verified = "RESULT: pass" in content
    print(f"[VERIFY] verified={verified} | {content[:100]}")

    meta = getattr(response, "usage_metadata", None)
    usage = {}
    if meta:
        usage = {
            "input_tokens": meta.get("input_tokens", 0) if isinstance(meta, dict) else getattr(meta, "input_tokens", 0),
            "output_tokens": meta.get("output_tokens", 0) if isinstance(meta, dict) else getattr(meta, "output_tokens", 0),
        }

    retry_count = state.get("retry_count", 0)

    if verified:
        return {
            "verified": True,
            "hitl_stage": "result_confirm",
            "retry_count": retry_count,
            "messages": [AIMessage(content=f"✅ 실행 검증 완료.\n\n{content}")],
            "last_token_usage": usage,
        }
    else:
        return {
            "verified": False,
            "retry_count": retry_count + 1,
            "messages": [AIMessage(content=f"❌ 실행 실패.\n\n{content}")],
            "last_token_usage": usage,
        }
