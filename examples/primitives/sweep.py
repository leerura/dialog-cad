# 검증 완료: Fusion 360 2701.1.27
# 설명: L자 경로를 따라 원형 단면을 Sweep하는 예시
# 핵심 패턴: createPath(lines, True) → setByDistanceOnPath → sweepFeatures

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Sweep"')
try:
    sketches = root.sketches
    xzPlane = root.xZConstructionPlane

    # 1) 경로 스케치 (XZ 평면에 L자 경로)
    pathSketch = sketches.add(xzPlane)
    lines = pathSketch.sketchCurves.sketchLines
    l1 = lines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(10, 0, 0))
    l2 = lines.addByTwoPoints(adsk.core.Point3D.create(10, 0, 0), adsk.core.Point3D.create(10, 0, 8))

    # 2) 경로 체인 생성
    pathLines = adsk.core.ObjectCollection.create()
    pathLines.add(l1)
    pathLines.add(l2)
    sweepPath = root.features.createPath(pathLines, True)

    # 3) 단면 스케치 (경로 시작점에 수직 평면)
    planes = root.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByDistanceOnPath(sweepPath, adsk.core.ValueInput.createByReal(0))
    profilePlane = planes.add(planeInput)

    profileSketch = sketches.add(profilePlane)
    profileSketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0), 1.5  # 반지름
    )

    # 4) Sweep
    sweepFeats = root.features.sweepFeatures
    sweepInput = sweepFeats.createInput(
        profileSketch.profiles.item(0),
        sweepPath,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    sweepInput.orientation = adsk.fusion.SweepOrientationTypes.ParallelOrientationType
    sweepFeats.add(sweepInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise