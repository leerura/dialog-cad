# 🤖 DialogCAD — AI-Powered CAD Agent

도면 이미지를 업로드하면 **치수 추출 → 형상 플랜 수립 → Fusion 360 실행**까지
end-to-end로 자동화하는 대화형 멀티스테이지 AI 에이전트입니다.

---

## Architecture

```
도면 이미지 입력
      ↓
parse_drawing  →  confirm_dims ──(수정)──→ parse_drawing
                       ↓(승인)
   csg_plan    →  confirm_plan ──(수정)──→ csg_plan
                       ↓(승인)
    execute    →     verify   ──(실패)──→ execute
                       ↓(성공)
 confirm_result →   [END]
```

LangGraph 기반 7노드 상태 머신으로 구성되며,
`confirm_dims` / `confirm_plan` / `confirm_result` 3단계에서
HITL(Human-in-the-Loop) 인터럽트로 사용자 승인·수정을 즉시 반영합니다.

| 노드 | 역할 | 모델 |
|---|---|---|
| `parse_drawing` | 도면 이미지에서 수치·형상 정보 추출 | Gemini 2.5 Flash |
| `confirm_dims` | 추출된 수치 사용자 확인 (HITL) | — |
| `csg_plan` | CSG 프리미티브 조합 플랜 수립 | Gemini 2.5 Flash |
| `confirm_plan` | CSG 플랜 사용자 승인 (HITL) | — |
| `execute` | Fusion 360 스크립트 작성 및 실행 (ReAct Agent) | Gemini 2.5 Pro |
| `verify` | 실행 결과 검증 (0-bodies hard-fail) | Gemini 2.5 Flash |
| `confirm_result` | 최종 결과 사용자 확인 (HITL) | — |

---

## Key Features

### CSG 플랜 방식
복잡한 3D 형상을 box·cylinder·sphere 등 기본 도형과 Boolean 연산(fuse/cut)의 조합으로 분해합니다.
LLM이 3D 좌표를 직접 계산하는 대신 형상 조합 논리를 출력하게 해 공간 추론 오류를 구조적으로 제거합니다.

```json
{
  "primitives": [
    { "id": "base", "type": "box", "width": 100, "height": 20, "depth": 60 },
    { "id": "hole", "type": "cylinder", "radius": 10, "height": 25, "origin": [50, 0, 30] }
  ],
  "operations": [
    { "type": "cut", "target": "base", "tool": "hole" }
  ]
}
```

### API 문서 동적 주입
실행 전마다 CSG 플랜의 형상 태그를 분석해 관련 Fusion 360 API 문서와 코드 예시를 프롬프트에 자동 삽입합니다.
재시도 시에도 원본 수치·플랜이 명시적으로 포함되므로 정보 손실 없이 코드만 수정됩니다.

> 평균 재시도 횟수: **3회 → 1회**

### Self-Healing 루프
`verify` 노드에서 실행 결과를 재검증하고 실패 시 `execute` 노드로 자동 복귀합니다.
`DONE: 0 bodies` 감지 시 LLM 호출 없이 즉시 fail 처리합니다(hard-fail guard).

### HITL 인터럽트
치수 확인 → 플랜 승인 → 최종 결과 3단계에서 사용자가 자연어로 수정 내용을 입력하면
파이프라인이 해당 단계부터 다시 실행됩니다.

---

## Tech Stack

| 분류 | 기술 |
|---|---|
| Agent Framework | LangGraph, LangChain |
| LLM | Gemini 2.5 Flash (planning), Gemini 2.5 Pro (execute) |
| CAD Integration | Fusion 360 MCP |
| UI | Gradio |
| Runtime | Python 3.11+ |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Fusion 360 및 Fusion 360 MCP 서버
- Google Cloud 프로젝트 (Vertex AI 활성화)

### Installation

```bash
git clone https://github.com/leerura/dialog-cad.git
cd dialog-cad
pip install -r requirements.txt
```

### Environment Variables

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
GCP_PROJECT_ID=your-gcp-project-id
FUSION_URL=your-fusion-mcp-server-url
FUSION_AUTH=your-fusion-auth-token
FUSION_TOKEN=your-fusion-tool-unlock-token
```

### Run

```bash
python app.py
```

브라우저에서 `http://localhost:7860` 접속 후 도면 이미지를 업로드합니다.

---

## Project Structure

```
dialog-cad/
├── agent/
│   ├── graph.py            # LangGraph 상태 머신 정의
│   ├── state.py            # 공유 상태(DialogCADState) 정의
│   ├── routers.py          # 조건부 엣지 라우터
│   ├── nodes/
│   │   ├── parse_drawing.py
│   │   ├── confirm_dims.py
│   │   ├── csg_plan.py
│   │   ├── confirm_plan.py
│   │   ├── execute.py
│   │   ├── verify.py
│   │   └── confirm_result.py
│   ├── prompts/
│   │   └── system.py       # 시스템 프롬프트
│   └── utils/
│       └── token_tracker.py
├── fusion_mcp/
│   ├── api_docs.py         # 형상 태그 기반 API 문서 동적 주입
│   ├── docs.py             # Fusion 360 Best Practices 로드
│   └── wrapper.py          # MCP 툴 래퍼 (fusion360_run_script)
├── examples/
│   ├── primitives/         # 기본 도형 예시 스크립트
│   └── assemblies/         # 조립 형상 예시 스크립트
├── app.py                  # Gradio UI 진입점
└── requirements.txt
```
