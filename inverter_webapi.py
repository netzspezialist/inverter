from flask import Flask, jsonify, request
from datetime import datetime
from inverter_commands import InverterCommands
from inverter_monitor import InverterMonitor
from inverter_remotepanel import InverterRemotePanel

class InverterWebAPI(Flask):
    def __init__(self, logger, inverterCommands: InverterCommands, inverterMonitor: InverterMonitor = None, inverterRemotePanel: InverterRemotePanel = None): 
        # Initialize your class here
        self.logger = logger
        self.inverterCommands = inverterCommands
        self.inverterMonitor = inverterMonitor
        self.inverterRemotePanel = inverterRemotePanel

        super().__init__(__name__)

        self.add_url_rule('/api/status', 'get_inverter_status', self.get_inverter_status, methods=['GET'])
        self.add_url_rule('/api/settings', 'get_inverter_settings', self.get_inverter_settings, methods=['GET'])
        self.add_url_rule('/api/bms', 'get_bms_data', self.get_bms_data, methods=['GET'])
        self.add_url_rule('/api/settings', 'patch_inverter_settings', self.patch_inverter_settings, methods=['PATCH'])
        self.add_url_rule('/api/energy', 'get_inverter_energy', self.get_inverter_energy, methods=['POST'])
        self.add_url_rule('/api/monitor', 'get_monitor_data', self.get_monitor_data, methods=['GET'])
        self.add_url_rule('/api/energy', 'get_remote_panel_data', self.get_remote_panel_data, methods=['GET'])
        self.json.sort_keys = False

    def start(self):
        # Start your service here
        self.logger.info('Starting inverter API ...')
        self.run(host='0.0.0.0', port=5000)

    def get_inverter_status(self):
        self.logger.info('get inverter qpigs ...')
        data = self.inverterCommands.qpigs()
        self.logger.info(f'Inverter data: {data}')
        data["timestamp"] = data["timestamp"].isoformat()[:-3]
        return jsonify(data)
    
    def get_inverter_settings(self):
        self.logger.info('get inverter qpiri ...')
        data = self.inverterCommands.qpiri()
        self.logger.info(f'Inverter data: {data}')
        data["timestamp"] = data["timestamp"].isoformat()[:-3]
        return jsonify(data)
    
    def get_bms_data(self):
        self.logger.info('get bms data ...')
        data = self.inverterCommands.qbms()
        self.logger.info(f'Inverter data: {data}')
        #data["timestamp"] = data["timestamp"].isoformat()[:-3]
        return data
    
    def patch_inverter_settings(self):
        self.logger.info('set inverter settings ...')
        data = request.get_json()
        self.logger.info(f'Inverter data: {data}')
        settingsName = data["name"]
        settingsValue = str(data["value"])
        responseData = self.inverterCommands.updateSetting(settingsName, settingsValue)
        responseData["timestamp"] = responseData["timestamp"].isoformat()[:-3]
        return jsonify(responseData)
    
    def get_inverter_energy(self):
        self.logger.info('get inverter energy ...')
        data = request.get_json()
        self.logger.info(f'Inverter data: {data}')
        command = data["command"]
        timestamp = data["timestamp"]
        response = self.inverterCommands.energy(command, timestamp)

        data = { 
            "command": "energy", 
            "timestamp": response["timestamp"].isoformat()[:-3], 
            "energy": response["energy"],
        }

        self.logger.info(f'Inverter data: {data}')
        return jsonify(response)

    def get_monitor_data(self):
        self.logger.info('get monitor data ...')
        if self.inverterMonitor is None:
            return jsonify({"error": "monitor_not_available"}), 503
        data = self.inverterMonitor.get_last_qpigs()
        if data is None:
            return jsonify({"error": "monitor_data_not_ready"}), 404
        return jsonify(data)

    def get_remote_panel_data(self):
        self.logger.info('get remote panel data ...')
        if self.inverterRemotePanel is None:
            return jsonify({"error": "remote_panel_not_available"}), 503
        data = self.inverterRemotePanel.get_last_energy_output()
        if data is None:
            return jsonify({"error": "remote_panel_data_not_ready"}), 404
        return jsonify(data)