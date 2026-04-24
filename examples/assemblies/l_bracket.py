# examples/assemblies/l_bracket.py
# 검증 완료: Fusion 360 2701.1.27
# 설명: L자 브라켓 - 수평판(20x15x3) + 수직판(20x3x15), 각 면에 볼트홀 2개
# 핵심 패턴:
#   - feature.bodies.item(0)으로 body 직접 추적 (잔여 body 영향 없음)
#   - 수직판 구멍: Y=0 frontFace + modelToSketchSpace + NegativeExtentDirection
#   - 원 프로파일만 면적 필터링으로 선택 (area < 20)

import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

app.executeTextCommand('PTransaction.Start "L-Bracket"')

sketches = root.sketches
extrudes = root.features.extrudeFeatures
xyPlane = root.xYConstructionPlane
planes = root.constructionPlanes
W=20; D=15; VH=15; T=3

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

# 3) Boolean Join
tools = adsk.core.ObjectCollection.create()
tools.add(bodyV)
ci = root.features.combineFeatures.createInput(bodyH, tools)
ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
ci.isKeepToolBodies = False
body = root.features.combineFeatures.add(ci).bodies.item(0)

# 4) 수평판 구멍 2개: Z=T 윗면 → -Z 관통
pi1 = planes.createInput()
pi1.setByOffset(xyPlane, adsk.core.ValueInput.createByReal(T))
skH = sketches.add(planes.add(pi1))
for px, py in [(4, 9), (16, 9)]:
    skH.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(px, py, T), 1.5)
pc1 = adsk.core.ObjectCollection.create()
for i in range(skH.profiles.count): pc1.add(skH.profiles.item(i))
cin1 = extrudes.createInput(pc1, adsk.fusion.FeatureOperations.CutFeatureOperation)
cin1.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
extrudes.add(cin1)

# 5) 수직판 구멍 2개: Y=0 앞면 → +Y 관통
# frontFace: Y=0, X 전체 폭, Z=VH 이상인 면
frontFace = None
for face in body.faces:
    fbb = face.boundingBox
    if (abs(fbb.minPoint.y) < 0.01 and abs(fbb.maxPoint.y) < 0.01
            and fbb.maxPoint.x - fbb.minPoint.x > W-1
            and fbb.maxPoint.z - fbb.minPoint.z > VH-1):
        frontFace = face
        break

skV = sketches.add(frontFace)
vZ = T + VH / 2  # 수직판 높이 중앙
for wx in [5, 15]:
    # modelToSketchSpace로 세계 좌표 → 스케치 좌표 변환
    skV.sketchCurves.sketchCircles.addByCenterRadius(
        skV.modelToSketchSpace(adsk.core.Point3D.create(wx, 0, vZ)), 1.5)

# 원 프로파일만 선택 (면적 < 20, 큰 면 영역 제외)
pc2 = adsk.core.ObjectCollection.create()
for i in range(skV.profiles.count):
    prof = skV.profiles.item(i)
    pbb = prof.boundingBox
    if (pbb.maxPoint.x-pbb.minPoint.x)*(pbb.maxPoint.y-pbb.minPoint.y) < 20:
        pc2.add(prof)

cin2 = extrudes.createInput(pc2, adsk.fusion.FeatureOperations.CutFeatureOperation)
cin2.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
extrudes.add(cin2)

app.executeTextCommand('PTransaction.Commit')