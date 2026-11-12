import numpy as np

# Dosyayi ac
veri = np.load(r"D:\cadproj\out\derinlik_z.npz")

# Icindeki isimleri listele
print("Dosyadaki diziler:", veri.files)
print()

# Tek tek oku
d = veri["derinlik"]
mmpx = float(veri["mm_per_px"])

print(f"Harita boyutu : {d.shape}")
print(f"mm / piksel   : {mmpx:.4f}")
print(f"Veri tipi     : {d.dtype}")
print()

gecerli = np.isfinite(d)
print(f"Dolu piksel   : {gecerli.sum()}")
print(f"Bos piksel    : {(~gecerli).sum()}")
print(f"Deger araligi : {d[gecerli].min():.2f} .. {d[gecerli].max():.2f}")
print()

# Hangi derinlik seviyeleri var?
seviyeler = np.unique(np.round(d[gecerli], 2))
print(f"Farkli derinlik degerleri: {seviyeler}")