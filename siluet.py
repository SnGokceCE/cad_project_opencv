#Siluetleri oluşturmak için yapılan dosya.

import numpy as np
import cv2

# --- 1. Derinlik haritasini oku ---
veri = np.load(r"D:\cadproj\out\derinlik_z.npz")
d = veri["derinlik"]
mmpx = float(veri["mm_per_px"])

dolu = np.isfinite(d)          # isin carpmis pikseller
H, W = d.shape

# --- 2. Bosluk maskesi ---
# Isinin carpmadigi her yer: parcanin disi + gecme deliklerin ici
bosluk = np.zeros((H, W), dtype=np.uint8)
bosluk[~dolu] = 255

print(f"Toplam bosluk pikseli: {(bosluk == 255).sum()}")

# --- 3. Flood fill: disaridan iceri dogru yayil ---
# floodFill'in istedigi maske, goruntuden 2 piksel buyuk olmali
ff_maske = np.zeros((H + 2, W + 2), dtype=np.uint8)

# Kopyasi uzerinde calisalim, orijinali bozmayalim
disari = bosluk.copy()

# (0,0) noktasindan basla - orasi kesinlikle parcanin disi
cv2.floodFill(disari, ff_maske, (0, 0), 128)

# Artik 128 olan her yer "disariya bagli bosluk" = arka plan
arka_plan = (disari == 128)

# 255 kalanlar ise "disariya ulasilamayan bosluk" = gecme delik
gecme_delik = (disari == 255)

print(f"Arka plan pikseli    : {arka_plan.sum()}")
print(f"Gecme delik pikseli  : {gecme_delik.sum()}")

# --- 4. Siluet ---
# Parcanin kapladigi alan = arka plan olmayan her yer
siluet = np.zeros((H, W), dtype=np.uint8)
siluet[~arka_plan] = 255

print(f"Siluet alani         : {(siluet == 255).sum()} px "
      f"({(siluet == 255).sum() * mmpx**2:.0f} mm2)")

# --- 5. Kaydet ---
cv2.imwrite(r"D:\cadproj\out\siluet.png", siluet)

gd_gorsel = np.zeros((H, W), dtype=np.uint8)
gd_gorsel[gecme_delik] = 255
cv2.imwrite(r"D:\cadproj\out\gecme_delik.png", gd_gorsel)

print()
print("Kaydedildi: out/siluet.png")
print("Kaydedildi: out/gecme_delik.png")