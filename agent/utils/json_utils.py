import json
import re


def parse_json_response(raw: str) -> dict:
    """LLM 응답에서 JSON 파싱 (코드 블록, 마크다운 처리 포함)"""
    # ```json ... ``` 또는 ``` ... ``` 블록 추출
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        raw = match.group(1)

    return json.loads(raw.strip())


def extract_text_content(content) -> str:
    """Gemini list 타입 content에서 텍스트 추출"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )
    return str(content)
