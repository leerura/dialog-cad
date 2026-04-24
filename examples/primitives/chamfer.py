# 검증 완료: Fusion 360 2701.1.27
# 설명: 박스 윗면 엣지 4개에 Chamfer (모따기) 적용
# 핵심 패턴: boundingBox Z값으로 수평 엣지 선택 → chamferFeatures.setToEqualDistance

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Chamfer"')
try:
    sketches = root.sketches
    extrudes = root.features.extrudeFeatures
    xyPlane = root.xYConstructionPlane

    # 1) 박스 (10x10x5)
    sk = sketches.add(xyPlane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(10, 10, 0)
    )
    extIn = extrudes.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extIn.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5))
    extrudes.add(extIn)
    body = root.bRepBodies.item(0)

    # 2) 윗면 수평 엣지 4개 선택 (Z=5인 엣지)
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        sv = edge.startVertex.geometry
        ev = edge.endVertex.geometry
        if abs(sv.z - 5) < 0.01 and abs(ev.z - 5) < 0.01:
            edges.add(edge)

    # 3) Chamfer 0.5cm 적용
    chamferFeats = root.features.chamferFeatures
    chamferInput = chamferFeats.createInput(edges, True)
    chamferInput.setToEqualDistance(adsk.core.ValueInput.createByReal(0.5))
    chamferFeats.add(chamferInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise