# 검증 완료: Fusion 360 2701.1.27
# 설명: 박스에서 윗면을 열고 두께 1cm Shell (속 비우기)
# 핵심 패턴: boundingBox로 면 찾기 → shellFeatures.createInput(faceCol)

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Shell"')
try:
    sketches = root.sketches
    extrudes = root.features.extrudeFeatures
    xyPlane = root.xYConstructionPlane

    # 1) 박스 (10x10x10)
    sk = sketches.add(xyPlane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(10, 10, 0)
    )
    extIn = extrudes.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extIn.setDistanceExtent(False, adsk.core.ValueInput.createByReal(10))
    extrudes.add(extIn)
    body = root.bRepBodies.item(0)

    # 2) 윗면 찾기 (Z=10인 면)
    topFace = None
    for face in body.faces:
        bb = face.boundingBox
        if abs(bb.minPoint.z - 10) < 0.01 and abs(bb.maxPoint.z - 10) < 0.01:
            topFace = face
            break

    # 3) Shell - 윗면 열고 두께 1cm
    faceCol = adsk.core.ObjectCollection.create()
    faceCol.add(topFace)
    shellFeats = root.features.shellFeatures
    shellInput = shellFeats.createInput(faceCol, False)
    shellInput.insideThickness = adsk.core.ValueInput.createByReal(1.0)
    shellFeats.add(shellInput)

    app.executeTextCommand('PTransaction.Commit')
except Exception as e:
    app.executeTextCommand('PTransaction.Cancel')
    raise