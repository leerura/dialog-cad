# examples/primitives/circular_pattern.py
# 검증 완료: Fusion 360 2701.1.27
# 설명: 원형 플레이트에 볼트홀 6개를 원형 배열 (Circular Pattern)
# 핵심 패턴: 구멍 1개 만들고 → circularPatternFeatures로 Z축 기준 등간격 복제

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Circular Pattern"')
try:
    sketches = root.sketches
    extrudes = root.features.extrudeFeatures
    xyPlane = root.xYConstructionPlane

    # 1) 원형 베이스 (R=15, 두께 3)
    sk = sketches.add(xyPlane)
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0), 15
    )
    extIn = extrudes.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extIn.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3))
    extrudes.add(extIn)

    # 2) 구멍 1개 (R=10 원 위에 첫 번째 구멍)
    planes = root.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(3))
    topPlane = planes.add(planeInput)

    holeSketch = sketches.add(topPlane)
    holeSketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(10, 0, 3), 2.0  # 중심에서 R=10 위치, 구멍 반지름 2
    )
    cutInput = extrudes.createInput(
        holeSketch.profiles.item(0),
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    cutInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
    holeFeat = extrudes.add(cutInput)

    # 3) Circular Pattern - Z축 기준 6개 360도 등간격
    circPatterns = root.features.circularPatternFeatures
    featCol = adsk.core.ObjectCollection.create()
    featCol.add(holeFeat)

    patInput = circPatterns.createInput(featCol, root.zConstructionAxis)
    patInput.quantity = adsk.core.ValueInput.createByReal(6)       # 개수
    patInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')  # 전체 각도
    patInput.isSymmetric = False
    circPatterns.add(patInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise