#Bu step dosyasından aldığım üç tane parçadan oluşan şeklin renklendirilmiş halini gösteriyor.

from pathlib import Path

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID
from OCC.Core.TopoDS import topods
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Display.SimpleGui import init_display

STEP_PATH = Path(r"D:\cadproj\data\00000050_80d90bfdd2e74e709956122a_step_000.step")

reader = STEPControl_Reader()
if reader.ReadFile(str(STEP_PATH)) != IFSelect_RetDone:
    raise RuntimeError("STEP okunamadi")
reader.TransferRoots()
shape = reader.OneShape()

solidler = []
exp = TopExp_Explorer(shape, TopAbs_SOLID)
while exp.More():
    solidler.append(topods.Solid(exp.Current()))
    exp.Next()

renkler = [(1.0, 0.3, 0.3), (0.3, 1.0, 0.3), (0.3, 0.3, 1.0)]

display, start_display, _, _ = init_display()

for i, solid in enumerate(solidler):
    r, g, b = renkler[i % 3]
    display.DisplayShape(
        solid,
        color=Quantity_Color(r, g, b, Quantity_TOC_RGB),
        transparency=0.6,          # ic ice girenleri gorebilmek icin
        update=False,
    )

display.FitAll()
display.Repaint()
start_display()