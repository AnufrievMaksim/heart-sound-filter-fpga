# ===================================================
# 1. ИМПОРТ БИБЛИОТЕК
# ===================================================
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter
from sklearn.linear_model import LogisticRegression

# ===================================================
# 2. ПАРАМЕТРЫ СИГНАЛА
# ===================================================
FS = 8000               # частота дискретизации, Гц
DURATION = 4.0          # длительность, с
T = np.linspace(0, DURATION, int(FS * DURATION), endpoint=False)

# ===================================================
# 3. ГЕНЕРАЦИЯ СИГНАЛА СЕРДЦА
# ===================================================
heart_beat = np.zeros_like(T)
for strike in np.arange(0, DURATION, 0.8):
    idx = int(strike * FS)
    if idx + int(0.3 * FS) < len(T):
        heart_beat[idx : idx + int(0.1 * FS)] = np.sin(
            2 * np.pi * 40 * T[: int(0.1 * FS)]
        )
        heart_beat[idx + int(0.25 * FS) : idx + int(0.35 * FS)] = (
            np.sin(2 * np.pi * 60 * T[: int(0.1 * FS)]) * 0.6
        )

# ===================================================
# 4. ГЕНЕРАЦИЯ ШУМА
# ===================================================
high_freq_noise = (
    np.sin(2 * np.pi * 1200 * T) * 0.4
    + np.sin(2 * np.pi * 1500 * T) * 0.3
)
noisy_signal = heart_beat + high_freq_noise

# ===================================================
# 5. FIR-ФИЛЬТР
# ===================================================
CUTOFF_HZ = 150.0
NUMTAPS = 101
fir_coeffs = firwin(NUMTAPS, CUTOFF_HZ, fs=FS)
filtered_signal = lfilter(fir_coeffs, 1.0, noisy_signal)

# Расчет групповой задержки линейно-фазового КИХ-фильтра (в отсчетах)
group_delay = (NUMTAPS - 1) // 2

# ===================================================
# 6. ОБУЧЕНИЕ ML-НЕЙРОНА
# ===================================================
WINDOW_SIZE = 100
features = []
labels = []

for i in range(0, len(filtered_signal) - WINDOW_SIZE, WINDOW_SIZE):
    window = filtered_signal[i : i + WINDOW_SIZE]
    features.append([np.max(np.abs(window)), np.mean(np.abs(window))])

    start_idx = i + group_delay
    end_idx = start_idx + WINDOW_SIZE

    if end_idx <= len(heart_beat):
        reference_window = heart_beat[start_idx:end_idx]
        labels.append(1 if np.max(np.abs(reference_window)) > 0.5 else 0)
    else:
        labels.append(0)

X = np.array(features)
y = np.array(labels)

model = LogisticRegression()
model.fit(X, y)

# ===================================================
# 7. ИЗВЛЕЧЕНИЕ ВЕСОВ
# ===================================================
weight1 = model.coef_[0][0]
weight2 = model.coef_[0][1]
bias = model.intercept_[0]

print(f"WEIGHT1 = {weight1:.4f}")
print(f"WEIGHT2 = {weight2:.4f}")
print(f"BIAS = {bias:.4f}")

# ===================================================
# 8. СОХРАНЕНИЕ КОЭФФИЦИЕНТОВ FIR
# ===================================================
fir_coeffs_int = np.round(fir_coeffs * 32768).astype(int)
with open("coeffs.hex", "w") as f:
    for coeff in fir_coeffs_int:
        val = coeff & 0xFFFF
        f.write(f"{val:04x}\n")

# ===================================================
# 9. СОХРАНЕНИЕ ВЕСОВ НЕЙРОНА
# ===================================================
with open("weights.hex", "w") as f:
    for w in [weight1, weight2, bias]:
        w_clipped = np.clip(w, -512.0, 511.9375)
        w_int = int(np.round(w_clipped * 64)) & 0xFFFF
        f.write(f"{val:04x}\n")

print("coeffs.hex и weights.hex созданы")

# ===================================================
# 10. ВИЗУАЛИЗАЦИЯ
# ===================================================
os.makedirs("docs", exist_ok=True)

plt.figure(figsize=(10, 8))

plt.subplot(3, 1, 1)
plt.plot(T, heart_beat, color="blue")
plt.title("Signal 1 (Reference)")
plt.grid(True)

plt.subplot(3, 1, 2)
plt.plot(T, noisy_signal, color="salmon")
plt.title("Signal 2 (Noisy)")
plt.grid(True)

plt.subplot(3, 1, 3)
plt.plot(T, filtered_signal, color="green")
plt.title("Signal 3 (Filtered)")
plt.grid(True)

plt.tight_layout()
plt.savefig("docs/graphs.png")
plt.show()



