import json
import visa
import time

class JSON_config(object):

    def __init__(self, filename, data=None):
        self.data = data
        self.filename = filename

    def config_write(self):
        writeName = self.filename
        try:
            with open(writeName,'w') as outfile:
                json.dump(self.data, outfile)
        except IOError as e:
            print(e)

    def config_read(self):
        readName = self.filename
        try:
            with open(readName,'r') as infile:
                dict_values = json.load(infile)
                return (dict_values)
        except IOError as e:
            print(e)
            return('None')


class DATA(JSON_config):
    # Only filenames are read. The rest is taken from json file
    def __init__(self,read=True):
        self.config_filename = "visa.json"

        if (read):
            super(DATA, self).__init__(filename=self.config_filename)
            self.visa_cfg = super(DATA,self).config_read()
        else:
            # These are default values.
            self.visa_cfg= {'CH1V':12.0,
                            'CH1A':3.0,
                            'CH2V':5,
                            'CH2A':1.5,
                            'paral_ind':True
                            }

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


if __name__ == "__main__":

    # Generate Configuration File with Defaults
    data = DATA(read=False)
    json_cfg = JSON_config(data.config_filename,
                           data.visa_cfg)
    json_cfg.config_write()