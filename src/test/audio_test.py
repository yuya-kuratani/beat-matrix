import json
import time
import pygame

PIN_DATA = "../../assets/pin_data.json"

BPM = 180 #テンポ
TOTAL_STEPS = 16 #1小節ごとのパターン数
STEP_INTERVAL = 60 / BPM / 2

pygame.mixer.init()

# JSON読み込み
with open(PIN_DATA, "r", encoding="utf-8") as f:
    data = json.load(f)

# volume_levels = data["volume_levels"]

sound_map = {}

# 楽器データをmapに加工
for sound in data["sounds"]:
	sound_map[sound["instrument"]] = {
		"sound": pygame.mixer.Sound(sound["file"]),
		"patterns": {int(k): v for k, v in sound["patterns"].items()},
		"complexity": 0,
		"volume": 0
	}


def get_loop_parameters():
	"""
	1ループ分の入力を返す関数
	[[instrument, complexity, volume], ...]
	"""

	# 今は仮の出力
	return [
		["hat", 0, 2],
		["kick", 0, 0],
		["snare", 0, 3]
	]


# 再生
step = 0

try:
	while True:
		if step == 0:
			params = get_loop_parameters()

			for instrument, complexity, volume in params:
				if instrument not in sound_map:
					continue

				sound = sound_map[instrument]
				sound["complexity"] = complexity
				sound["volume"] = volume

				sound["sound"].set_volume(1)

			print("New loop params:", params)


		for sound in sound_map.values():
			pattern = sound["patterns"][sound["complexity"]]
			if pattern[step] == 1:
				# sound["sound"].set_volume(volume_levels[sound["volume"]])
				sound["sound"].play()

		step = (step + 1) % (TOTAL_STEPS * 2)
		time.sleep(STEP_INTERVAL)

except KeyboardInterrupt:
	pygame.mixer.quit()
	print("停止")
