import json
from pathlib import Path

_EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def _load_metadata() -> dict[str, dict]:
    meta = {}
    for meta_file in _EXAMPLES_DIR.rglob("metadata.json"):
        folder = meta_file.parent
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        for filename, info in data.items():
            meta[str(folder / filename)] = info
    return meta


def retrieve_examples(shape_tags: list[str], top_k: int = 3) -> str:
    """
    shape_tags와 태그 오버랩이 가장 많은 예시 파일 top_k개를 반환.
    반환값: 각 예시의 코드를 헤더와 함께 이어붙인 문자열
    """
    if not shape_tags:
        return ""

    tag_set = set(t.lower() for t in shape_tags)
    metadata = _load_metadata()

    scored: list[tuple[int, str, dict]] = []
    for filepath, info in metadata.items():
        file_tags = set(t.lower() for t in info.get("tags", []))
        score = len(tag_set & file_tags)
        if score > 0:
            scored.append((score, filepath, info))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    if not top:
        return ""

    parts = []
    for _, filepath, info in top:
        path = Path(filepath)
        if not path.exists():
            continue
        code = path.read_text(encoding="utf-8")
        parts.append(f"### {path.name} — {info['desc']}\n```python\n{code}\n```")

    return "\n\n".join(parts)
