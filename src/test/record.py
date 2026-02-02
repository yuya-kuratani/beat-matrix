import pyaudio   # マイク入力・スピーカー出力を扱う
import wave      # wavファイルの読み書き
import datetime  # 現在時刻åを取得
import time      # 録音の時間を管理
import select    # キーを選ぶ
import sys       # システム関連（保険的にインポート）
import os        # フォルダを自動生成


# instrument ごとの保存先（JSONと一致させる）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INSTRUMENT_WAV_PATH = {
    "hat": os.path.join(BASE_DIR, "assets/sounds/hat.wav"),
    "kick": os.path.join(BASE_DIR, "assets/sounds/kick.wav"),
    "snare": os.path.join(BASE_DIR, "assets/sounds/snare.wav")
}


# =====================
# 設定パラメータ
# =====================

RECORD_SECONDS = 5          # 録音する時間（秒）
WAV_FILE = "output.wav"     # 保存するwavファイル名

FORMAT = pyaudio.paInt16    # 音声フォーマット（16bit）
CHANNELS = 1                # チャンネル数（1 = モノラル）
RATE = 44100                # サンプリング周波数（Hz）
CHUNK = 1024                # 一度に処理する音データ数

# macOS の「デフォルト入力デバイス」を使用
INPUT_DEVICE_INDEX = None

# =====================
# 録音処理
# =====================
# 録音してwaveファイルに保存する関数
def record_audio(save_path):
    # PyAudio のインスタンスを作成
    audio = pyaudio.PyAudio()

    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=INPUT_DEVICE_INDEX,
        frames_per_buffer=CHUNK
    )

    input("▶ Enterキーを押して録音開始")

    frames = []
    start_time = time.time()

    print("録音中... Enterキーで終了（最大5秒）")

    while True:
        if time.time() - start_time > RECORD_SECONDS:
            break

        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
            break

    print("録音終了")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    os.makedirs(os.path.dirname(save_path), exist_ok=True)


    # ★ JSONが参照している wav を上書き保存
    with wave.open(save_path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))


def get_instrument_from_resistance(resistance):
    if resistance < 1000:
        return "hat"
    elif resistance < 5000:
        return "kick"
    else:
        return "snare"


# =====================
# 再生処理
# =====================
# 保存したwavファイルを再生する関数
def play_audio(wav_path):
    # wavファイルを読み込み
    wf = wave.open(wav_path, "rb")

    # PyAudio インスタンス作成
    audio = pyaudio.PyAudio()

    # 再生用ストリームを開く
    stream = audio.open(
        format=audio.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True                # 出力（スピーカー）を使う
    )

    print("再生中...")

    # wavファイルから音データを順に読み込んで再生
    data = wf.readframes(CHUNK)
    while data:
        stream.write(data)
        data = wf.readframes(CHUNK)

    # 再生終了処理
    stream.stop_stream()
    stream.close()
    audio.terminate()
    wf.close()

    print("再生終了")


# =====================
# メイン処理
# =====================
def main():
    print("=== 抵抗値テストモード ===")
    print("例: hat=500, kick=3000, snare=8000")

    # 抵抗値を手入力
    resistance = int(input("抵抗値を入力してください: "))

    # instrument 判別
    instrument = get_instrument_from_resistance(resistance)
    print(f"→ 判別結果: {instrument}")

    # 対応する wav パス
    save_path = INSTRUMENT_WAV_PATH[instrument]
    print(f"→ 保存先: {save_path}")

    # 録音
    record_audio(save_path)

    print(f"{instrument} の音を更新しました")

    # 再生確認
    input("▶ Enterキーで再生")
    play_audio(save_path)




# =====================
# 実行開始地点
# =====================
if __name__ == "__main__":
    # このファイルを直接実行したときだけ main() を呼ぶ
    main()
