# code.py — Feather nRF52840 + Grove Shield (ohne Button, zyklisch)
import time
import board
import adafruit_dht
from ultrasonic_ranger import Ultrasonic
from chainable_led import P9813
import tm1637lib
import analogio


# --- Pins / Hardware ---
ULTRA_PIN = board.D9
DHT_PIN   = board.D5
led       = P9813(board.A5, board.A4, 1)                       # Grove A4: A5=CLK, A4=DATA
display   = tm1637lib.Grove4DigitDisplay(board.A2, board.A3)  # Grove A2: A2=DIO, A3=CLK
light_sensor = analogio.AnalogIn(board.A0)  # Grove A0-Port

sonar = Ultrasonic(ULTRA_PIN)
dht   = adafruit_dht.DHT11(DHT_PIN)

# --- Intervalle ---
DHT_INTERVAL   = 2.0
US_INTERVAL    = 0.3
PRINT_INTERVAL = 2.0
COLON_PERIOD   = 0.5

def set_led_rgb(r, g, b):
    led[0] = (r, g, b)
    led.write()

def color_for_temp(t):
    if t is None:
        set_led_rgb(0, 0, 0)
    elif t < 30:
        set_led_rgb(0, 0, 255)     # blau
    elif 60 <= t <= 65:
        set_led_rgb(0, 255, 0)     # grün
    elif t > 65:
        set_led_rgb(255, 0, 0)     # rot
    else:
        set_led_rgb(0, 0, 0)

def show_temp_on_display(t):
    display.show("----" if t is None else "{:>4}".format(int(round(t))))

print("Start: Ultra + DHT11 + 4-Digit + RGB-LED (zyklisch)")
print("Zeit,Distanz_cm,Temp_C,Feuchte_%")

last_dht_t = last_us_t = last_print_t = -999.0
last_colon_t = 0.0
colon_on = False

temp_c = hum = dist = None

while True:
    now = time.monotonic()

    # Doppelpunkt blinken
    if now - last_colon_t >= COLON_PERIOD:
        colon_on = not colon_on
        try:
            display.set_colon(colon_on)
        except Exception:
            pass
        last_colon_t = now

    # Ultraschall
    if now - last_us_t >= US_INTERVAL:
        try:
            dist = sonar.measure_in_centimeters()
        except Exception:
            dist = None
        last_us_t = now

    # DHT11
    if now - last_dht_t >= DHT_INTERVAL:
        try:
            t = dht.temperature
            h = dht.humidity
            temp_c = float(t) if t is not None else None
            hum    = float(h) if h is not None else None
        except Exception:
            temp_c = hum = None
        color_for_temp(temp_c)
        show_temp_on_display(temp_c)
        last_dht_t = now

    # Serielle CSV-Zeile
    if now - last_print_t >= PRINT_INTERVAL:
        ts = time.localtime()
        dist_v = -1.0 if dist   is None else float(dist)
        temp_v = -1.0 if temp_c is None else float(temp_c)
        hum_v  = -1.0 if hum    is None else float(hum)
        light_raw = light_sensor.value
        light_pct = (light_raw / 65535.0) * 100.0
        line = "{:02d}:{:02d}:{:02d},{:.1f},{:.1f},{:.1f},{:.1f}".format(
            ts.tm_hour, ts.tm_min, ts.tm_sec, dist_v, temp_v, hum_v, light_pct
        )
        print(line)
        last_print_t = now

    time.sleep(0.01)
