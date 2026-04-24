# 키워드: 박스, box, 직육면체, 정육면체
# 파라미터: width, height, depth

import adsk.core, adsk.fusion
design = app.activeProduct
rootComp = design.rootComponent
sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
lines = sketch.sketchCurves.sketchLines
lines.addTwoPointRectangle(
    adsk.core.Point3D.create(0, 0, 0),
    adsk.core.Point3D.create(10, 10, 0)
)
prof = sketch.profiles.item(0)
extrudes = rootComp.features.extrudeFeatures
extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(10.0))
extrudes.add(extInput)