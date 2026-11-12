#Beş feature içeren bir parçayı oluşturup STEP dosyası olarak kaydeden örnek.

from pathlib import Path

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Ax2, gp_Dir
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.IFSelect import IFSelect_RetDone

CIKTI = Path(r"D:\cadproj\data\test_parca.step")

# Blok olculeri (mm)
BLOK_X, BLOK_Y, BLOK_Z = 120.0, 80.0, 20.0
UST = BLOK_Z          # ust yuzey z = 20
TASMA = 1.0           # kesici aletin ust yuzeyden tasma payi


def kutu(x, y, z, dx, dy, dz):
    return BRepPrimAPI_MakeBox(gp_Pnt(x, y, z), dx, dy, dz).Shape()


def silindir(cx, cy, z_alt, r, h):
    """Z ekseni boyunca yukari uzanan silindir."""
    eksen = gp_Ax2(gp_Pnt(cx, cy, z_alt), gp_Dir(0, 0, 1))
    return BRepPrimAPI_MakeCylinder(eksen, r, h).Shape()


def slot_kesici(x1, y1, x2, y2, genislik, z_alt, h):
    """
    (x1,y1)-(x2,y2) dogrusu boyunca uzanan, uclari yuvarlatilmis kesici.
    Sadece eksene paralel slotlar icin (yatay veya dikey).
    """
    r = genislik / 2.0
    parcalar = [
        silindir(x1, y1, z_alt, r, h),
        silindir(x2, y2, z_alt, r, h),
    ]

    if abs(y2 - y1) < 1e-9:                     # yatay slot
        xs, xb = min(x1, x2), max(x1, x2)
        govde = kutu(xs, y1 - r, z_alt, xb - xs, genislik, h)
    else:                                        # dikey slot
        ys, yb = min(y1, y2), max(y1, y2)
        govde = kutu(x1 - r, ys, z_alt, genislik, yb - ys, h)

    sonuc = govde
    for p in parcalar:
        sonuc = BRepAlgoAPI_Fuse(sonuc, p).Shape()
    return sonuc


def cikar(hedef, kesici):
    return BRepAlgoAPI_Cut(hedef, kesici).Shape()


# --- parcayi kur ---

parca = kutu(0, 0, 0, BLOK_X, BLOK_Y, BLOK_Z)

# 1) Gecme delik  (through hole) - r=8, blogu bastan basa deler
parca = cikar(parca, silindir(25, 20, -TASMA, 8.0, BLOK_Z + 2 * TASMA))

# 2) Kor delik    (blind hole)   - r=6, derinlik 8
parca = cikar(parca, silindir(25, 58, UST - 8.0, 6.0, 8.0 + TASMA))

# 3) Dikdortgen cep (pocket)     - 40x24, derinlik 7
parca = cikar(parca, kutu(52, 46, UST - 7.0, 40.0, 24.0, 7.0 + TASMA))

# 4) Kapali slot  (closed slot)  - uzunluk 35, genislik 12, derinlik 6
parca = cikar(parca, slot_kesici(58, 20, 93, 20, 12.0, UST - 6.0, 6.0 + TASMA))

# 5) Acik slot    (open slot)    - kenardan disari cikar
parca = cikar(parca, kutu(104, 8, UST - 6.0, BLOK_X - 104 + TASMA, 14.0, 6.0 + TASMA))


# --- kaydet ---

writer = STEPControl_Writer()
writer.Transfer(parca, STEPControl_AsIs)
if writer.Write(str(CIKTI)) != IFSelect_RetDone:
    raise RuntimeError("STEP yazilamadi")

print(f"Kaydedildi: {CIKTI}")
print(f"Blok: {BLOK_X} x {BLOK_Y} x {BLOK_Z}")
print()
print("Beklenen feature'lar (ust yuzeyden, +Z yonunden bakildiginda):")
print("  1. Gecme delik : merkez (25, 20),  cap 16,  bastan basa")
print("  2. Kor delik   : merkez (25, 58),  cap 12,  derinlik 8")
print("  3. Cep         : (52,46)-(92,70),  40x24,   derinlik 7")
print("  4. Kapali slot : (58,20)-(93,20),  genislik 12, derinlik 6")
print("  5. Acik slot   : x=104'ten kenara, genislik 14, derinlik 6")