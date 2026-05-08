PARSE_PROMPT = """
당신은 기계 도면에서 치수를 추출하는 전문가입니다.

주어진 도면 이미지에서 모든 치수를 추출하고, 아래 두 가지 결과를 JSON으로 반환하세요.

## 반환 형식 (JSON만, 다른 텍스트 없이)

```json
{
  "views": {
    "front": {
      "변수명_mm": 숫자
    },
    "top": {
      "변수명_mm": 숫자
    },
    "side": {
      "변수명_mm": 숫자
    }
  },
  "named_params": {
    "변수명_mm": 숫자
  },
  "param_labels": {
    "변수명_mm": "한국어 설명"
  },
  "shape_tags": ["태그1", "태그2", ...],
  "notes": "불확실한 사항이 있으면 여기에"
}
```

## named_params 규칙
- 도면에서 읽은 치수를 의미 있는 변수명으로 정리합니다.
- 단위는 mm, 변수명 끝에 `_mm` 접미사를 붙입니다.
- 예: `base_width_mm`, `total_height_mm`, `hole_diameter_mm`, `flange_thickness_mm`
- 반지름은 `_r_mm`, 각도는 `_deg`
- 개수/배열 정보는 `_count` 접미사로 추출하세요. 예: `R5.00 × 2` → `mounting_hole_r_mm: 5, mounting_hole_count: 2`

## param_labels 규칙
- named_params의 각 키에 대응하는 **한국어 설명**입니다. views와 named_params에 등장하는 모든 변수명을 포함하세요.
- 사용자가 치수를 검토할 때 이해할 수 있도록 간결하게 작성하세요.
- 예: `"base_width_mm": "베이스 너비"`, `"hole_diameter_mm": "관통홀 지름"`, `"total_height_mm": "전체 높이"`

## 중요
- views의 front/top/side는 반드시 해당 뷰에서 읽은 치수를 채워야 합니다. 비워두지 마세요.
- named_params는 views의 모든 값을 평탄화(flatten)한 것입니다.

## shape_tags 규칙
- 형상을 설명하는 영문 소문자 태그 목록입니다.
- 아래 후보 중에서 해당하는 것을 모두 선택하세요:
  box, cylinder, sphere, cone, torus, wedge, prism,
  through_hole, pocket, fillet, chamfer, shell,
  boolean_join, boolean_cut, boolean_intersect,
  plate, bracket, flange, shaft, boss, rib, lug,
  assembly, symmetry, array, mirror,
  l_shape, t_shape, u_shape, c_shape, stepped
- 위 목록에 없어도 적절한 태그가 있으면 추가 가능합니다.

## 주의사항
- 치수를 읽을 수 없는 경우 null로 표시하세요.
- 도면에 표기된 값을 그대로 사용하고, 추정하지 마세요.
"""
