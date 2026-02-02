import time, threading
import board, busio
import RPi.GPIO as GPIO
from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction, Pull

# ================= Raspberry Pi GPIO =================
SER   = 15   # pin10
RCLK  = 18   # pin12
SRCLK = 23   # pin16
INT_PIN = 24 # pin18

GPIO.setmode(GPIO.BCM)
GPIO.setup([SER, RCLK, SRCLK], GPIO.OUT)
GPIO.setup(INT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ================= MCP23017 =================
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c)

def pin_in(n):
    p = mcp.get_pin(n)
    p.direction = Direction.INPUT
    p.pull = Pull.UP
    return p

def pin_out(n, init=True):
    p = mcp.get_pin(n)
    p.direction = Direction.OUTPUT
    p.value = init
    return p

# ---- Encoder 1 (TEMPO) ----
enc1_a  = pin_in(6)
enc1_b  = pin_in(5)
enc1_sw = pin_in(7)

# ---- Encoder 2 (VOLUME) ----
enc2_a  = pin_in(1)
enc2_b  = pin_in(0)
enc2_sw = pin_in(2)

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

def shift_out(val):
    for i in range(8):
        GPIO.output(SER, (val >> (7 - i)) & 1)
        GPIO.output(SRCLK, 1)
        GPIO.output(SRCLK, 0)

def latch():
    GPIO.output(RCLK, 1)
    GPIO.output(RCLK, 0)

# ================= Controller =================
class Controller:
    def __init__(self):
        self.tempo = 120.0
        self.volume = 50.0
        self.mode = 0  # 0=TEMPO, 1=VOLUME

        self.last_a1 = enc1_a.value
        self.last_a2 = enc2_a.value
        self.last_time = time.monotonic()
        self.last_action = time.monotonic()

        self.led1 = True
        self.led2 = True

    # ---------- Actions ----------
    def Play(self):
        print("PLAY")
        self.led1 = not self.led1
        led1_in.value = self.led1

    def Rec(self):
        print("REC")
        self.led2 = not self.led2
        led2_in.value = self.led2

    # ---------- Encoder ----------
    def handle(self, a, b, is_tempo):
        now = time.monotonic()
        dt = now - self.last_time
        self.last_time = now

        step = 0.5 if dt > 0.3 else 1 if dt > 0.15 else 5
        direction = 1 if b.value != a.value else -1

        if is_tempo:
            self.tempo = max(20, min(300, self.tempo + direction * step))
            self.mode = 0
        else:
            self.volume = max(0, min(100, self.volume + direction * step))
            self.mode = 1

        self.last_action = now

    # ---------- Interrupt ----------
    def interrupt(self, ch):
        if enc1_a.value != self.last_a1:
            self.handle(enc1_a, enc1_b, True)
            self.last_a1 = enc1_a.value

        if enc2_a.value != self.last_a2:
            self.handle(enc2_a, enc2_b, False)
            self.last_a2 = enc2_a.value

        if not enc1_sw.value:
            self.Play()
            time.sleep(0.2)

        if not enc2_sw.value:
            self.Rec()
            time.sleep(0.2)

    # ---------- Display ----------
    def display(self):
        while True:
            v = int(self.tempo if self.mode == 0 else self.volume)
            s = f"{v:4d}"[-4:]

            for i, ch in enumerate(s):
                for d in digits:
                    d.value = True

                seg = SEG[ch]
                if self.mode == 0:
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

threading.Thread(target=ctrl.display, daemon=True).start()

print("SYSTEM READY")

try:
    while True:
        if time.monotonic() - ctrl.last_action > 2:
            ctrl.mode = 0
        time.sleep(0.05)
except KeyboardInterrupt:
    GPIO.cleanup()
