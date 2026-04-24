# examples/extrude_cut.py
# 검증 완료: Fusion 360 2701.1.27
# 설명: 직육면체에 원형 구멍을 뚫는 Extrude Cut 예시

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Box with Hole"')
try:
    sketches = root.sketches
    xyPlane = root.xYConstructionPlane

    # 1) 베이스 박스 스케치 (10 x 10)
    boxSketch = sketches.add(xyPlane)
    lines = boxSketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(10, 10, 0)
    )

    # 2) Extrude 높이 5
    extrudes = root.features.extrudeFeatures
    extInput = extrudes.createInput(
        boxSketch.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5))
    extrudes.add(extInput)

    # 3) 구멍 스케치 - 오프셋 평면 (Z=5 윗면)
    planes = root.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(5))
    topPlane = planes.add(planeInput)

    holeSketch = sketches.add(topPlane)
    holeSketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(5, 5, 5),
        2.0  # 반지름
    )

    # 4) Extrude Cut (관통)
    cutInput = extrudes.createInput(
        holeSketch.profiles.item(0),
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    cutInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
    extrudes.add(cutInput)

    app.executeTextCommand('PTransaction.Commit')

except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise