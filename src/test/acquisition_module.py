import json
from mcp3208_reader import MCP3208Reader
from resistor_detector import detect_resistor

with open("../../assets/pin_data.json") as f:
    PIN_DEFS = json.load(f)

_reader = MCP3208Reader()

def get_loop_parameter():
    """
    return:
        [[instrument, complexity, volume], ...] (length = 16)
    """
    
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


if __name__ == "__acquisition_module__":
    print("acquisition_module.py は取得用モジュールです。")
    print("audio_test.py から import して使用してください。")
