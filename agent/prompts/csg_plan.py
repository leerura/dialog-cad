CSG_PLAN_PROMPT_TEMPLATE = """
당신은 Fusion 360 CSG(Constructive Solid Geometry) 모델링 전문가입니다.
도면 치수와 Few-shot 예시를 참고하여 CSG 오퍼레이션 시퀀스 플랜을 작성하세요.

## 추출된 치수 (named_params)
{named_params_json}

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

## 회전 (rotation)
- 프리미티브 step에 `"rotation"` 필드를 추가하면 해당 body가 생성 후 회전됩니다.
- Fusion 360에서 MoveFeature로 구현됩니다.
- 예: base가 45도 회전된 경우 → `"rotation": {{"axis": "z", "deg": 45}}`
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
      "rotation": {{"axis": "z", "deg": 45}},
      "result_name": "base_body",
      "desc": "베이스 박스 (Z축 45도 회전)"
    }},
    {{
      "id": 2,
      "op": "primitive",
      "type": "cylinder",
      "params": {{"radius_mm": 15, "height_mm": 30}},
      "position": {{"x": 0, "y": 0, "z": 60}},
      "rotation": null,
      "result_name": "boss_body",
      "desc": "원통형 보스"
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
2. 각 step은 하나의 오퍼레이션만 수행합니다.
3. Boolean 오퍼레이션은 반드시 이전 step에서 생성된 body를 참조해야 합니다.
4. position은 해당 body의 하단 중심 기준 절대 좌표입니다. Z축 = 높이.
5. 회전이 필요한 body는 rotation 필드를 반드시 채우세요 (null 아님).
6. 예시 코드의 패턴을 최대한 따르세요.
"""


def build_csg_plan_prompt(named_params: dict, retrieved_examples: str) -> str:
    import json
    return CSG_PLAN_PROMPT_TEMPLATE.format(
        named_params_json=json.dumps(named_params, ensure_ascii=False, indent=2),
        retrieved_examples=retrieved_examples or "*(참고 예시 없음)*",
    )
