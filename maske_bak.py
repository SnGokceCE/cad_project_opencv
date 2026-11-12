#Maskenin ne olduğunu iyice anlamak için oluşturduğum dosya.

import numpy as np

veri = np.load(r"D:\cadproj\out\derinlik_z.npz")
d = veri["derinlik"]

# --- dolu maskesi (True/False) ---
dolu = np.isfinite(d)

print("dolu maskesi:")
print(f"  tip   : {dolu.dtype}")
print(f"  boyut : {dolu.shape}")
print(f"  True  : {dolu.sum()}")
print(f"  False : {(~dolu).sum()}")
print()

# Kucuk bir bolgeyi yazdir - parcanin sol ust kosesi civari
print("Derinlik degerleri (satir 90-95, sutun 100-108):")
print(d[90:96, 100:109])
print()

print("Ayni bolgede dolu maskesi:")
print(dolu[90:96, 100:109])
print()

# Bos bolgeden ornek - goruntunun sol ust kosesi (parcanin disi)
print("Parcanin disi (satir 5-8, sutun 5-10):")
print(d[5:9, 5:11])
print()
print("Orada dolu maskesi:")
print(dolu[5:9, 5:11])