from binascii import unhexlify
import os
import threading
import time
import crcmod
import serial

from inverter_config import inverter as inverterConfig

class InverterConnection:
    def __init__(self, logger=None):
        self.logger = logger
        self.xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')
        self.lock = threading.Lock()

        self.connectionType = inverterConfig["connectionType"]        
        self.port = inverterConfig["port"]
    
        if not os.path.exists(self.port):
            raise FileNotFoundError('Port not found')

    def __open(self):
        try:
            if self.connectionType == 'serial':
                self.logger.debug('Opening inverter connection serial port')    
                self.ser = serial.Serial()
                self.ser.port = self.port                
                self.ser.baudrate = 2400
                self.ser.bytesize = serial.EIGHTBITS     #number of bits per bytes
                self.ser.parity = serial.PARITY_NONE     #set parity check: no parity
                self.ser.stopbits = serial.STOPBITS_ONE  #number of stop bits
                self.ser.timeout = 1                     #non-block read
                self.ser.xonxoff = False                 #disable software flow control
                self.ser.rtscts = False                  #disable hardware (RTS/CTS) flow control
                self.ser.dsrdtr = False                  #disable hardware (DSR/DTR) flow control
                self.ser.writeTimeout = 2                #timeout for write

                self.ser.open()
            else:
                self.logger.debug('Opening inverter connection USB port')    
                self.usb.port = os.open(self.usb.port, os.O_RDWR | os.O_NONBLOCK)

            self.logger.debug('Inverter connection opened')
        except Exception as e:
            self.logger.error(f"error open USB port: {e}")


    def __close(self):
        if self.connectionType == 'serial':
            self.ser.close()
        else:
            os.close(self.port)
        self.connected = False
        self.logger.debug('Inverter connection closed')

    def __send_command(self, command):
        encoded_cmd = command.encode('ascii')
        b_cmd = encoded_cmd            
        i_crc = self.xmodem_crc_func(b_cmd)
        h_crc = self.__hex2(i_crc)
        self.logger.debug(f'crc hex {h_crc}')
        h_crc = h_crc.replace('0x','',1)
        i_cmd = int.from_bytes(b_cmd, 'big')
        h_cmd = self.__hex2(i_cmd)
        self.logger.debug(f'command hex {h_cmd}')
        h_cmd = h_cmd.replace('0x','',1)
        command_crc = h_cmd + h_crc + "0d"
        self.logger.debug(f'command and crc hex {command_crc}')
        command_crc = unhexlify(command_crc)
        
        response = ""
        try:
            if self.connectionType == 'serial':
                time.sleep (0.05)
                self.ser.write(command_crc)
            else:
                if len (command_crc) < 9:
                    os.write(self.port, command_crc)
                else:
                    cmd1 = command_crc[:8]
                    cmd2 = command_crc[8:]
                    os.write(self.port, cmd1)
                    time.sleep (0.05)
                    os.write(self.port, cmd2)

            responseBytes = b''
            lastResponse = False
            while lastResponse == False:
                time.sleep (0.05)
                if self.connectionType == 'serial':
                    r = self.ser.read(256)
                else:
                    r = os.read(self.usb.port, 256)
                responseBytes += r
                if  b'\r' in responseBytes:
                    lastResponse = True
                if len(r) == 0:
                    return None

            self.logger.debug(f'Inverter response [{responseBytes}]')     
            responseBytes = responseBytes[:responseBytes.index(b'\r') - 2]
            response += responseBytes.decode("ascii")

        except Exception as e:
            self.logger.error(f"error reading inverter - Exception: [{e}] Response: [{response}]")  
            return None

        return response
    
    def __hex2(self, n):
        x = '%x' % (n,)
        return ('0' * (len(x) % 2)) + x
    
    def execute(self, command):
        with self.lock:
            self.logger.debug(f'Inverter execute command {[command]}')    
            self.__open()
            response = self.__send_command(command)
            self.__close()

            if response is None:
                self.logger.error('No response from inverter')
                raise ConnectionError('No response from inverter')

            self.logger.debug(f'Inverter execute response [{response}]')

            return response