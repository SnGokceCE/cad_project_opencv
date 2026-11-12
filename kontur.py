import numpy as np
import cv2

# --- 1. Maskeyi olustur (esikle.py'deki adimlarin ozeti) ---
veri = np.load(r"D:\cadproj\out\derinlik_z.npz")
d = veri["derinlik"]
mmpx = float(veri["mm_per_px"])

dolu = np.isfinite(d)
degerler, sayilar = np.unique(d[dolu], return_counts=True)
referans = degerler[np.argmax(sayilar)]

fark = np.zeros_like(d)
fark[dolu] = d[dolu] - referans

ESIK_MM = 0.5
maske = np.zeros(d.shape, dtype=np.uint8)
maske[dolu & (fark > ESIK_MM)] = 255

# --- 2. Konturlari bul ---
konturlar, hiyerarsi = cv2.findContours(
    maske,
    cv2.RETR_CCOMP,              # dis ve ic konturlari ayri seviyelerde tut
    cv2.CHAIN_APPROX_SIMPLE,     # duz kenarlardaki ara noktalari at
)

print(f"Bulunan kontur sayisi: {len(konturlar)}")
print()

# --- 3. Her kontur icin sekil olculeri ---
H, W = maske.shape

for i, knt in enumerate(konturlar):
    alan_px = cv2.contourArea(knt)
    cevre_px = cv2.arcLength(knt, True)

    # --- Dairesellik ---
    # Daire icin 1.0, uzadikca veya girintilendikce dusser
    if cevre_px > 0:
        dairesellik = 4.0 * np.pi * alan_px / (cevre_px ** 2)
    else:
        dairesellik = 0.0

    # --- Donebilen en kucuk saran dikdortgen ---
    # ((merkez_x, merkez_y), (genislik, yukseklik), aci)
    (rc_x, rc_y), (rw, rh), aci = cv2.minAreaRect(knt)
    uzun = max(rw, rh)
    kisa = min(rw, rh)
    en_boy = uzun / kisa if kisa > 0 else 0.0

    # --- Dikdortgene doluluk ---
    # Sekil, saran dikdortgeni ne kadar dolduruyor
    rect_doluluk = alan_px / (rw * rh) if rw * rh > 0 else 0.0

    # --- Konveks orte doluluk ---
    # Girintili sekillerde duser
    hull = cv2.convexHull(knt)
    hull_alan = cv2.contourArea(hull)
    doluluk = alan_px / hull_alan if hull_alan > 0 else 0.0

    # --- Saran daire ---
    (dc_x, dc_y), yaricap = cv2.minEnclosingCircle(knt)
    daire_doluluk = alan_px / (np.pi * yaricap ** 2) if yaricap > 0 else 0.0

    # --- Goruntu kenarina degiyor mu ---
    x, y, w, h = cv2.boundingRect(knt)
    kenarda = (x <= 1) or (y <= 1) or (x + w >= W - 1) or (y + h >= H - 1)

    # --- Ortalama derinlik (orijinal haritadan) ---
    bolge = np.zeros(maske.shape, dtype=np.uint8)
    cv2.drawContours(bolge, [knt], -1, 255, thickness=cv2.FILLED)
    ic = fark[(bolge == 255) & dolu]
    ort_derinlik = float(ic.mean()) if ic.size > 0 else 0.0
    derinlik_std = float(ic.std()) if ic.size > 0 else 0.0

    # --- Yazdir ---
    print(f"[{i}]")
    print(f"    alan          : {alan_px * mmpx**2:8.1f} mm2")
    print(f"    dairesellik   : {dairesellik:8.3f}")
    print(f"    en/boy orani  : {en_boy:8.2f}   ({uzun*mmpx:.1f} x {kisa*mmpx:.1f} mm)")
    print(f"    dikd. doluluk : {rect_doluluk:8.3f}")
    print(f"    konveks dolu. : {doluluk:8.3f}")
    print(f"    daire doluluk : {daire_doluluk:8.3f}")
    print(f"    kenarda mi    : {kenarda}")
    print(f"    derinlik      : {ort_derinlik:8.2f} mm  (sapma {derinlik_std:.3f})")
    print()

# --- 4. Konturlari ciz ve kaydet ---
gorsel = cv2.cvtColor(maske, cv2.COLOR_GRAY2BGR)   # gri -> renkli
cv2.drawContours(gorsel, konturlar, -1, (0, 0, 255), 2)   # kirmizi, 2 px kalinlik

cv2.imwrite(r"D:\cadproj\out\konturlar.png", gorsel)
print("Kaydedildi: out/konturlar.png")