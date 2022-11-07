try:
    import socketserver
except ImportError:
    import SocketServer as socketserver
import socket, threading
import argparse, random, logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
import board
import busio
import time
from thermocouples_reference import thermocouples
import matplotlib.pyplot as plt
i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

THERMO_TYPE = 'K'

#-------Functions you want to call from a SCPI-command----------
#Function for reading out ADS1115 Thermocoupler
def getTemp(thermotype = 'K', ):
    ads = ADS.ADS1115(i2c)
    type = thermocouples[thermotype] #Defines the Type of Thermocoupler used or more precise, the LUT
    #For more information visit: https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15
    chan = AnalogIn(ads, ADS.P0, ADS.P1) #Change ADS.P0 and P1 to the right AnalogIn on the ADS1115
    temp = type.inverse_CmV(chan.voltage*1000, Tref=0) #Converts the voltage to temp
    return "{}".format(temp) #returns temp as String
#

logger = logging.getLogger('scpi-server')
#-----------------------------------------------------

#-------Just leave everything below like it is--------
"""Class for a general TCP Server"""
class CmdTCPServer(socketserver.ThreadingTCPServer):


    #newline character
    newline = '\n'
    daemon_threads = True
    allow_reuse_address = True
    address_family = socket.AF_INET

    class CmdRequestHandler(socketserver.StreamRequestHandler):
        def handle(self):
            if not self.server.lock.acquire(blocking=False):
                self.log(DEBUG, 'Additional cliend tried to connect from {client}')
                return
            self.log(DEBUG, 'Connected to {client}.')
            self.send_reply('Connected to Raspberry Pi')
            try:
                while True:
                    self.single_cmd()
            except Disconnected:
                pass
                self.log(DEBUG, '{client} closed the connection')
            finally:
                self.server.lock.release()
        def read_cmd(self):
            return self.rfile.readline().decode('utf-8').strip()
        def log(self, level, msg, *args, **kwargs):
            if type(level) == str:
                level = getattr(logging, level.upper())
            msg = msg.format(client=self.client_address[0])
            logger.log(level, msg, *args, **kwargs)
        def send_reply(self, reply):
            if type(reply) == str:
                if self.server.newline: reply += self.server.newline
                reply = reply.encode('utf-8')
            self.wfile.write(reply)
        def single_cmd(self):
            cmd = self.read_cmd()
            #self.send_reply(cmd)
            if not cmd: raise Disconnected
            self.log(DEBUG, 'Received a cmd: {}'.format(cmd))
            try:
                reply = self.server.process(cmd)
                if reply is not None:
                    self.send_reply(reply)
            except:
                self.send_reply('ERR')

    def __init__(self, server_address, name=None):
        socketserver.TCPServer.__init__(self, server_address, self.CmdRequestHandler)
        self.lock = threading.Lock()
        self.name = name if name else "{}:{}".format(*server_address)

    def process(self, cmd):
        """
        Leave empty
        """
        raise NotImplemented
#-----------------------------------------------------

#---------Implement Server Stuff here-----------
class SCPIServerExample(CmdTCPServer):
    def getTemp(THERMO_TYPE = 'K', GAIN = 8):
       ads = ADS.ADS1115(i2c)
       type = thermocouples[THERMO_TYPE]
       chan = AnalogIn(ads, ADS.P0, ADS.P1)
       temp = type.inverse_CmV(chan.voltage*1000, Tref=0)
       return "{}".format(temp)

    def process(self, cmd):
        """
        This is the method to process each SCPI command
        received from the client.
        """
        if cmd.startswith('*IDN?'):
            return self.name
        #Examples for different SCPI commands, better implementation with .split() possible
        #and recommended as soon as a larger scale is implemented
        if cmd.startswith('READ:K?'):
            temp = getTemp('K')
            return temp
        if cmd.startswith('READ:C?'):
            temp = getTemp('C')
            return temp
        else:
            return 'unknown cmd'
#--------------------------------------------------------------


#------------Just leave everything below like it is------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5025, help='TCP port to listen to.')
    parser.add_argument('--host', default='::', help='The host / IP address to listen at.')
    parser.add_argument('--loglevel', default='INFO', help='log level',
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'])
    args = parser.parse_args()
    logging.basicConfig(format='%(message)s', level=args.loglevel.upper())
    scpi_server = SCPIServerExample((args.host, args.port))
    try:
        print('Server started...')
        scpi_server.serve_forever()
    except KeyboardInterrupt:
        logger.info('Ctrl-C pressed. Shutting down...')
    scpi_server.server_close()

class Disconnected(Exception): pass

if __name__ == "__main__":
    main()
#-----------------------------------------------------------------
