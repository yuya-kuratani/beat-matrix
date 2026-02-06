# sudo apt update
# sudo apt install -y portaudio19-dev ffmpeg
# pip install pyaudio pydub

import pyaudio   # マイク入力・スピーカー出力を扱う
import wave      # wavファイルの読み書き
import time      # 録音の時間を管理
import select    # キーを選ぶ ←ここはキーボードの入力のやつだから後で消す
import sys       # システム関連（保険的にインポート）
import os        # フォルダを自動生成
from pydub import AudioSegment, silence # コンプレッションやトリミング、増幅
from enum import Enum                   # 止める、抜くで結果の変更

class RecordResult(Enum):
    OK = 1         # 録音成功
    ABORT = 2      # 抵抗抜く
    SILENCE = 3    # 無音時


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
bpm = 120                   # 後でロータリーエンコーダで可変にする
counts = 4                  # 気まぐれで後でロータリーエンコーダで可変にする
target_db = -1.0            # 気まぐれで後でロータリーエンコーダで可変にする
WAV_FILE = "output.wav"     # 保存するwavファイル名
FORMAT = pyaudio.paInt16    # 音声フォーマット（16bit）
CHANNELS = 1                # チャンネル数（1 = モノラル）
RATE = 44100                # サンプリング周波数（Hz）
CHUNK = 1024                # 一度に処理する音データ数
fade_ms = 50                # fadeする秒数

INPUT_DEVICE_INDEX = None   # macOS の「デフォルト入力デバイス」を使用

def tempo(bpm):        
    return 60 / bpm         # テンポの設定
# =====================
# 録音処理
# =====================
# 録音前に4カウント打つ
def count_in(bpm):
    interval = tempo(bpm)    # 1拍の秒数
    for i in range(counts):
        print(f"{counts - i}")
        #7segで表示&LED光らせる
        time.sleep(interval)
        
# 録音してwaveファイルに保存する関数
def record_audio():
    
    # PyAudio のインスタンスを作成
    audio = pyaudio.PyAudio()
    sample_width = audio.get_sample_size(FORMAT)

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
    
    # 録音前カウント
    

    print("録音中... Enterキーで終了（最大１小節）") #本来はボタンを押して終了

    while True:
        if time.time() - start_time > tempo(bpm) * 4:
            result = RecordResult.OK
            break

        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]: # stdinに入力が来ているか0秒待って調べる=後で消して
            sys.stdin.readline()
            result = RecordResult.OK
            break
            
        if record_RE_switch(): # ロータリーエンコーダのスイッチが押されたら
            result = RecordResult.OK
            break
            
        if resistance_removed(): # 抵抗が抜けたら
            result = RecordResult.ABORT
            break

    print("録音終了")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    return frames, result, sample_width #flamesで一時データを保持

def resistance_removed():
    #処理お願い
    return False

def record_RE_switch():
    #GPIO読み取り(7seg,ロータリーエンコーダ(RE)読み取りの書いたら後で貼ります)
    return False
    
    


def get_instrument_from_resistance(resistance): # ここも本来はロータリーエンコーダで選択、決定
    if resistance < 1000:
        return "hat"
    elif resistance < 5000:
        return "kick"
    else:
        return "snare"
        
# =====================
# トリミング処理
# =====================
def trim_silence(audio_seg, silence_thresh=-40, min_silence_len=80) : # -40dBより小さい音が80ms以上続いたら切る

    chunks = silence.split_on_silence(
        audio_seg,
        minsilence_len = min_silence_len,  
        silence_thresh = silence_thresh
    )

    if len(chunks) == 0:
        print("無音しか検出されませんでした")
        return audio_seg, RecordResult.SILENCE

    return chunks[0], RecordResult.OK

def compress_audio(audio_seg):
    return audio_seg.compress_dynamic_range(
        threshold = -12.0,                  # これ(dB)超えたら潰す
        ratio = 3.0,                        # thresholdで超えたdBを、元の比率の3:1に
        attack = 5,                         # 音がthresholdを超えてからどれくらいの速さ(ms)で圧縮開始か
        release = 100                       # 音がthresholdを下回った時、いつ圧縮を解除するか
    )
def peak_normalize(audio_seg):              # 小ちゃい音を大体増幅!
    if audio_seg.max_dBFS == float("-inf"): # 一応無音はそのまま
        return audio_seg
    peak_db = audio_seg.max_dBFS            # 録音したやつで一番でかい瞬間
    gain = target_db - peak_db              # target_dbになるように全体に同じゲインをかける
    return audio_seg.apply_gain(gain)

def fade(audio_seg, bpm, counts):
    return audio_seg.fade_out(fade_ms)

    if length > bar_ms:
        # 長すぎる → バッサリ
        return audio_seg[:bar_ms]

    else:
        # 短い → フェードアウト
        fade_ms = min(fade_ms, length)
        return audio_seg.fade_out(fade_ms)
# =====================
# 再生処理
# =====================
        
# 保存したwavファイルを再生する関数
def play_audio(wav_path):
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

    # ---------------------
    # 録音
    # ---------------------
    #4カウント
    count_in(bpm)
    
    #録音
    frames, result, sample_width = record_audio()
    
    #処理で分岐
    if result == RecordResult.ABORT:
        print("抵抗が抜けたため録音破棄")
        #LED(7segでQUITか赤色光らす)
        return #何もしないでwavを保存

    
    elif result == RecordResult.OK:
        
        #一時wavに保存
        temp_path = save_path + ".tmp.wav"

        # ★ JSONが参照している wav を上書き保存
        with wave.open(temp_path, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(sample_width)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))

        # 無音をトリム
        audio_seg = AudioSegment.from_wav(temp_path)
        trimmed, process_result = trim_silence(audio_seg)
        
        if process_result == RecordResult.SILENCE:
            print("無音検出のため元のwavを維持")
            #LED(7segでANYか赤色光らす)
            os.remove(temp_path)
            return
        

        processed = peak_normalize(trimmed)    # 小さい音を持ち上げる
        processed = compress_audio(processed)  # 大きい音を潰す
        processed = fade(fade_ms)              # 長いやつをfadeする

        # 本保存
        processed.export(save_path, format = "wav")
        os.remove(temp_path)
    
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
