import time, threading                             # threadingは7seg表示をメイン処理と分岐のため
import board, busio                                # I2C用
import RPi.GPIO as GPIO                            # ラズパイのGPIO
from adafruit_mcp230xx.mcp23017 import MCP23017    # I2CのMCP23017の制御
from digitalio import Direction, Pull              # IN,OUTを読み取る Pull.UPで内部プルアップ

# ================= Raspberry Pi GPIO =================
SER   = 15   # pin10
RCLK  = 18   # pin12
SRCLK = 23   # pin16
INT_PIN = 24 # pin18

GPIO.setmode(GPIO.BCM)
GPIO.setup([SER, RCLK, SRCLK], GPIO.OUT)
GPIO.setup(INT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)    #INTはプルアップ(MCP側がLOWに落とす)

# ================= MCP23017 =================
i2c = busio.I2C(board.SCL, board.SDA) #バス作成
mcp = MCP23017(i2c)

def pin_in(n):                        #入力ピン用
    p = mcp.get_pin(n)
    p.direction = Direction.INPUT     
    p.pull = Pull.UP
    return p

def pin_out(n, init=True):            #出力ピン用
    p = mcp.get_pin(n)
    p.direction = Direction.OUTPUT
    p.value = init
    return p

# ---- Encoder 1 (VOLUME) ----
enc1_a  = pin_in(6)
enc1_b  = pin_in(5)
enc1_sw = pin_in(7) #PLAY-STOP

# ---- Encoder 2 (TEMPO) ----
enc2_a  = pin_in(1)
enc2_b  = pin_in(0)
enc2_sw = pin_in(2) #REC-STOP

# ---- LED control inputs ----
led1_in = pin_out(8, True)   # GPB0
led2_in = pin_out(9, True)   # GPB1

# ---- 7seg cathodes CC4..1 ----
digits = [
    pin_out(12, True),  # GPB4 CC4
    pin_out(13, True),  # GPB5 CC3
    pin_out(14, True),  # GPB6 CC2
    pin_out(15, True),  # GPB7 CC1
]

# ================= 7SEG MAP =================
SEG = {
    '0': 0b00111111,'1': 0b00000110,'2': 0b01011011,'3': 0b01001111,
    '4': 0b01100110,'5': 0b01101101,'6': 0b01111101,'7': 0b00000111,
    '8': 0b01111111,'9': 0b01101111,' ': 0b00000000,
}

def shift_out(val):                            # 8bitをシリアル転送
    for i in range(8):
        GPIO.output(SER, (val >> (7 - i)) & 1)
        GPIO.output(SRCLK, 1)
        GPIO.output(SRCLK, 0)

def latch():                                   # 表示確定
    GPIO.output(RCLK, 1)
    GPIO.output(RCLK, 0)

# ================= Controller =================
class Controller:
    def __init__(self):
        self.tempo = 120.0
        self.volume = 50.0
        self.mode = 0  # 0=VOLUME, 1=TEMPO
        
        #エンコーダの前回の状態の保存
        self.last_a1 = enc1_a.value
        self.last_a2 = enc2_a.value
        self.last_time = time.monotonic()
        self.last_action = time.monotonic()

        self.led1 = True
        self.led2 = True

    # ---------- Actions ----------
    def Rec(self):
        print("REC")
        self.led1 = not self.led1
        led1_in.value = self.led1

    def Play(self):
        print("PLAY")
        self.led2 = not self.led2
        led2_in.value = self.led2
        
    # ---------- Encoder ---------- .mode = 0でvol,1でtempo
    def handle(self, a, b, is_tempo):
        now = time.monotonic()
        dt = now - self.last_time
        self.last_time = now

        step = 0.5 if dt > 0.3 else 1 if dt > 0.15 else 5    # ゆっくり回すと0.5,普通の時は1,早く回したら5ずつ変化
        direction = 1 if b.value != a.value else -1          # A/Bの位相判定で読み取る(詳しくはwebで仕組みを理解していただけたら)

        if is_tempo:
            self.tempo = max(20, min(300, self.tempo + direction * step))    # 新しいtempo = self.tempo + direction * stepで、20<=tempo<=300
            self.mode = 1
        else:
            self.volume = max(0, min(100, self.volume + direction * step))   # 新しいvol = self.volume + direction * stepで、0<=vol<=100
            self.mode = 0

        self.last_action = now                                               # いじっている方を表示

    # ---------- Interrupt ----------
    def interrupt(self, ch):
        
        # どれが動いたかを割り込み内で判定
        if enc1_a.value != self.last_a1:            
            self.handle(enc1_a, enc1_b, False)
            self.last_a1 = enc1_a.value

        if enc2_a.value != self.last_a2:
            self.handle(enc2_a, enc2_b, True)
            self.last_a2 = enc2_a.value

        # スイッチの検出
        if not enc1_sw.value:
            self.Play()
            time.sleep(0.2)

        if not enc2_sw.value:
            self.Rec()
            time.sleep(0.2)

    # ---------- Display ----------
    def display(self):
        while True:
            v = int(self.volume if self.mode == 0 else self.tempo)
            s = f"{v:4d}"[-4:]

            for i, ch in enumerate(s):
                for d in digits:
                    d.value = True

                seg = SEG[ch]
                if self.mode == 1:
                    seg |= 0b10000000

                shift_out(seg)
                latch()
                digits[i].value = False
                time.sleep(0.002)

# ================= main =================
ctrl = Controller()

GPIO.add_event_detect(
    INT_PIN,
    GPIO.FALLING,
    callback=ctrl.interrupt,
    bouncetime=1
)

threading.Thread(target=ctrl.display, daemon=True).start() #メイン処理を絶対止めない

print("SYSTEM READY")

try:
    while True:
        if time.monotonic() - ctrl.last_action > 2:    # 2秒間何もしなかったらTEMPO表示に戻る←ここのデザインは要検討
            ctrl.mode = 1
        time.sleep(0.05)
except KeyboardInterrupt:
    GPIO.cleanup()
