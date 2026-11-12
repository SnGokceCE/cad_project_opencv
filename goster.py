#Bu kendi oluşturduğum beş tane feature içeren parçayı gösteriyor. 

from pathlib import Path

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Display.SimpleGui import init_display

STEP_PATH = Path(r"D:\cadproj\data\test_parca.step")

def step_oku(path: Path):
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"STEP okunamadi: {path}")
    reader.TransferRoots()
    return reader.OneShape()


shape = step_oku(STEP_PATH)

display, start_display, add_menu, add_function_to_menu = init_display()
display.DisplayShape(shape, update=True)
display.FitAll()
start_display()