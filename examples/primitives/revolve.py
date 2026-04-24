# 검증 완료: Fusion 360 2701.1.27
# 설명: XZ 평면에 단면 그리고 Z축으로 360도 Revolve (컵 모양)
# 핵심 패턴: 스케치 안에 그린 선을 회전축으로 사용 (ConstructionAxis 아님!)

import adsk.core, adsk.fusion, math

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Revolve"')
try:
    sketches = root.sketches
    xzPlane = root.xZConstructionPlane

    # 1) 회전 단면 스케치 (XZ 평면) - 컵 모양
    sk = sketches.add(xzPlane)
    lines = sk.sketchCurves.sketchLines
    pts = [
        adsk.core.Point3D.create(0, 0, 0),  # 바닥 중심
        adsk.core.Point3D.create(5, 0, 0),  # 바닥 끝
        adsk.core.Point3D.create(5, 0, 3),  # 모서리
        adsk.core.Point3D.create(3, 0, 3),  # 안쪽
        adsk.core.Point3D.create(3, 0, 8),  # 위 지점
        adsk.core.Point3D.create(0, 0, 8),  # 위 중심
    ]
    for i in range(len(pts) - 1):
        lines.addByTwoPoints(pts[i], pts[i+1])
    lines.addByTwoPoints(pts[-1], pts[0])  # 닫기

    # 2) 회전축: 스케치 안에 Z축 선분으로 정의
    # ❌ root.zConstructionAxis 사용 불가 → ✅ 스케치 안에 선 직접 그리기
    axisLine = lines.addByTwoPoints(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(0, 0, 8)
    )

    # 3) Revolve 360도
    revolves = root.features.revolveFeatures
    revInput = revolves.createInput(
        sk.profiles.item(0),
        axisLine,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    revInput.setAngleExtent(True, adsk.core.ValueInput.createByReal(2 * math.pi))
    revolves.add(revInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise