import json, logging, configparser, time
import serial
import paho.mqtt.client as mqtt
import requests

THINGSPEAK_URL = "https://api.thingspeak.com/update"
THINGSPEAK_MIN_INTERVAL = 15  # s

def parse_csv_line(line: str):
    parts = line.strip().split(",")
    if len(parts) < 4:
        return None
    try:
        data = {
            "timestamp":     parts[0],
            "distance_cm":   float(parts[1]),
            "temperature_c": float(parts[2]),
            "humidity_pct":  float(parts[3]),
        }
        if len(parts) >= 5 and parts[4] != "":
            data["light_pct"] = float(parts[4])
        return data
    except ValueError:
        return None

def setup_mqtt(cfg):
    use_ws = cfg.getboolean("MQTT", "use_websockets", fallback=True)
    host   = cfg["MQTT"]["server"]
    port   = cfg.getint("MQTT", "port")
    user   = cfg["MQTT"].get("username", "")
    pw     = cfg["MQTT"].get("password", "")
    transport = "websockets" if use_ws else "tcp"
    client = mqtt.Client(client_id="FeatherBridge", transport=transport)

    if use_ws:
        client.ws_set_options(path="/ws")

    if user:
        client.username_pw_set(user, pw)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.on_connect    = lambda c,u,f,rc: logging.info(f"MQTT connected (rc={rc})")
    client.on_disconnect = lambda c,u,rc: logging.warning(f"MQTT disconnected (rc={rc}) – auto-reconnect läuft…")
    client.connect(host, port, keepalive=60)
    client.loop_start()
    return client

def maybe_send_to_thingspeak(cfg, data, last_sent_ts):
    if not cfg.getboolean("THINGSPEAK", "enabled", fallback=False):
        return last_sent_ts
    if time.monotonic() - last_sent_ts < THINGSPEAK_MIN_INTERVAL:
        return last_sent_ts
    if not cfg.has_section("THINGSPEAK"):
        return last_sent_ts

    api_key = cfg["THINGSPEAK"].get("write_api_key", "").strip()
    if not api_key:
        return last_sent_ts

    f1 = cfg["THINGSPEAK"].get("field1", "temperature_c")
    f2 = cfg["THINGSPEAK"].get("field2", "humidity_pct")
    f3 = cfg["THINGSPEAK"].get("field3", "distance_cm")
    f4 = cfg["THINGSPEAK"].get("field4", "")

    params = {"api_key": api_key}
    if f1 in data: params["field1"] = data[f1]
    if f2 in data: params["field2"] = data[f2]
    if f3 in data: params["field3"] = data[f3]
    if f4 and f4 in data: params["field4"] = data[f4]

    try:
        r = requests.get(THINGSPEAK_URL, params=params, timeout=5)
        if r.status_code == 200 and r.text.strip().isdigit():
            logging.info(f"ThingSpeak update id={r.text.strip()} ok")
            return time.monotonic()
        logging.warning(f"ThingSpeak HTTP {r.status_code}: {r.text}")
    except Exception as e:
        logging.warning(f"ThingSpeak send failed: {e}")
    return last_sent_ts

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    cfg = configparser.ConfigParser()
    cfg.read("configuration.ini")

    topic  = cfg["MQTT"]["topic"]
    qos    = cfg.getint("MQTT", "qos", fallback=0)
    client = setup_mqtt(cfg)

    port = cfg["SERIAL"]["port"]
    baud = cfg.getint("SERIAL", "baudrate", fallback=115200)

    logging.info(f"Open serial {port} @ {baud}")
    last_ts_push = 0.0
    try:
        with serial.Serial(port, baudrate=baud, timeout=2) as ser:
            _ = ser.readline()  # Header verwerfen
            while True:
                raw = ser.readline().decode(errors="ignore").strip()
                if not raw:
                    continue
                data = parse_csv_line(raw)
                if not data:
                    logging.debug(f"skip: {raw}")
                    continue
                payload = json.dumps(data)
                client.publish(topic, payload, qos=qos)
                logging.info(f"MQTT → {topic}: {payload}")
                last_ts_push = maybe_send_to_thingspeak(cfg, data, last_ts_push)
    except KeyboardInterrupt:
        logging.info("Abbruch…")
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass

if __name__ == "__main__":
    main()
