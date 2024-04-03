from binascii import unhexlify
import os
import threading
import time
import crcmod
import serial

from inverter_config import inverter as invertConfig

class InverterConnection:
    def __init__(self, logger=None):
        self.logger = logger
        self.xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')
        self.connected = False
        self.lock = threading.Lock()

        if not os.path.exists(invertConfig.port):
            raise FileNotFoundError('Port not found')

    def open(self):
        try:
            if invertConfig.connectionType == 'serial':
                self.ser = serial.Serial()
                self.ser.port = invertConfig.port                
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
                self.port = os.open('/dev/hidraw0', os.O_RDWR | os.O_NONBLOCK)

            self.connected = True
            self.logger.info('Inverter connection opened')
        except Exception as e:
            self.logger.error(f"error open USB port: {e}")


    def close(self):
        if invertConfig.connectionType == 'serial':
            self.ser.close()
        else:
            os.close(self.port)
        self.connected = False
        self.logger.info('Inverter connection closed')


    def execute(self, command):
        if not self.connected:
            raise ConnectionError('Connect first')
        
        self.logger.debug(f'Inverter execute command {[command]}')

        self.lock.acquire()
        response = self.send_command(command)
        self.lock.release()

        if response is None:
            raise ConnectionError('No response from inverter')

        self.logger.debug(f'Inverter execute response [{response}]')

        return response

    def send_command(self, command):
        encoded_cmd = command.encode('ascii')
        b_cmd = encoded_cmd            
        i_crc = self.xmodem_crc_func(b_cmd)
        h_crc = self.hex2(i_crc)
        self.logger.debug(f'crc hex {h_crc}')
        h_crc = h_crc.replace('0x','',1)
        i_cmd = int.from_bytes(b_cmd, 'big')
        h_cmd = self.hex2(i_cmd)
        self.logger.debug(f'command hex {h_cmd}')
        h_cmd = h_cmd.replace('0x','',1)
        command_crc = h_cmd + h_crc + "0d"
        self.logger.debug(f'command and crc hex {command_crc}')
        command_crc = unhexlify(command_crc)
        
        response = ""
        try:
            if invertConfig.connectionType == 'serial':
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
                if invertConfig.connectionType == 'serial':
                    r = self.ser.read(256)
                else:
                    r = os.read(self.port, 256)
                responseBytes += r
                if  b'\r' in responseBytes:
                    lastResponse = True

            self.logger.debug(f'Inverter response [{responseBytes}]')     
            responseBytes = responseBytes[:responseBytes.index(b'\r') - 2]
            response += responseBytes.decode("ascii")

        except Exception as e:
            self.logger.error(f"error reading inverter - Exception: [{e}] Response: [{response}]")  
            return None

        return response
    
    def hex2(self, n):
        x = '%x' % (n,)
        return ('0' * (len(x) % 2)) + x