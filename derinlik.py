#Derinlik haritası oluşturmak için STEP dosyasını okuyup, en büyük solidi seçip, mesh çıkarıp,
#derinlik haritasını oluşturuyor ve kaydediyor.

from pathlib import Path

import numpy as np

from mesh_cikar import step_oku, en_buyuk_solid, mesh_cikar
from raster import derinlik_haritasi

STEP_PATH = Path(r"D:\cadproj\data\test_parca.step")

shape = step_oku(STEP_PATH)
solid = en_buyuk_solid(shape)
v, f = mesh_cikar(solid, sapma_orani=0.0001)

print(f"Kose : {len(v)}")
print(f"Ucgen: {len(f)}")
print(f"Sinir: {v.min(axis=0).round(2)} .. {v.max(axis=0).round(2)}")
print()

# +Z ustten bakis (eksenin arti tarafindan asagi)
d, mmpx, kapsam = derinlik_haritasi(v, f, eksen=2, pozitif=False, cozunurluk=512)

gecerli = np.isfinite(d)
print(f"Harita boyutu   : {d.shape}")
print(f"mm / piksel     : {mmpx:.4f}")
print(f"Dolu piksel     : {gecerli.sum()} / {d.size}")
print(f"Derinlik araligi: {d[gecerli].min():.2f} .. {d[gecerli].max():.2f}")

import os
import cv2

os.makedirs(r"D:\cadproj\out", exist_ok=True)

# Bos pikselleri en derin degerin de otesine at ki ayrissin
en_derin = d[gecerli].max()
gorunur = np.where(gecerli, d, en_derin + 2.0)

# 0-255 araligina olcekle
norm = cv2.normalize(gorunur, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# Ters cevir: yuzeye yakin = acik, derin = koyu
norm = 255 - norm

cv2.imwrite(r"D:\cadproj\out\derinlik_gri.png", norm)

# Renkli versiyon - seviyeleri ayirt etmek daha kolay
renkli = cv2.applyColorMap(norm, cv2.COLORMAP_VIRIDIS)
cv2.imwrite(r"D:\cadproj\out\derinlik_renkli.png", renkli)

print("Kaydedildi: out/derinlik_gri.png")
print("Kaydedildi: out/derinlik_renkli.png")

# --- derinlik haritasini ham haliyle kaydet ---
np.savez(
    r"D:\cadproj\out\derinlik_z.npz",
    derinlik=d,
    mm_per_px=mmpx,
    kapsam=np.array(kapsam),
    eksen=2,
    pozitif=False,
)
print("Kaydedildi: out/derinlik_z.npz")