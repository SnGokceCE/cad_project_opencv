from pathlib import Path

import numpy as np

from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID
from OCC.Core.TopoDS import topods

GIRDI = Path(r"D:\cadproj\data\00000050_80d90bfdd2e74e709956122a_step_000.step")
CIKTI = Path(r"D:\cadproj\data\parca_temiz.step")


def step_oku(path: Path):
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"STEP okunamadi: {path}")
    reader.TransferRoots()
    return reader.OneShape()


def kutu_hacmi(shape) -> float:
    box = Bnd_Box()
    brepbndlib.Add(shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return (xmax - xmin) * (ymax - ymin) * (zmax - zmin)


def solidleri_ayir(shape):
    solidler = []
    exp = TopExp_Explorer(shape, TopAbs_SOLID)
    while exp.More():
        solidler.append(topods.Solid(exp.Current()))
        exp.Next()
    return solidler


def step_yaz(shape, path: Path):
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    if writer.Write(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"STEP yazilamadi: {path}")


# --- ana akis ---

shape = step_oku(GIRDI)
solidler = solidleri_ayir(shape)
print(f"{len(solidler)} solid bulundu.")

if not solidler:
    raise RuntimeError("Dosyada solid yok")

secilen = max(solidler, key=kutu_hacmi)

box = Bnd_Box()
brepbndlib.Add(secilen, box)
xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
print(f"Secilen solid boyutu: {xmax-xmin:.2f} x {ymax-ymin:.2f} x {zmax-zmin:.2f}")

step_yaz(secilen, CIKTI)
print(f"Kaydedildi: {CIKTI}")