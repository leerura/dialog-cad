# bolt_hole_plate

## 설명

20x10 직사각형 플레이트에 네 모서리에 볼트 홀 4개를 뚫는 형상.

## 파라미터

- W=20 (X방향 너비)
- D=10 (Y방향 깊이)
- T=3 (Z방향 두께)
- R=1.0 (구멍 반지름)
- 구멍 위치: 모서리에서 (2, 2) 오프셋

## ASCII 단면도 (XY 평면, 위에서 본 모습)

Y
▲
10─┤ ○ ○ ├─
│ │
│ │
0─┤ ○ ○ ├─
└──────────────────►X
0 2 18 20

## Feature 순서

1. XY평면에 W×D (20×10) 직사각형 스케치 → +Z 방향 T(3) extrude
2. Z=T(3) 오프셋 평면 생성
3. 오프셋 평면에 원 4개 한 스케치에 그리기 (ObjectCollection)
4. NegativeExtentDirection으로 한번에 CutFeatureOperation

## 구멍 위치 (X, Y, Z)

- (2, 2, 3) 좌하단
- (18, 2, 3) 우하단
- (2, 8, 3) 좌상단
- (18, 8, 3) 우상단

## 핵심 패턴

- 다중 구멍: 한 스케치에 모든 원 → ObjectCollection으로 한번에 Cut
- 구멍마다 별도 Extrude Cut 금지 → body 복제됨
