import numpy as np
import cv2

# ============================================================
# 1. VERIYI OKU
# ============================================================
veri = np.load(r"D:\cadproj\out\derinlik_z.npz")
d = veri["derinlik"]
mmpx = float(veri["mm_per_px"])

H, W = d.shape
dolu = np.isfinite(d)

# ============================================================
# 2. SILUET VE GECME DELIKLER
# ============================================================
bosluk = np.zeros((H, W), dtype=np.uint8)
bosluk[~dolu] = 255

ff_maske = np.zeros((H + 2, W + 2), dtype=np.uint8)
disari = bosluk.copy()
cv2.floodFill(disari, ff_maske, (0, 0), 128)

arka_plan = (disari == 128)
gecme_delik = (disari == 255)

siluet = np.zeros((H, W), dtype=np.uint8)
siluet[~arka_plan] = 255

# ============================================================
# 3. REFERANS YUZEY VE FARK HARITASI
# ============================================================
degerler, sayilar = np.unique(d[dolu], return_counts=True)
referans = degerler[np.argmax(sayilar)]

fark = np.zeros_like(d)
fark[dolu] = d[dolu] - referans

# ============================================================
# 4. TAM FEATURE MASKESI
# ============================================================
ESIK_MM = 0.5

tam_maske = np.zeros((H, W), dtype=np.uint8)

# (a) Referanstan derin olan dolu pikseller
tam_maske[dolu & (fark > ESIK_MM)] = 255

# (b) Gecme delikler - artik hangileri oldugunu biliyoruz
tam_maske[gecme_delik] = 255

print(f"Referans yuzey : {referans:.2f} mm")
print(f"Maske pikseli  : {(tam_maske == 255).sum()}")
print()

# ============================================================
# 5. SILUET KENAR SERIDI
# ============================================================
# Erozyon: siluetin dis kabugunu soyar.
# Siluet ile soyulmus hali arasindaki fark = kenar seridi.
KENAR_KALINLIK = 3

cekirdek = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
siluet_ic = cv2.erode(siluet, cekirdek, iterations=KENAR_KALINLIK)
kenar_seridi = (siluet == 255) & (siluet_ic == 0)

print(f"Kenar seridi pikseli: {kenar_seridi.sum()}")
print()

# ============================================================
# 6. KONTURLARI BUL VE OLC
# ============================================================
konturlar, hiyerarsi = cv2.findContours(
    tam_maske, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
)

print(f"Bulunan kontur sayisi: {len(konturlar)}")
print()

for i, knt in enumerate(konturlar):
    alan_px = cv2.contourArea(knt)
    cevre_px = cv2.arcLength(knt, True)

    dairesellik = 4 * np.pi * alan_px / cevre_px**2 if cevre_px > 0 else 0

    (_, _), (rw, rh), _ = cv2.minAreaRect(knt)
    uzun, kisa = max(rw, rh), min(rw, rh)
    en_boy = uzun / kisa if kisa > 0 else 0

    (_, _), yaricap = cv2.minEnclosingCircle(knt)
    daire_dol = alan_px / (np.pi * yaricap**2) if yaricap > 0 else 0

    # --- Bu konturun kapsadigi pikseller ---
    bolge = np.zeros((H, W), dtype=np.uint8)
    cv2.drawContours(bolge, [knt], -1, 255, thickness=cv2.FILLED)
    bolge_bool = (bolge == 255)

    # --- Siluet kenarina degiyor mu ---
    kenara_degiyor = bool((bolge_bool & kenar_seridi).any())

    # --- Gecme delik mi ---
    gecme_orani = (bolge_bool & gecme_delik).sum() / max(bolge_bool.sum(), 1)
    geciyor = gecme_orani > 0.5

    # --- Derinlik ---
    ic = fark[bolge_bool & dolu]
    ort_der = float(ic.mean()) if ic.size > 0 else float("nan")

    print(f"[{i}]")
    print(f"    alan          : {alan_px * mmpx**2:8.1f} mm2")
    print(f"    dairesellik   : {dairesellik:8.3f}")
    print(f"    en/boy        : {en_boy:8.2f}   ({uzun*mmpx:.1f} x {kisa*mmpx:.1f} mm)")
    print(f"    daire doluluk : {daire_dol:8.3f}")
    print(f"    kenara deger  : {kenara_degiyor}")
    print(f"    gecme delik   : {geciyor}")
    if np.isnan(ort_der):
        print(f"    derinlik      :   (gecme - taban yok)")
    else:
        print(f"    derinlik      : {ort_der:8.2f} mm")
    print()

# ============================================================
# 7. GORSELLESTIR
# ============================================================
gorsel = cv2.cvtColor(tam_maske, cv2.COLOR_GRAY2BGR)

# Kenar seridini mavi goster
gorsel[kenar_seridi] = (255, 100, 0)

# Konturlari kirmizi ciz
cv2.drawContours(gorsel, konturlar, -1, (0, 0, 255), 2)

cv2.imwrite(r"D:\cadproj\out\tam_maske.png", gorsel)
print("Kaydedildi: out/tam_maske.png")