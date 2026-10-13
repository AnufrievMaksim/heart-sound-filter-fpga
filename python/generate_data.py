import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter

# 1. Параметры входного сигнала
Fs = 8000  # Частота дискретизации, Гц
duration = 4.0  # Длительность сигнала, с
t = np.linspace(0, duration, int(Fs * duration), endpoint=False)

# 2. Моделирование первичного сигнала сердцебиения
heart_beat = np.zeros_like(t)
for strike in np.arange(0, duration, 0.8):
    idx = int(strike * Fs)
    if idx + int(0.3 * Fs) < len(t):
        # Формирование компонента S1 (частота 40 Гц, длительность 0.1 с)
        heart_beat[idx : idx + int(0.1 * Fs)] = np.sin(2 * np.pi * 40 * t[: int(0.1 * Fs)])
        # Формирование компонента S2 (частота 60 Гц, задержка 0.25 с, коэффициент ослабления 0.6)
        heart_beat[idx + int(0.25 * Fs) : idx + int(0.35 * Fs)] = np.sin(2 * np.pi * 60 * t[: int(0.1 * Fs)]) * 0.6

# 3. Моделирование высокочастотной помехи
# Аддитивная смесь двух гармонических составляющих (1200 Гц и 1500 Гц) в одну строку
high_freq_noise = np.sin(2 * np.pi * 1200 * t) * 0.4 + np.sin(2 * np.pi * 1500 * t) * 0.3

# 4. Формирование суммарного зашумленного сигнала
ecg_audio_signal = heart_beat + high_freq_noise

# 5. Цифровая фильтрация низких частот (ФНЧ)
# Расчет весовых коэффициентов КИХ-фильтра методом окон (частота среза 150 Гц, порядок фильтра 100)
cutoff_hz = 150.0
numtaps = 101
fir_coeffs = firwin(numtaps, cutoff_hz, fs=Fs)
# Линейная фильтрация входной последовательности
filtered_signal = lfilter(fir_coeffs, 1.0, ecg_audio_signal)

# 6. Масштабирование и дискретизация по амплитуде (квантование)
adc_values = (ecg_audio_signal * 1000).astype(int)

# 7. Преобразование плавающих коэффициентов в 16-битный целочисленный формат (Q15)
fir_coeffs_int = np.round(fir_coeffs * 32768).astype(int)

# 8. Запись расчетных коэффициентов в текстовый файл формата HEX
with open("coeffs.hex", "w") as f:
    for coeff in fir_coeffs_int:
        val = coeff & 0xFFFF
        f.write(f"{val:04x}\n")

# 9. Текстовый вывод результатов в консоль
print("Шаг 1.2 Завершен: Искусственный аудиосигнал сердца успешно сгенерирован!")
print("Файл coeffs.hex успешно создан в памяти!")
print("Первые 10 коэффициентов в HEX формате:")
for i in range(10):
    val = fir_coeffs_int[i] & 0xFFFF
    print(f"Адрес [{i}]: {val:04x} (в десятичной системе: {fir_coeffs_int[i]})")

# 10. Графический анализ результатов моделирования
plt.figure(figsize=(10, 10))

# Временная диаграмма исходного сигнала
plt.subplot(3, 1, 1)
plt.plot(t, heart_beat, color="blue")
plt.title("Исходный сигнал сердцебиения (heart_beat)")
plt.xlabel("Время, с")
plt.ylabel("Амплитуда, у.е.")
plt.xlim(0, 2.0)
plt.grid(True)

# Временная диаграмма зашумленного входного сигнала
plt.subplot(3, 1, 2)
plt.plot(t, ecg_audio_signal, color="salmon")
plt.title("Зашумленный сигнал (полоса помехи 1200-1500 Гц)")
plt.xlabel("Время, с")
plt.ylabel("Амплитуда, у.е.")
plt.xlim(0, 2.0)
plt.grid(True)

# Временная диаграмма сигнала после прохождения КИХ-фильтра
plt.subplot(3, 1, 3)
plt.plot(t, filtered_signal, color="green")
plt.title("Сигнал на выходе низкочастотного КИХ-фильтра (filtered_signal)")
plt.xlabel("Время, с")
plt.ylabel("Амплитуда, у.е.")
plt.xlim(0, 2.0)
plt.grid(True)

plt.tight_layout()
plt.show()


