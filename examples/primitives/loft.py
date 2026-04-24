# examples/primitives/loft.py
# 검증 완료: Fusion 360 2701.1.27
# 설명: 아래는 사각형(10x10), 위는 원형(R=3), 높이 10 Loft
# 핵심 패턴: 두 평면에 각각 스케치 → loftSections.add() 순서대로 추가

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Loft"')
try:
    sketches = root.sketches
    xyPlane = root.xYConstructionPlane

    # 1) 아래 단면: 10x10 사각형 (Z=0)
    skBottom = sketches.add(xyPlane)
    skBottom.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-5, -5, 0),
        adsk.core.Point3D.create(5, 5, 0)
    )

    # 2) 위 단면: 원형 R=3 (Z=10)
    planes = root.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(10))
    topPlane = planes.add(planeInput)

    skTop = sketches.add(topPlane)
    skTop.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 10), 3.0
    )

    # 3) Loft - 아래→위 순서로 섹션 추가
    lofts = root.features.loftFeatures
    loftInput = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    loftInput.loftSections.add(skBottom.profiles.item(0))
    loftInput.loftSections.add(skTop.profiles.item(0))
    lofts.add(loftInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise