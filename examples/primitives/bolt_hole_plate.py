# examples/bolt_hole_plate.py
# 검증 완료: Fusion 360 2701.1.27
# 설명: 20x10 플레이트에 네 모서리 볼트 홀 4개 뚫기
# 핵심 패턴: 다중 구멍은 한 스케치에 모두 그리고 ObjectCollection으로 한번에 Cut

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Bolt Hole Plate"')
try:
    sketches = root.sketches
    extrudes = root.features.extrudeFeatures
    xyPlane = root.xYConstructionPlane

    # 1) 플레이트 스케치 + Extrude (20x10x3)
    plateSketch = sketches.add(xyPlane)
    plateSketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(20, 10, 0)
    )
    extInput = extrudes.createInput(
        plateSketch.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3))
    extrudes.add(extInput)

    # 2) 윗면 오프셋 평면 (Z=3)
    planes = root.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(3))
    topPlane = planes.add(planeInput)

    # 3) 구멍 스케치 - 한 스케치에 4개 원 한번에 그리기
    holeSketch = sketches.add(topPlane)
    circles = holeSketch.sketchCurves.sketchCircles
    holePositions = [
        (2, 2, 3),   # 좌하단
        (18, 2, 3),  # 우하단
        (2, 8, 3),   # 좌상단
        (18, 8, 3),  # 우상단
    ]
    for x, y, z in holePositions:
        circles.addByCenterRadius(adsk.core.Point3D.create(x, y, z), 1.0)

    # 4) ObjectCollection으로 4개 프로파일 한번에 CutFeatureOperation
    # ❌ 구멍마다 별도 Extrude Cut 반복 금지 → body가 복제됨
    # ✅ 한번에 ObjectCollection으로 처리
    profileCollection = adsk.core.ObjectCollection.create()
    for i in range(holeSketch.profiles.count):
        profileCollection.add(holeSketch.profiles.item(i))

    cutInput = extrudes.createInput(
        profileCollection,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    cutInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
    extrudes.add(cutInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise