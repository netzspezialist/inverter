class InverterResponseConverter(object):
    @staticmethod
    def qpigs(command, timestamp, response1, response2):

        # qpigs  (000.0 00.0 230.1 50.0 0575 0497 007 382 52.30 000 041 0045 00.5 090.5 00.00 00008 00010110 00 00 00051 010
        # qpigs2 (00.9 090.0 00084

        batteryVoltage = float(response1[41:46])

        batteryDischargingCurrent = int(response1[77:82])
        batteryChargingCurrent = int(response1[47:50])

        if batteryDischargingCurrent > 0:
            batteryCurrent = batteryDischargingCurrent * -1
        else:
            batteryCurrent = batteryChargingCurrent

        batteryStateOfCharge = int(response1[51:54])

        outputLoadPercent = int(response1[33:36])
        outputApparentPower = int(response1[23:27])
        outputActivePower = int(response1[28:32])
        
        temperature = int(response1[55:59])
        inputCurrent1 = float(response1[60:64])
        inputVoltage1 = float(response1[65:70])        
        inputPower1 = int(response1[98:103])        

        inputCurrent2 = float(response2[1:5])
        inputVoltage2 = float(response2[6:11])
        inputPower2 = int(response2[12:17])

        inputCurrent = round((inputCurrent1 + inputCurrent2) / 2, 2)
        inputVoltage = round((inputVoltage1 + inputVoltage2) / 2, 2)
        inputPower = float(inputPower1 + inputPower2) + 0.001



        

        data =  {
            "command": command,
            "timestamp": timestamp,#timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), # "2021-09-29T19:00:00.000",
            "batteryVoltage": batteryVoltage,
            "batteryStateOfCharge": batteryStateOfCharge,
            "batteryCurrent": batteryCurrent,
            "outputLoadPercent": outputLoadPercent,
            "outputApparentPower": outputApparentPower,
            "outputActivePower": outputActivePower,
            "inputCurrent": inputCurrent,
            "inputVoltage": inputVoltage,
            "inputPower": inputPower,
            "temperature": temperature
        }

        return data
    
    @staticmethod
    def qpiri(command, timestamp, response):

        batteryRatingVoltage = float(response[38:42])
        batteryReconnectChargingVoltage = float(response[43:47])
        batteryReconnectDischargingVoltage = float(response[87:91])
        batteryUnderVoltage = float(response[48:52])
        batteryBulkVoltage = float(response[53:57])
        batteryFloatVoltage = float(response[58:62])
        batteryMaxChargingCurrent = int(response[68:71])

        data = { 
            "command": command, 
            "timestamp": timestamp, 
            "batteryRatingVoltage": batteryRatingVoltage,
            "batteryReconnectChargingVoltage": batteryReconnectChargingVoltage,
            "batteryReconnectDischargingVoltage": batteryReconnectDischargingVoltage,
            "batteryUnderVoltage": batteryUnderVoltage,
            "batteryBulkVoltage": batteryBulkVoltage,
            "batteryFloatVoltage": batteryFloatVoltage,
            "batteryMaxChargingCurrent": batteryMaxChargingCurrent
        }
        return data
    
    @staticmethod
    def energy(command, timestamp, response, logger = None):

        energy = 0

        if response[1:4] != "NAK":
            try:
                energy = int(response[2:10])    
            except: 
                logger.error(f'Error converting energy value: {response}')    
                energy = 0
        
        data = { 
            "command": command, 
            "timestamp": timestamp, 
            "energy": energy
        }
        return data

    @staticmethod
    def updateSetting(command, timestamp, response):
        data =  {
            "command": command, 
            "timestamp": timestamp,  
            "status": response[1:4]
        }
        return data

    @staticmethod
    def createTimeStamp(startTime, stopTime):
        bmsRequestDuration = stopTime - startTime    
        timestamp = (startTime + ( (bmsRequestDuration) / 2)) 

        return timestamp


        '''
        data = {
            "gridVoltage": response[1:6],
            "gridFrequency": response[7:11],
            "outputVoltage": response[12:17],
            "outputFrequency": response[18:22],
            "outputApparentPower": response[23:27],
            "outputActivePower": response[28:32],
            "outputLoadPercent": response[33:36],
            "busVoltage": response[37:40],
            "batteryVoltage": response[41:46],
            "batteryChargingCurrent": response[47:50],
            "batteryDischargingCurrent": response[77:82],
            "batteryCapacity": response[51:54],
            "inputCurrent1": response[60:64],
            "inputVoltage1": response[65:70],
            "inputPower1": response[98:103],                    
            "batteryVoltageSCC": response[71:76],
            "deviceStatus": response[83:91],
            "temperature": response[55:59]                   
        }
        '''