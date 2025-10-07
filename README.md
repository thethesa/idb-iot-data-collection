# idb-iot-data-collection
Dieses Projekt erfasst Umgebungsdaten wie Temperatur, Luftfeuchtigkeit, Distanz und Lichtintensität mithilfe von Sensoren auf einem Adafruit Feather. Die Daten werden über einen Raspberry Pi per MQTT an einen Broker übertragen und direkt  an ThingSpeak gesendet.

## 📡 Datenfluss – IoT-System (Theresa Ofogo)

Feather nRF52840  (code.py)
│
│  misst: Temperatur 🌡️, Luftfeuchtigkeit 💧, Distanz 📏, Licht 💡
│
▼
Raspberry Pi  (mqtt_idb.py)
│
│  empfängt Sensordaten über Serial (USB)
│  → veröffentlicht Daten via MQTT und HTTP
│
▼
MQTT Broker (test.mosquitto.org)
│
│  dient als Zwischenspeicher für MQTT-Nachrichten
│
▼
ThingSpeak Cloud 🌩️
│
│  empfängt Daten per HTTP-Request
│  → visualisiert Messwerte im Dashboard
│
▼
Visualisierung (Browser-Dashboard)
│
└── Zeigt Live-Daten zu Temperatur, Feuchtigkeit, Distanz, Licht
