from pathlib import Path

import numpy as np

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_REVERSED
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location


def step_oku(path: Path):
    """STEP dosyasini okuyup tek shape dondurur."""
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"STEP okunamadi: {path}")
    reader.TransferRoots()
    return reader.OneShape()


def solidleri_ayir(shape):
    """Shape icindeki solidleri liste olarak dondurur."""
    solidler = []
    exp = TopExp_Explorer(shape, TopAbs_SOLID)
    while exp.More():
        solidler.append(topods.Solid(exp.Current()))
        exp.Next()
    return solidler


def kutu_olcu(shape):
    """(boyut, kosegen) dondurur."""
    box = Bnd_Box()
    brepbndlib.Add(shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    boyut = np.array([xmax - xmin, ymax - ymin, zmax - zmin])
    return boyut, float(np.linalg.norm(boyut))


def en_buyuk_solid(shape):
    """Kutu hacmi en buyuk solidi dondurur. Solid yoksa shape'in kendisi."""
    solidler = solidleri_ayir(shape)
    if not solidler:
        return shape
    return max(solidler, key=lambda s: np.prod(kutu_olcu(s)[0]))


def mesh_cikar(shape, sapma_orani=0.0005, aci=0.5):
    """
    Shape'i mesh'leyip (vertices, faces) numpy dizileri olarak dondurur.

    vertices : (N, 3) float64  -> kose noktalarinin XYZ koordinatlari
    faces    : (M, 3) int32    -> her ucgenin 3 kose indeksi
    """
    _, kosegen = kutu_olcu(shape)
    sapma = kosegen * sapma_orani

    # Mesh'i shape'in icine yazar
    BRepMesh_IncrementalMesh(shape, sapma, False, aci, True)

    tum_vert = []
    tum_face = []
    ofset = 0  # her yuzeyin dugumleri global listede kayar

    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = topods.Face(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation(face, loc)

        if tri is None:
            exp.Next()
            continue

        trsf = loc.Transformation()
        ters = face.Orientation() == TopAbs_REVERSED

        # --- dugumler ---
        n_node = tri.NbNodes()
        v = np.empty((n_node, 3), dtype=np.float64)
        for i in range(1, n_node + 1):          # OCC 1-tabanli indeksler
            p = tri.Node(i).Transformed(trsf)   # yuzeyin konumunu uygula
            v[i - 1] = (p.X(), p.Y(), p.Z())
        tum_vert.append(v)

        # --- ucgenler ---
        n_tri = tri.NbTriangles()
        f = np.empty((n_tri, 3), dtype=np.int64)
        for i in range(1, n_tri + 1):
            a, b, c = tri.Triangle(i).Get()
            if ters:
                a, c = c, a                      # sarim yonunu duzelt
            f[i - 1] = (a - 1 + ofset, b - 1 + ofset, c - 1 + ofset)
        tum_face.append(f)

        ofset += n_node
        exp.Next()

    if not tum_vert:
        raise RuntimeError("Mesh uretilemedi - shape bos olabilir")

    vertices = np.vstack(tum_vert)
    faces = np.vstack(tum_face).astype(np.int32)
    return vertices, faces


# --- test ---
if __name__ == "__main__":
    STEP_PATH = Path(r"D:\cadproj\data\00000050_80d90bfdd2e74e709956122a_step_000.step")

    shape = step_oku(STEP_PATH)
    solid = en_buyuk_solid(shape)

    boyut, kosegen = kutu_olcu(solid)
    print(f"Secilen solid boyutu: {boyut[0]:.2f} x {boyut[1]:.2f} x {boyut[2]:.2f}")
    print(f"Kosegen: {kosegen:.2f}")

    v, f = mesh_cikar(solid)
    print(f"Kose sayisi : {len(v)}")
    print(f"Ucgen sayisi: {len(f)}")
    print(f"Kose aralik : {v.min(axis=0).round(2)} .. {v.max(axis=0).round(2)}")

    # trimesh ile dogrulama
    import trimesh
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    print(f"trimesh watertight mi: {m.is_watertight}")
    print(f"trimesh hacim: {m.volume:.2f}")