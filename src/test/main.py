import json
import time
import os

from mcp3208_reader import MCP3208Reader
from resistor_detector import detect_resistor

with open("pin_data.json") as f:
    PIN_DEFS = json.load(f)

UPDATE_INTERVAL = 0.2  # 秒（リアルタイム更新周期）

def get_loop_parameter():
    """
    return:
        [[instrument, complexity, volume], ...] (length = 16)
    """
    reader = MCP3208Reader()
    voltages = reader.read_all_16()

    loop_params = []

    for v in voltages:
        pin = detect_resistor(v)

        if pin is None:
            # ピンなし
            loop_params.append([None, 0, 0])
        else:
            info = PIN_DEFS[pin]
            loop_params.append([
                info["instrument"],
                info["complexity"],
                info["volume"]
            ])

    return loop_params


if __name__ == "__main__":
    while True:
        os.system("clear")   # 画面を元通りリセット

        params = get_loop_parameter()
        for i, p in enumerate(params):
            print(f"Slot {i:02d}: {p}")

        time.sleep(UPDATE_INTERVAL)
