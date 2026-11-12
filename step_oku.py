from pathlib import Path

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.TopoDS import topods

STEP_PATH = Path(r"D:\cadproj\data\00000050_80d90bfdd2e74e709956122a_step_000.step")


def step_oku(path: Path):
    """STEP dosyasini okur ve tek bir shape dondurur."""
    reader = STEPControl_Reader()
    status = reader.ReadFile(str(path))

    if status != IFSelect_RetDone:
        raise RuntimeError(f"STEP okunamadi: {path}")

    reader.TransferRoots()
    return reader.OneShape()


def sinir_kutusu(shape):
    """Parcanin sinirlayici kutusunu (xmin, ymin, zmin, xmax, ymax, zmax) dondurur."""
    box = Bnd_Box()
    brepbndlib.Add(shape, box)
    return box.Get()


def say(shape, tip):
    """Verilen topoloji tipinden kac tane oldugunu sayar."""
    exp = TopExp_Explorer(shape, tip)
    n = 0
    while exp.More():
        n += 1
        exp.Next()
    return n


def ucgen_say(shape):
    """Mesh'lenmis shape uzerindeki toplam ucgen ve dugum sayisini dondurur."""
    toplam_ucgen = 0
    toplam_dugum = 0

    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = topods.Face(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation(face, loc)

        if tri is not None:
            toplam_ucgen += tri.NbTriangles()
            toplam_dugum += tri.NbNodes()

        exp.Next()

    return toplam_ucgen, toplam_dugum


# --- ana akis ---

print(f"Dosya: {STEP_PATH.name}")
shape = step_oku(STEP_PATH)

xmin, ymin, zmin, xmax, ymax, zmax = sinir_kutusu(shape)
boyut = (xmax - xmin, ymax - ymin, zmax - zmin)
kosegen = (boyut[0] ** 2 + boyut[1] ** 2 + boyut[2] ** 2) ** 0.5

print(f"Kati (solid) sayisi : {say(shape, TopAbs_SOLID)}")
print(f"Yuzey (face) sayisi : {say(shape, TopAbs_FACE)}")
print(f"Sinir kutusu boyutu : {boyut[0]:.2f} x {boyut[1]:.2f} x {boyut[2]:.2f}")
print(f"Kosegen uzunlugu    : {kosegen:.2f}")

# Mesh hassasiyetini parcanin boyutuna gore olcekle
sapma = kosegen * 0.001
print(f"Mesh sapma toleransi: {sapma:.4f}")

BRepMesh_IncrementalMesh(shape, sapma, False, 0.5, True)

ucgen, dugum = ucgen_say(shape)
print(f"Ucgen sayisi        : {ucgen}")
print(f"Dugum sayisi        : {dugum}")