# 키워드: 원기둥, cylinder, 실린더
# 파라미터: radius, height

import adsk.core, adsk.fusion
design = app.activeProduct
rootComp = design.rootComponent
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
circles = sketch.sketchCurves.sketchCircles
circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 5.0)
prof = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(10.0))
extrudes.add(extInput)