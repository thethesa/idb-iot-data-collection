# idb-iot-data-collection
Dieses Projekt erfasst Umgebungsdaten wie Temperatur, Luftfeuchtigkeit, Distanz und Lichtintensität mithilfe von Sensoren auf einem Adafruit Feather. Die Daten werden über einen Raspberry Pi per MQTT an einen Broker übertragen und direkt  an ThingSpeak gesendet.

## 🔁 Datenflussdiagramm

Feather nRF52840 (Sensoren + LED, code.py)
   ➜  Raspberry Pi (mqtt_idb.py)
   ➜  MQTT Broker
   ➜  ThingSpeak Cloud (HTTP Upload)
   ➜  Dashboard(ThingSpeak(Visualisierung))
