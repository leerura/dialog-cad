# examples/primitives/rectangular_pattern.py
# 검증 완료: Fusion 360 2701.1.27
# 설명: 30x20 플레이트에 구멍 3x2 격자 배열 (완전 대칭)
# 핵심 패턴: 시작 위치 자동 계산으로 대칭 보장 + ObjectCollection 한번에 Cut

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Rectangular Pattern"')
try:
    sketches = root.sketches
    extrudes = root.features.extrudeFeatures
    xyPlane = root.xYConstructionPlane

    plateW, plateH, plateZ = 30, 20, 2   # 플레이트 크기
    cols, rows, spacing, radius = 3, 2, 10, 1.5  # 격자 설정

    # 1) 플레이트
    sk = sketches.add(xyPlane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(plateW, plateH, 0)
    )
    extIn = extrudes.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extIn.setDistanceExtent(False, adsk.core.ValueInput.createByReal(plateZ))
    extrudes.add(extIn)

    # 2) 대칭 시작 위치 자동 계산
    # startX = (전체폭 - 전체스팬) / 2 → 좌우 여백 동일 보장
    startX = (plateW - (cols-1)*spacing) / 2
    startY = (plateH - (rows-1)*spacing) / 2

    planes = root.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(plateZ))
    topPlane = planes.add(planeInput)

    # 3) 한 스케치에 모든 원 한번에
    holeSketch = sketches.add(topPlane)
    for r in range(rows):
        for c in range(cols):
            holeSketch.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(startX + c*spacing, startY + r*spacing, plateZ),
                radius
            )

    # 4) ObjectCollection으로 한번에 Cut
    profileCol = adsk.core.ObjectCollection.create()
    for i in range(holeSketch.profiles.count):
        profileCol.add(holeSketch.profiles.item(i))

    cutInput = extrudes.createInput(profileCol, adsk.fusion.FeatureOperations.CutFeatureOperation)
    cutInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
    extrudes.add(cutInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise