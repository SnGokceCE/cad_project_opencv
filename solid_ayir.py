from pathlib import Path

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID
from OCC.Core.TopoDS import topods
from OCC.Core.StlAPI import StlAPI_Writer

STEP_PATH = Path(r"D:\cadproj\data\00000050_80d90bfdd2e74e709956122a_step_000.step")
CIKTI_DIR = Path(r"D:\cadproj\out")


def step_oku(path: Path):
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"STEP okunamadi: {path}")
    reader.TransferRoots()
    return reader.OneShape()


def solidleri_ayir(shape):
    """Shape icindeki tum solidleri liste olarak dondurur."""
    solidler = []
    exp = TopExp_Explorer(shape, TopAbs_SOLID)
    while exp.More():
        solidler.append(topods.Solid(exp.Current()))
        exp.Next()
    return solidler


def olcu(shape):
    """(boyut, hacim_tahmini, yuzey_sayisi) dondurur."""
    box = Bnd_Box()
    brepbndlib.Add(shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    boyut = (xmax - xmin, ymax - ymin, zmax - zmin)

    n_face = 0
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        n_face += 1
        exp.Next()

    return boyut, boyut[0] * boyut[1] * boyut[2], n_face


def stl_yaz(shape, path: Path, sapma: float):
    """Shape'i mesh'leyip STL olarak kaydeder."""
    BRepMesh_IncrementalMesh(shape, sapma, False, 0.5, True)
    writer = StlAPI_Writer()
    writer.SetASCIIMode(False)          # binary STL, daha kucuk dosya
    writer.Write(shape, str(path))


# --- ana akis ---

CIKTI_DIR.mkdir(parents=True, exist_ok=True)

shape = step_oku(STEP_PATH)
solidler = solidleri_ayir(shape)
print(f"Toplam {len(solidler)} solid bulundu.\n")

# Kutu hacmine gore buyukten kucuge sirala
sirali = sorted(solidler, key=lambda s: olcu(s)[1], reverse=True)

for i, solid in enumerate(sirali):
    boyut, hacim, n_face = olcu(solid)
    kosegen = sum(b ** 2 for b in boyut) ** 0.5
    sapma = kosegen * 0.0005

    ad = f"solid_{i}.stl"
    stl_yaz(solid, CIKTI_DIR / ad, sapma)

    print(f"[{i}] {ad}")
    print(f"    boyut  : {boyut[0]:.2f} x {boyut[1]:.2f} x {boyut[2]:.2f}")
    print(f"    kutu hacmi: {hacim:.1f}")
    print(f"    yuzey  : {n_face}")
    print()

print(f"STL dosyalari: {CIKTI_DIR}")