#Eşikleme yaptığım kısım.

import numpy as np

# --- 1. Kaydettigimiz haritayi oku ---
veri = np.load(r"D:\cadproj\out\derinlik_z.npz")
d = veri["derinlik"]
mmpx = float(veri["mm_per_px"])

# --- 2. Dolu (isin carpmis) pikselleri isaretle ---
dolu = np.isfinite(d)

# --- 3. Referans yuzeyi bul ---
degerler, sayilar = np.unique(d[dolu], return_counts=True)
referans = degerler[np.argmax(sayilar)]

print("Derinlik seviyeleri ve piksel sayilari:")
for deg, say in zip(degerler, sayilar):
    print(f"  {deg:6.2f} mm  ->  {say:7d} piksel")
print()
print(f"Referans yuzey: {referans:.2f} mm")

# --- 4. Fark haritasi ---
fark = np.zeros_like(d)
fark[dolu] = d[dolu] - referans

print()
print(f"Fark araligi: {fark[dolu].min():.2f} .. {fark[dolu].max():.2f} mm")

import cv2

# --- 5. Esik degeri ---
# Referanstan bu kadar derin olan yerler "cikarilmis malzeme" sayilir.
# 0.5 mm secildi: mesh gurultusunu eler, en sig feature (6 mm) rahat gecer.
ESIK_MM = 0.5

# --- 6. Ikili maske olustur ---
# Once hepsi sifir (siyah) bir dizi
maske = np.zeros(d.shape, dtype=np.uint8)

# Dolu VE esikten derin olan pikselleri beyaz yap
derin = dolu & (fark > ESIK_MM)
maske[derin] = 255

print()
print(f"Esik: {ESIK_MM} mm")
print(f"Beyaz piksel: {maske.sum() // 255} / {maske.size}")

# --- 7. Kaydet ve bak ---
cv2.imwrite(r"D:\cadproj\out\maske_ilk.png", maske)
print("Kaydedildi: out/maske_ilk.png")