import math

KNOWN_RESISTORS = {
    "100k": 100_000,
    "45k": 45_000,
    "26.6k": 26_600,
    "17.5k": 17_500,
    "12k": 12_000,
    "8.3k": 8_300,
    "5.7k": 5_700,
    "3.75k": 3_750,
    "2.22k": 2_220,
    "1k": 1_000
}

FIXED_R = 10_000      # 分圧用 10kΩ
VREF = 3.3
TOLERANCE = 0.15      # ±15%

def voltage_to_resistance(v):
    if v <= 0.01 or v >= VREF - 0.01:
        return None
    return FIXED_R * v / (VREF - v)

def detect_resistor(v):
    r = voltage_to_resistance(v)
    if r is None:
        return None

    for name, ref in KNOWN_RESISTORS.items():
        if abs(r - ref) / ref < TOLERANCE:
            return name
    return None
