import json
import time
import pygame

from acquisition_module import get_loop_parameter

#再生設定
BPM = 180 #テンポ
TOTAL_STEPS = 16 #1小節ごとのパターン数
STEP_INTERVAL = 60 / BPM / 2

volume_levels = [0.0, 0.3, 0.6, 1.0]

pygame.mixer.init()

# sound_mapをJSONから構築
PIN_DATA = "../../assets/pin_data.json"

with open(PIN_DATA, "r", encoding="utf-8") as f:
    pin_data = json.load(f)

sound_map = {}

for sound in pin_data["sounds"]:
	sound_map[sound["instrument"]] = {
		"sound": pygame.mixer.Sound(sound["file"]),
		"patterns": {int(k): v for k, v in sound["patterns"].items()},
	}


#再生ループ
try:
	step = 0

	while True:
		loop_params = get_loop_parameter()
			
		for slot, param in enumerate(loop_params):
            instrument, complexity, volume = param

            # ピンなし
            if instrument is None:
                continue

            # JSONに存在しない楽器は無視
            if instrument not in sound_map:
                continue

            sound_info = sound_map[instrument]
            pattern = sound_info["patterns"][complexity]

            if pattern[step % TOTAL_STEPS] == 1:
                snd = sound_info["sound"]
                snd.set_volume(volume_levels[volume])
                snd.play()

		step = (step + 1) % (TOTAL_STEPS * 2)
		time.sleep(STEP_INTERVAL)

except KeyboardInterrupt:
	pygame.mixer.quit()
	print("停止")
