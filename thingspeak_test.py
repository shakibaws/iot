from ThingSpeak.publisher import ThingSpeakPublisher
from ThingSpeak.listener import ThingSpeakListener


def custom_on_message(topic, message):
    print(f"Custom handler received message on topic {topic}: {message}")


listener = ThingSpeakListener()
listener.start_listening(custom_on_message)
publisher = ThingSpeakPublisher()
publisher.publish(soil_moisture=1, light_level=1, temperature=34)
listener.stop_listening()
