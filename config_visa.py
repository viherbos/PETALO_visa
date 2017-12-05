import json
import visa
import time
import socket as sk
from threading import Thread, Event


class DATA(object):
    # Only filenames are read. The rest is taken from json file
    def __init__(self,read=True):
        self.filename = "visa.json"
        self.visa_cfg=[]

        if (read==True):
            self.config_read()
        else:
            # These are default values.
            self.visa_cfg= {'CH1V':12.0,
                            'CH1A':3.0,
                            'CH2V':5,
                            'CH2A':1.5,
                            'paral_ind':True,
                            'VI_ADDRESS': 'USB0::1510::8752::9030149::0::INSTR',
                            'localhost': '158.42.105.105',
                            'server_port': 5010
                            }
        self.config_write()

    def config_write(self):
        writeName = self.filename
        try:
            with open(writeName,'w') as outfile:
                json.dump(self.visa_cfg, outfile)
        except IOError as e:
            print(e)

    def config_read(self):
        try:
            with open(self.filename,'r') as infile:
                self.visa_cfg = json.load(infile)
        except IOError as e:
            print(e)


class ONOFF_server(Thread):

    def __init__(self,upper_class,stopper):
        self.uc = upper_class
        super(SCK_server,self).__init__()
        self.stopper = stopper
        self.s = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        try:
            self.s.bind((self.uc.sh_DATA.localhost,
                        self.uc.sh_DATA.server_port))
            self.s.listen(5)
        except sk.error as e:
            print ("Server couldn't be opened: %s" % e)
            os._exit(1)


    def run(self):
        while not self.stopper.is_set():
            try:
                self.s.settimeout(5.0)
                self.conn, self.addr = self.s.accept()
            except sk.timeout:
                pass
            else:
                try:
                    self.s.settimeout(5.0)
                    # Ten seconds to receive the data
                    self.data = self.conn.recv(1024)
                except:
                    print ("Data not received by server")
                    pass
                else:
                    # Do whatever you need
                    self.item = json.loads(self.data)
                    if (self.item['command']=="DC"):
                        if (self.item['arg1']=="ON"):
                            self.uc.b_buttons.switch_on()
                        elif (self.item['arg1']=="OFF"):
                            self.uc.b_buttons.switch_off()
                    else:
                        pass

                    self.conn.close()
        self.s.close()
        print ("SERVER SOCKET IS DEAD")



class VISA():
    def __init__(self,upper_class):
        self.uc = upper_class
        self.rm = visa.ResourceManager('@py')
        self.inst = self.rm.open_resource(self.uc.sh_DATA.VI_ADDRESS)
        self.inst.timeout = 3000
        self.current = 0
        self.voltage = 0
        # May be not needed
        self.inst.write('SYST:REM')
        self.inst.write('*CLS')
        self.inst.write('*ESE 0')
        time.sleep(1)
        print self.inst.query("*IDN?")

    def float_v(self,number):
        try:
            return float("{0:.2f}".format(float(number)))
        except ValueError:
            return 0.0

    def wait_VI(self):
        while self.float_v(self.inst.query('*OPC?'))!=1.0:
            print "FALLO OPC"
            time.sleep(0.5)

    def read_CH1_CH2(self):
        self.current={}
        self.voltage={}
        #self.wait_VI()
        self.inst.write("INSTrument:SELect CH1")
        self.current['1'] = self.float_v(self.inst.query('MEASure:CURRent?'))
        self.wait_VI()
        self.voltage['1'] = self.float_v(self.inst.query('MEASure:VOLTage?'))
        self.wait_VI()

        self.inst.write("INSTrument:SELect CH2")
        self.current['2'] = self.float_v(self.inst.query('MEASure:CURRent?'))
        self.wait_VI()
        self.voltage['2'] = self.float_v(self.inst.query('MEASure:VOLTage?'))
        self.wait_VI()

        return self.voltage,self.current

    def read_PARAL(self):
        #self.wait_VI()
        self.inst.write("INSTrument:SELect PARAllel")
        self.current = self.float_v(self.inst.query('MEASure:CURRent?'))
        self.wait_VI()
        self.voltage = self.float_v(self.inst.query('MEASure:VOLTage?'))
        self.wait_VI()
        return self.voltage,self.current

    def write_CH1_CH2(self):
        self.inst.write("INSTrument:COMbine:OFF")
        self.inst.write("INSTrument:SELect CH1")
        message_v = "VOLTage " + str(self.uc.sh_DATA.d['CH1V'])
        message_i = "CURRent " + str(self.uc.sh_DATA.d['CH1A'])
        self.inst.write(message_v)
        self.inst.write(message_i)

        self.inst.write("INSTrument:SELect CH2")
        message_v = "VOLTage " + str(self.uc.sh_DATA.d['CH2V'])
        message_i = "CURRent " + str(self.uc.sh_DATA.d['CH2A'])
        self.inst.write(message_v)
        self.inst.write(message_i)


    def write_PARAL(self):
        self.inst.write("INSTrument:COMbine:PARAllel")
        message_v = "VOLTage " + str(self.uc.sh_DATA.d['CH1V'])
        message_i = "CURRent " + str(self.uc.sh_DATA.d['CH1A'])
        self.inst.write(message_v)
        self.inst.write(message_i)


    def ON(self):
        self.inst.write("OUTPUT ON")

    def OFF(self):
        self.inst.write("OUTPUT OFF")


# if __name__ == "__main__":
#
#     # Generate Configuration File with Defaults
#     data = DATA(read=False)
#     json_cfg = JSON_config(data.config_filename,
#                            data.visa_cfg)
#     json_cfg.config_write()
