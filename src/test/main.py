import json
from mcp3208_reader import MCP3208Reader
from resistor_detector import detect_resistor

with open("pin_data.json") as f:
    PIN_DEFS = json.load(f)

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
    params = get_loop_parameter()
    for i, p in enumerate(params):
        print(f"Slot {i:02d}: {p}")
