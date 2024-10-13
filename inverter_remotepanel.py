import time
import paho.mqtt.client as mqtt

class RemotePanel:
    def __init__(self, broker_address, topic):
        self.broker_address = broker_address
        self.topic = topic
        self.client = mqtt.Client()
        self.running = False
        self.database = None

        def connect(self):
        self.client.connect(self.broker_address)

        def send_data(self, data):
        self.client.publish(self.topic, data)

        def start_loop(self, data_generator, interval):
        self.running = True
        try:
            while self.running:
            data = data_generator(self.database)
            self.send_data(data)
            time.sleep(interval)
        except KeyboardInterrupt:
            print("Stopping periodic data sending.")

        def stop_loop(self):
        self.running = False

        def disconnect(self):
        self.client.disconnect()

        def set_database(self, database):
        self.database = database

    # Example usage:
    # def generate_data(database):
    #     # Replace with your data generation logic from the database
    #     return database.get_data()
    #
    # panel = RemotePanel("broker.hivemq.com", "inverter/data")
    # panel.set_database(your_database_instance)  # Set your NoSQL database instance here
    # panel.connect()
    # panel.start_loop(generate_data, 5)  # Sends data every 5 seconds
    # panel.stop_loop()
    # panel.disconnect()