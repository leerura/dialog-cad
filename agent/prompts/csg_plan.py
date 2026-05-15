CSG_PLAN_PROMPT_TEMPLATE = """
당신은 Fusion 360 CSG(Constructive Solid Geometry) 모델링 전문가입니다.
도면 치수와 Few-shot 예시를 참고하여 CSG 오퍼레이션 시퀀스 플랜을 작성하세요.

## 추출된 치수 (named_params)
{named_params_json}

## 형상 태그 (shape_tags)
{shape_tags}

이 태그를 참고하여 각 피처의 타입(box/cylinder 등)을 판단하세요.
예: `cylinder` 또는 `boss` 태그가 있으면 해당 피처는 cylinder로 생성하세요.

## 참고 예시 코드
{retrieved_examples}

---

## CSG 기본 프리미티브 (7가지)
- box(width, height, depth)
- cylinder(radius, height)
- sphere(radius)
- cone(radius1, radius2, height)
- torus(major_radius, minor_radius)
- wedge(width, height, depth, xmin, zmin, xmax, zmax)
- prism(polygon_points, height)

## Boolean 오퍼레이션
- join(body_a, body_b) → 합집합
- cut(body_a, body_b) → 차집합 (body_b를 body_a에서 제거)
- intersect(body_a, body_b) → 교집합

## 좌표계 (중요)
- **Y축 = 높이(수직)**, X축 = 좌우, Z축 = 앞뒤

## 스케치 평면 (sketch_plane)
프리미티브마다 어느 평면에서 스케치할지 명시해야 합니다:
- `"xz"` — XZ 평면에서 스케치 → Y 방향으로 압출 (기본값, 수직 압출)
- `"xy"` — XY 평면에서 스케치 → Z 방향으로 압출 (앞뒤 방향 관통)
- `"yz"` — YZ 평면에서 스케치 → X 방향으로 압출 (좌우 방향 관통)

도면 정면도에서 원이 보이는 피처 → 축이 Z 방향 → `"xy"` 사용
도면 측면도에서 원이 보이는 피처 → 축이 X 방향 → `"yz"` 사용
수직으로 쌓이는 피처 → `"xz"` 사용

position 해석:
- `"xz"` 평면: position.y = 스케치 시작 높이
- `"xy"` 평면: position.z = 스케치 시작 깊이
- `"yz"` 평면: position.x = 스케치 시작 X 위치

## 회전 (rotation)
- 프리미티브 step에 `"rotation"` 필드를 추가하면 해당 body가 생성 후 회전됩니다.
- Fusion 360에서 MoveFeature로 구현됩니다.
- 수평면 회전(탑뷰에서 돌아가 보이는 경우) → `"rotation": {{"axis": "y", "deg": 45}}`
- 회전 없으면 `"rotation": null`

## 반환 형식 (JSON만, 다른 텍스트 없이)

```json
{{
  "steps": [
    {{
      "id": 1,
      "op": "primitive",
      "type": "box",
      "params": {{"width_mm": 100, "height_mm": 30, "depth_mm": 100}},
      "position": {{"x": 0, "y": 0, "z": 0}},
      "sketch_plane": "xz",
      "rotation": {{"axis": "y", "deg": 45}},
      "result_name": "base_body",
      "desc": "베이스 박스 (XZ 평면, Y 방향 압출)"
    }},
    {{
      "id": 2,
      "op": "primitive",
      "type": "cylinder",
      "params": {{"radius_mm": 15, "height_mm": 40}},
      "position": {{"x": 0, "y": 60, "z": -20}},
      "sketch_plane": "xy",
      "rotation": null,
      "result_name": "boss_body",
      "desc": "수평 보스 (XY 평면, Z 방향 압출 — 정면도에서 원으로 보이는 피처, rotation 사용 금지)"
    }},
    {{
      "id": 3,
      "op": "boolean",
      "type": "cut",
      "body_a": "base_body",
      "body_b": "hole_tool",
      "result_name": "final_body",
      "desc": "관통홀 제거"
    }}
  ],
  "final_body": "final_body",
  "notes": "특이사항"
}}
```

## 작성 규칙
1. named_params의 변수명과 값을 params에 직접 사용하세요.
   named_params에 없는 치수는 절대 가정하거나 추정하지 마세요. 치수가 부족한 피처는 생성하지 말고 notes에 "XXX 치수 누락"으로 기재하세요.
2. 각 step은 하나의 오퍼레이션만 수행합니다.
3. Boolean 오퍼레이션은 반드시 이전 step에서 생성된 body를 참조해야 합니다.
4. position은 해당 body의 하단 중심 기준 절대 좌표입니다. Y축 = 높이 (y값이 바닥 높이).
5. 수평 방향 피처(정면도/측면도에서 원으로 보이는 실린더 등)는 sketch_plane으로 방향을 지정하세요. rotation으로 눕히지 마세요.
6. 탑뷰 기준 수평 회전이 필요한 body만 rotation 필드를 채우세요.
7. named_params에 `_count`가 있으면 해당 개수만큼 primitive step을 생성하세요.
"""


CSG_PLAN_MODIFY_TEMPLATE = """
당신은 Fusion 360 CSG 모델링 전문가입니다.
아래 현재 플랜에 사용자 피드백을 반영하여 수정된 플랜을 반환하세요.

## 현재 플랜 (JSON)
{current_plan_json}

## 사용자 피드백
{user_feedback}

## 수정 규칙
- 피드백에서 명시적으로 언급된 부분만 변경하세요.
- 언급되지 않은 step과 필드는 원본 JSON 값을 그대로 유지하세요.
- 반환 형식은 원본과 동일한 JSON 구조를 유지하세요 (JSON만, 다른 텍스트 없이).
- rotation 관련 피드백은 반드시 해당 step의 `"rotation"` JSON 필드를 추가/수정하세요. description 텍스트 변경만으로는 부족합니다.
  예: "베이스 45도 회전" → 해당 step에 `"rotation": {{"axis": "y", "deg": 45}}` 추가 (Y축 = 수직축, 탑뷰 기준 수평 회전)
"""


def build_csg_plan_prompt(named_params: dict, retrieved_examples: str, shape_tags: list | None = None) -> str:
    import json
    tags_str = ", ".join(shape_tags) if shape_tags else "*(태그 없음)*"
    return CSG_PLAN_PROMPT_TEMPLATE.format(
        named_params_json=json.dumps(named_params, ensure_ascii=False, indent=2),
        shape_tags=tags_str,
        retrieved_examples=retrieved_examples or "*(참고 예시 없음)*",
    )


def build_csg_plan_modify_prompt(current_plan: dict, user_feedback: str) -> str:
    import json
    return CSG_PLAN_MODIFY_TEMPLATE.format(
        current_plan_json=json.dumps(current_plan, ensure_ascii=False, indent=2),
        user_feedback=user_feedback,
    )
