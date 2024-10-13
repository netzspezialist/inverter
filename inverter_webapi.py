from flask import Flask, jsonify, request
from datetime import datetime
from inverter_commands import InverterCommands
from inverter_bms_state import BMSStateManager

class InverterWebAPI(Flask):
    def __init__(self, logger, inverterCommands : InverterCommands, bmsStateManager : BMSStateManager): 
        # Initialize your class here
        self.logger = logger
        self.inverterCommands = inverterCommands
        self.bmsStateManager = bmsStateManager

        super().__init__(__name__)

        self.add_url_rule('/api/status', 'get_inverter_status', self.get_inverter_status, methods=['GET'])
        self.add_url_rule('/api/settings', 'get_inverter_settings', self.get_inverter_settings, methods=['GET'])
        self.add_url_rule('/api/settings', 'patch_inverter_settings', self.patch_inverter_settings, methods=['PATCH'])
        self.add_url_rule('/api/energy', 'get_inverter_energy', self.get_inverter_energy, methods=['GET'])
        self.add_url_rule('/api/bms', 'put_bms_state', self.put_bms_state, methods=['put'])
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
        dataInput = self.inverterCommands.qet()
        dataOutput = self.inverterCommands.qlt()
        data = { 
            "command": "energy", 
            "timestamp": dataInput["timestamp"].isoformat()[:-3], 
            "totalInput": dataInput["totalGenerated"],
            "totalOutput": dataOutput["totalOutput"]
        }        
        self.logger.info(f'Inverter data: {data}')
        return jsonify(data)
    
    def put_bms_state(self):
        self.logger.info('set bms status ...')
        data = request.get_json()
        self.logger.info(f'BMS data: {data}')
        
        # Set the BMS state
        self.bmsStateManager.set_bms_state(data)


    