# examples/assemblies/gusset_bracket.py
# 검증 완료: Fusion 360 2701.1.27
# 설명: L-bracket 양 끝에 얇은 삼각형 리브(gusset) 추가
# 핵심 패턴:
#   - 리브: body face + modelToSketchSpace + setOneSideExtent(NegativeExtentDirection)
#   - 두께: RIB=0.3 (T의 1/10)
#   - 방향: NegativeExtentDirection = 항상 body 안쪽

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "Gusset Bracket"')

sketches = root.sketches
extrudes = root.features.extrudeFeatures
xyPlane = root.xYConstructionPlane
planes = root.constructionPlanes
W=20; D=15; VH=15; T=3; G=10; RIB=0.3

# 1) 수평판: XY평면 W x D → +Z T
sk1 = sketches.add(xyPlane)
sk1.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(W,D,0))
ein1 = extrudes.createInput(sk1.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
ein1.setDistanceExtent(False, adsk.core.ValueInput.createByReal(T))
bodyH = extrudes.add(ein1).bodies.item(0)

# 2) 수직판: XY평면 W x T → +Z (T+VH)
sk2 = sketches.add(xyPlane)
sk2.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(W,T,0))
ein2 = extrudes.createInput(sk2.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
ein2.setDistanceExtent(False, adsk.core.ValueInput.createByReal(T+VH))
bodyV = extrudes.add(ein2).bodies.item(0)
tools = adsk.core.ObjectCollection.create()
tools.add(bodyV)
ci = root.features.combineFeatures.createInput(bodyH, tools)
ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
ci.isKeepToolBodies = False
body = root.features.combineFeatures.add(ci).bodies.item(0)

def add_rib(body, face_x, rib_thickness):
    """X=face_x 면에 삼각형 리브 추가
    NegativeExtentDirection = 항상 body 안쪽 방향 (X=0이면 +X, X=W이면 -X)
    """
    targetFace = None
    for face in body.faces:
        fbb = face.boundingBox
        if (abs(fbb.minPoint.x - face_x) < 0.01 and
                abs(fbb.maxPoint.x - face_x) < 0.01 and
                fbb.maxPoint.y - fbb.minPoint.y > D-1 and
                fbb.maxPoint.z - fbb.minPoint.z > VH-1):
            targetFace = face
            break
    if not targetFace:
        return body

    # 삼각형 꼭짓점: 내측 코너(Y=T,Z=T), 수평방향(Y=T+G,Z=T), 수직방향(Y=T,Z=T+G)
    sk = sketches.add(targetFace)
    sp1 = sk.modelToSketchSpace(adsk.core.Point3D.create(face_x, T,   T))
    sp2 = sk.modelToSketchSpace(adsk.core.Point3D.create(face_x, T+G, T))
    sp3 = sk.modelToSketchSpace(adsk.core.Point3D.create(face_x, T,   T+G))
    sk.sketchCurves.sketchLines.addByTwoPoints(sp1, sp2)
    sk.sketchCurves.sketchLines.addByTwoPoints(sp2, sp3)
    sk.sketchCurves.sketchLines.addByTwoPoints(sp3, sp1)

    # 가장 작은 프로파일 = 삼각형
    tri_prof = min(
        [sk.profiles.item(i) for i in range(sk.profiles.count)],
        key=lambda p: (
            (p.boundingBox.maxPoint.x - p.boundingBox.minPoint.x) *
            (p.boundingBox.maxPoint.y - p.boundingBox.minPoint.y)))

    ein = extrudes.createInput(tri_prof, adsk.fusion.FeatureOperations.JoinFeatureOperation)
    dd = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByReal(rib_thickness))
    ein.setOneSideExtent(dd, adsk.fusion.ExtentDirections.NegativeExtentDirection)
    return extrudes.add(ein).bodies.item(0)

# 3) 왼쪽 리브 (X=0 면 → +X 방향 RIB)
body = add_rib(body, 0, RIB)

# 4) 오른쪽 리브 (X=W 면 → -X 방향 RIB)
body = add_rib(body, W, RIB)

# 5) 수평판 구멍 2개 (Z방향, Y=T+G 뒤쪽)
pi1 = planes.createInput()
pi1.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(T))
skH = sketches.add(planes.add(pi1))
for px, py in [(4, 12), (16, 12)]:
    skH.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(px, py, T), 1.5)
pc1 = adsk.core.ObjectCollection.create()
for i in range(skH.profiles.count): pc1.add(skH.profiles.item(i))
cin1 = extrudes.createInput(pc1, adsk.fusion.FeatureOperations.CutFeatureOperation)
cin1.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
extrudes.add(cin1)

# 6) 수직판 구멍 2개 (Y방향, Y=0 앞면)
body = root.bRepBodies.item(0)
frontFace = None
for face in body.faces:
    fbb = face.boundingBox
    if (abs(fbb.minPoint.y) < 0.01 and abs(fbb.maxPoint.y) < 0.01
            and fbb.maxPoint.x - fbb.minPoint.x > W-1
            and fbb.maxPoint.z - fbb.minPoint.z > VH-1):
        frontFace = face
        break
skV = sketches.add(frontFace)
vZ = T + VH/2
for wx in [5, 15]:
    skV.sketchCurves.sketchCircles.addByCenterRadius(
        skV.modelToSketchSpace(adsk.core.Point3D.create(wx, 0, vZ)), 1.5)
pc2 = adsk.core.ObjectCollection.create()
for i in range(skV.profiles.count):
    p = skV.profiles.item(i)
    pbb = p.boundingBox
    if (pbb.maxPoint.x-pbb.minPoint.x)*(pbb.maxPoint.y-pbb.minPoint.y) < 20:
        pc2.add(p)
cin2 = extrudes.createInput(pc2, adsk.fusion.FeatureOperations.CutFeatureOperation)
cin2.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
extrudes.add(cin2)

app.executeTextCommand('PTransaction.Commit')