import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Box with Fillet"')
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

    # 2) 수직 엣지 4개 선택 (Z방향 엣지)
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        sv = edge.startVertex.geometry
        ev = edge.endVertex.geometry
        if abs(ev.z - sv.z) > 4.9 and abs(ev.x - sv.x) < 0.01 and abs(ev.y - sv.y) < 0.01:
            edges.add(edge)

    # 3) Fillet R=1 적용
    filletInput = root.features.filletFeatures.createInput()
    filletInput.addConstantRadiusEdgeSet(
        edges,
        adsk.core.ValueInput.createByReal(1.0),
        True
    )
    root.features.filletFeatures.add(filletInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise