#Sınıflandırmayı yaptığım dosya. 

import numpy as np
import cv2

# ============================================================
# SINIFLANDIRMA ESIKLERI
# Hepsi tek yerde - ayar yapmak kolay olsun
# ============================================================
ESIK_MM        = 0.5     # bu kadar derin olan yerler "cikarilmis malzeme"
MIN_ALAN_MM2   = 5.0     # bundan kucuk lekeler gurultu sayilir
DAIRE_ESIK     = 0.85    # daire dolulugu bunun ustundeyse DELIK
SLOT_ORAN      = 2.5     # en/boy orani bunun ustundeyse SLOT
KENAR_KALINLIK = 3       # siluet kenar seridinin piksel kalinligi


def siniflandir(daire_dol, en_boy, kenara_degiyor, geciyor):
    """
    Bir feature'in tipini belirler.
    Sira onemli: once delik, sonra slot, geri kalan cep.
    """
    # 1) DELIK - dairesel mi
    if daire_dol > DAIRE_ESIK:
        return "GECME DELIK" if geciyor else "KOR DELIK"

    # 2) SLOT - uzun ve dar mi
    if en_boy > SLOT_ORAN:
        return "ACIK SLOT" if kenara_degiyor else "KAPALI SLOT"

    # 3) Kenara degen ve dairesel olmayan -> kesik slot olabilir
    if kenara_degiyor:
        return "ACIK SLOT"

    # 4) Geri kalan
    return "CEP"


# ============================================================
# 1. VERIYI OKU
# ============================================================
veri = np.load(r"D:\cadproj\out\derinlik_z.npz")
d = veri["derinlik"]
mmpx = float(veri["mm_per_px"])

H, W = d.shape
dolu = np.isfinite(d)

# ============================================================
# 2. SILUET, GECME DELIKLER, KENAR SERIDI
# ============================================================
bosluk = np.zeros((H, W), dtype=np.uint8)
bosluk[~dolu] = 255

ff = np.zeros((H + 2, W + 2), dtype=np.uint8)
disari = bosluk.copy()
cv2.floodFill(disari, ff, (0, 0), 128)

arka_plan   = (disari == 128)
gecme_delik = (disari == 255)

siluet = np.zeros((H, W), dtype=np.uint8)
siluet[~arka_plan] = 255

cekirdek = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
siluet_ic = cv2.erode(siluet, cekirdek, iterations=KENAR_KALINLIK)
kenar_seridi = (siluet == 255) & (siluet_ic == 0)

# ============================================================
# 3. REFERANS VE FARK
# ============================================================
degerler, sayilar = np.unique(d[dolu], return_counts=True)
referans = degerler[np.argmax(sayilar)]

fark = np.zeros_like(d)
fark[dolu] = d[dolu] - referans

# ============================================================
# 4. MASKE
# ============================================================
maske = np.zeros((H, W), dtype=np.uint8)
maske[dolu & (fark > ESIK_MM)] = 255
maske[gecme_delik] = 255

# Gurultu temizligi: kucuk delikleri kapat, serpintiyi sil
maske = cv2.morphologyEx(maske, cv2.MORPH_CLOSE, cekirdek, iterations=2)
maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN,  cekirdek, iterations=1)

# ============================================================
# 5. KONTURLAR VE SINIFLANDIRMA
# ============================================================
konturlar, _ = cv2.findContours(maske, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

# Renk kodlari (BGR)
RENK = {
    "GECME DELIK": (0, 255, 255),    # sari
    "KOR DELIK":   (0, 165, 255),    # turuncu
    "KAPALI SLOT": (0, 255, 0),      # yesil
    "ACIK SLOT":   (255, 255, 0),    # turkuaz
    "CEP":         (255, 0, 255),    # mor
}

gorsel = cv2.cvtColor(
    np.where(siluet == 255, 40, 0).astype(np.uint8),
    cv2.COLOR_GRAY2BGR,
)

sonuclar = []

for knt in konturlar:
    alan_px = cv2.contourArea(knt)
    alan_mm2 = alan_px * mmpx**2

    if alan_mm2 < MIN_ALAN_MM2:
        continue                      # gurultu, atla

    cevre_px = cv2.arcLength(knt, True)

    (_, _), (rw, rh), _ = cv2.minAreaRect(knt)
    uzun, kisa = max(rw, rh), min(rw, rh)
    en_boy = uzun / kisa if kisa > 0 else 0

    (_, _), yaricap = cv2.minEnclosingCircle(knt)
    daire_dol = alan_px / (np.pi * yaricap**2) if yaricap > 0 else 0

    bolge = np.zeros((H, W), dtype=np.uint8)
    cv2.drawContours(bolge, [knt], -1, 255, cv2.FILLED)
    bolge_bool = (bolge == 255)

    kenara_degiyor = bool((bolge_bool & kenar_seridi).any())
    gecme_orani = (bolge_bool & gecme_delik).sum() / max(bolge_bool.sum(), 1)
    geciyor = gecme_orani > 0.5

    ic = fark[bolge_bool & dolu]
    derinlik = float(ic.mean()) if ic.size > 0 else None

    tip = siniflandir(daire_dol, en_boy, kenara_degiyor, geciyor)

    M = cv2.moments(knt)
    cx = int(M["m10"] / M["m00"]) if M["m00"] else 0
    cy = int(M["m01"] / M["m00"]) if M["m00"] else 0

    sonuclar.append({
        "tip": tip,
        "alan_mm2": alan_mm2,
        "uzun_mm": uzun * mmpx,
        "kisa_mm": kisa * mmpx,
        "derinlik": derinlik,
        "merkez": (cx, cy),
    })

    # --- ciz ---
    renk = RENK[tip]
    cv2.drawContours(gorsel, [knt], -1, renk, 2)
    cv2.circle(gorsel, (cx, cy), 3, renk, -1)

# ============================================================
# 6. SONUCLARI YAZDIR
# ============================================================
print(f"Toplam {len(sonuclar)} feature bulundu.\n")

sayac = {}
for s in sonuclar:
    sayac[s["tip"]] = sayac.get(s["tip"], 0) + 1

    der = f"{s['derinlik']:.2f} mm" if s["derinlik"] is not None else "gecme"
    print(f"  {s['tip']:<12}  "
          f"alan {s['alan_mm2']:7.1f} mm2   "
          f"olcu {s['uzun_mm']:5.1f} x {s['kisa_mm']:4.1f} mm   "
          f"derinlik {der}")

print()
print("Ozet:")
for tip, adet in sorted(sayac.items()):
    print(f"  {tip:<12} : {adet}")

# ============================================================
# 7. ETIKETLERI GORSELE YAZ
# ============================================================
for s in sonuclar:
    cx, cy = s["merkez"]
    cv2.putText(gorsel, s["tip"], (cx - 45, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, RENK[s["tip"]], 1, cv2.LINE_AA)

cv2.imwrite(r"D:\cadproj\out\sonuc.png", gorsel)
print("\nKaydedildi: out/sonuc.png")