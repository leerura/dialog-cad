# 키워드: 구, sphere, 공
# 파라미터: radius
# 핵심: revolve 축은 ConstructionAxis 아니라 스케치 선 사용

import adsk.core, adsk.fusion
design = app.activeProduct
rootComp = design.rootComponent
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)

center = adsk.core.Point3D.create(0, 0, 0)
radius = 5.0

line1 = sketch.sketchCurves.sketchLines.addByTwoPoints(
    center, adsk.core.Point3D.create(radius, 0, 0)
)
arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(
    center, adsk.core.Point3D.create(radius, 0, 0), 180
)
line2 = sketch.sketchCurves.sketchLines.addByTwoPoints(
    center, adsk.core.Point3D.create(-radius, 0, 0)
)

prof = sketch.profiles.item(0)
revolves = rootComp.features.revolveFeatures
revInput = revolves.createInput(prof, line1, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
revInput.setAngleExtent(False, adsk.core.ValueInput.createByReal(360))
revolves.add(revInput)