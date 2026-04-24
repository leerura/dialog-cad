# examples/primitives/mirror.py
# 검증 완료: Fusion 360 2701.1.27
# 설명: L자 형상을 YZ 평면 기준으로 미러
# 핵심 패턴: mirrorFeatures.createInput(featCol, 평면) → isCombine으로 합칠지 결정

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Mirror"')
try:
    sketches = root.sketches
    extrudes = root.features.extrudeFeatures
    xyPlane = root.xYConstructionPlane

    # 1) L자 형상 (YZ 평면 오른쪽)
    sk = sketches.add(xyPlane)
    lines = sk.sketchCurves.sketchLines
    pts = [
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(8, 0, 0),
        adsk.core.Point3D.create(8, 3, 0),
        adsk.core.Point3D.create(3, 3, 0),
        adsk.core.Point3D.create(3, 8, 0),
        adsk.core.Point3D.create(0, 8, 0),
    ]
    for i in range(len(pts)-1):
        lines.addByTwoPoints(pts[i], pts[i+1])
    lines.addByTwoPoints(pts[-1], pts[0])

    extIn = extrudes.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extIn.setDistanceExtent(False, adsk.core.ValueInput.createByReal(3))
    featA = extrudes.add(extIn)

    # 2) Mirror - YZ 평면 기준 (X축 대칭)
    # isCombine=True → 하나로 합치기, False → 별도 body 유지
    mirrorFeats = root.features.mirrorFeatures
    featCol = adsk.core.ObjectCollection.create()
    featCol.add(featA)

    mirrorInput = mirrorFeats.createInput(featCol, root.yZConstructionPlane)
    mirrorInput.isCombine = False
    mirrorFeats.add(mirrorInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise