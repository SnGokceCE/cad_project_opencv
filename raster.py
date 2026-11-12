#Rasterizasyon ile derinlik haritası üretmek için kullanılan fonksiyonlar.

import numpy as np


def derinlik_haritasi(vertices, faces, eksen, pozitif,
                      cozunurluk=512, pay=0.05):
    """
    Ortografik derinlik haritasi uretir (z-buffer rasterizasyonu).

    vertices : (N,3) float  kose koordinatlari
    faces    : (M,3) int    ucgen indeksleri
    eksen    : 0=X, 1=Y, 2=Z  bakis ekseni
    pozitif  : True  -> eksenin eksi tarafindan bakilir (isin +yone gider)
               False -> eksenin arti tarafindan bakilir (isin -yone gider)

    Doner: (derinlik, mm_per_px, kapsam)
      derinlik  : (H,W) float32, carpma yoksa np.inf
      mm_per_px : bir pikselin mm karsiligi
      kapsam    : (u_min, u_max, v_min, v_max)
    """
    v = np.asarray(vertices, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64)

    u_ax, v_ax = [i for i in range(3) if i != eksen]

    lo = v.min(axis=0)
    hi = v.max(axis=0)

    span_u = hi[u_ax] - lo[u_ax]
    span_v = hi[v_ax] - lo[v_ax]
    u_min = lo[u_ax] - span_u * pay
    u_max = hi[u_ax] + span_u * pay
    v_min = lo[v_ax] - span_v * pay
    v_max = hi[v_ax] + span_v * pay

    mm_per_px = max(u_max - u_min, v_max - v_min) / cozunurluk
    W = int(np.ceil((u_max - u_min) / mm_per_px))
    H = int(np.ceil((v_max - v_min) / mm_per_px))

    # Isin baslangic duzlemi (parcanin tamamen disinda)
    kalinlik = hi[eksen] - lo[eksen]
    if pozitif:
        w0 = lo[eksen] - kalinlik - 10.0
    else:
        w0 = hi[eksen] + kalinlik + 10.0

    # Ucgen koselerini piksel koordinatlarina cevir
    # px = (u - u_min) / mmpx - 0.5   -> piksel merkezleri tam sayilarda
    P = v[f]                                  # (M,3,3)
    pu = (P[:, :, u_ax] - u_min) / mm_per_px - 0.5
    pv = (P[:, :, v_ax] - v_min) / mm_per_px - 0.5
    pw = P[:, :, eksen]                       # derinlik ekseni degeri

    # Bize en yakin yuzey: pozitif bakista en kucuk w, negatifte en buyuk w
    en_iyi = np.full((H, W), np.inf if pozitif else -np.inf, dtype=np.float64)

    for t in range(len(f)):
        u0, u1, u2 = pu[t]
        v0, v1, v2 = pv[t]
        w0_, w1_, w2_ = pw[t]

        alan = (u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0)
        if abs(alan) < 1e-12:
            continue                          # bakis yonune paralel yuzey

        i0 = max(int(np.floor(min(u0, u1, u2))), 0)
        i1 = min(int(np.ceil(max(u0, u1, u2))), W - 1)
        j0 = max(int(np.floor(min(v0, v1, v2))), 0)
        j1 = min(int(np.ceil(max(v0, v1, v2))), H - 1)
        if i1 < i0 or j1 < j0:
            continue

        ii, jj = np.meshgrid(np.arange(i0, i1 + 1),
                             np.arange(j0, j1 + 1))
        ii = ii.astype(np.float64)
        jj = jj.astype(np.float64)

        # Barycentric koordinatlar
        b1 = ((ii - u0) * (v2 - v0) - (u2 - u0) * (jj - v0)) / alan
        b2 = ((u1 - u0) * (jj - v0) - (ii - u0) * (v1 - v0)) / alan
        b0 = 1.0 - b1 - b2

        icinde = (b0 >= -1e-9) & (b1 >= -1e-9) & (b2 >= -1e-9)
        if not icinde.any():
            continue

        w = b0 * w0_ + b1 * w1_ + b2 * w2_

        alt = en_iyi[j0:j1 + 1, i0:i1 + 1]
        if pozitif:
            np.copyto(alt, w, where=icinde & (w < alt))
        else:
            np.copyto(alt, w, where=icinde & (w > alt))

    bos = ~np.isfinite(en_iyi)
    derinlik = np.abs(en_iyi - w0).astype(np.float32)
    derinlik[bos] = np.inf

    # Goruntu koordinatinda v ekseni asagi dogru artar
    derinlik = np.flipud(derinlik)

    return derinlik, mm_per_px, (u_min, u_max, v_min, v_max)