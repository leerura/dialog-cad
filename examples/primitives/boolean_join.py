import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Boolean Join"')
try:
    sketches = root.sketches
    extrudes = root.features.extrudeFeatures
    xyPlane = root.xYConstructionPlane

    # 1) 박스 (10x10x5)
    skA = sketches.add(xyPlane)
    skA.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(10, 10, 0)
    )
    inA = extrudes.createInput(skA.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inA.setDistanceExtent(False, adsk.core.ValueInput.createByReal(5))
    extrudes.add(inA)
    bodyA = root.bRepBodies.item(0)

    # 2) 원기둥 (반지름 3, 높이 8) - 박스 중앙 위에
    skB = sketches.add(xyPlane)
    skB.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(5, 5, 0), 3.0
    )
    inB = extrudes.createInput(skB.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    inB.setDistanceExtent(False, adsk.core.ValueInput.createByReal(8))
    extrudes.add(inB)
    bodyB = root.bRepBodies.item(1)

    # 3) Boolean Join: bodyA + bodyB → 1개로 합치기
    tools = adsk.core.ObjectCollection.create()
    tools.add(bodyB)
    combineInput = root.features.combineFeatures.createInput(bodyA, tools)
    combineInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
    combineInput.isKeepToolBodies = False
    root.features.combineFeatures.add(combineInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise