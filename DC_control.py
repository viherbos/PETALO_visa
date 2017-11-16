#!/opt/anaconda/anaconda2/bin/python

import visa
import pyvisa
import time
import config_visa
import sys
from PyQt5 import QtCore, QtWidgets, uic
from threading import Thread, Event, RLock
from Queue import Queue, Empty


qtCreatorFile = "DC_control.ui" # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class DATA():
    def __init__(self):
        self.dv = config_visa.DATA(read=True)
        self.d  = { 'CH1V':self.dv.visa_cfg['CH1V'],
                    'CH2V':self.dv.visa_cfg['CH2V'],
                    'CH1A':self.dv.visa_cfg['CH1A'],
                    'CH2A':self.dv.visa_cfg['CH2A'],
                    'paral_ind':self.dv.visa_cfg['paral_ind']
                  }
        self.dr = { 'CH1V_r':0,
                    'CH2V_r':0,
                    'CH1A_r':0,
                    'CH2A_r':0,
                    }
        self.VI_ADDRESS = 'USB0::1510::8752::9030149::0::INSTR'


class read_VI(Thread):
    def __init__(self,upper_class,stopper,lock):
        super(read_VI,self).__init__()
        self.stopper = stopper
        self.uc = upper_class
        self.lock = lock
        # Lock is not really needed but looks fancy

    def run(self):
        while not self.stopper.is_set():
            with self.lock:
                if self.uc.sh_DATA.d['paral_ind']:
                    voltage,current=self.uc.VI.read_PARAL()
                    self.uc.sh_DATA.dr['CH1V_r']=voltage
                    self.uc.sh_DATA.dr['CH1A_r']=current
                    self.uc.sh_DATA.dr['CH2V_r']=0
                    self.uc.sh_DATA.dr['CH2A_r']=0
                else:
                    voltage,current=self.uc.VI.read_CH1_CH2()
                    self.uc.sh_DATA.dr['CH1V_r']=voltage['1']
                    self.uc.sh_DATA.dr['CH1A_r']=current['1']
                    self.uc.sh_DATA.dr['CH2V_r']=voltage['2']
                    self.uc.sh_DATA.dr['CH2A_r']=current['2']
            time.sleep(0.5)

class UPDATE_LCD(Thread):
    def __init__(self,upper_class,stopper,lock):
        super(UPDATE_LCD,self).__init__()
        self.stopper = stopper
        self.uc = upper_class
        self.lock = lock

    def run(self):
        while not self.stopper.is_set():
            with self.lock:
                # print ("voltage1 = %f" % self.uc.sh_DATA.dr['CH1V_r'])
                # print ("current1 = %f" % self.uc.sh_DATA.dr['CH1A_r'])
                # print ("voltage2 = %f" % self.uc.sh_DATA.dr['CH2V_r'])
                # print ("current2 = %f" % self.uc.sh_DATA.dr['CH2A_r'])
                self.uc.lcd_CH1V.display(self.uc.sh_DATA.dr['CH1V_r'])
                self.uc.lcd_CH2V.display(self.uc.sh_DATA.dr['CH2V_r'])
                self.uc.lcd_CH1A.display(self.uc.sh_DATA.dr['CH1A_r'])
                self.uc.lcd_CH2A.display(self.uc.sh_DATA.dr['CH2A_r'])
                QtWidgets.qApp.processEvents()
            time.sleep(0.1)


class BUTTONS():
    def __init__(self,upper_class):
        self.uc = upper_class

    def float_v(self,number):
        try:
            return float(number)
        except ValueError:
            return 0.0

    def int_v(self,number):
        try:
            return int(number)
        except ValueError:
            return 0
    # Controlled Casting


    def switch_on(self):
        self.data_update()
        if self.uc.sh_DATA.d['paral_ind']:
            self.uc.lcd_CH2V.setEnabled(False)
            self.uc.lcd_CH2A.setEnabled(False)
            self.uc.VI.write_PARAL()
        else:
            self.uc.lcd_CH2V.setEnabled(True)
            self.uc.lcd_CH2A.setEnabled(True)
            self.uc.VI.write_CH1_CH2()
        time.sleep(0.5)
        self.uc.VI.ON()

    def switch_off(self):
        self.uc.VI.OFF()

    def data_update(self):
        # Update Internal variables
        self.uc.sh_DATA.d['CH1V'] = self.float_v(self.uc.sb_CH1V.value())
        self.uc.sh_DATA.d['CH2V'] = self.float_v(self.uc.sb_CH2V.value())
        self.uc.sh_DATA.d['CH1A'] = self.float_v(self.uc.sb_CH1A.value())
        self.uc.sh_DATA.d['CH2A'] = self.float_v(self.uc.sb_CH2A.value())
        self.uc.sh_DATA.d['paral_ind'] = self.uc.rbut_parall.isChecked()

        # Update GUI State
        if self.uc.sh_DATA.d['paral_ind']:
            self.uc.sb_CH1A.setMaximum(3.0)
        else:
            self.uc.sb_CH1A.setMaximum(1.5)
            if self.uc.sh_DATA.d['CH1A']>1.5:
                self.uc.sh_DATA.d['CH1A']=1.5
                self.uc.sb_CH1A.setValue(1.5)

    def discard(self):
        # Update Internal variables
        self.uc.sb_CH1V.setValue(self.uc.sh_DATA.d['CH1V'])
        self.uc.sb_CH2V.setValue(self.uc.sh_DATA.d['CH2V'])
        self.uc.sb_CH1A.setValue(self.uc.sh_DATA.d['CH1A'])
        self.uc.sb_CH2A.setValue(self.uc.sh_DATA.d['CH2A'])
        if self.uc.sh_DATA.d['paral_ind']==True:
            self.uc.rbut_parall.setChecked(True)
            self.uc.rbut_ind.setChecked(False)
            self.uc.lcd_CH2V.setEnabled(False)
            self.uc.lcd_CH2A.setEnabled(False)
            #self.VI.write_PARAL()
        else:
            self.uc.rbut_parall.setChecked(False)
            self.uc.rbut_ind.setChecked(True)
            self.uc.lcd_CH2V.setEnabled(True)
            self.uc.lcd_CH2A.setEnabled(True)

        # Update GUI State
        if self.uc.sh_DATA.d['paral_ind']:
            self.uc.sb_CH1A.setMaximum(3.0)
        else:
            self.uc.sb_CH1A.setMaximum(1.5)
            if self.uc.sh_DATA.d['CH1A']>1.5:
                self.uc.sh_DATA.d['CH1A']=1.5
                self.uc.sb_CH1A.setValue(1.5)


    def limits_update(self):
        if self.uc.rbut_parall.isChecked():
            self.uc.sb_CH1A.setMaximum(3.0)
        else:
            self.uc.sb_CH1A.setMaximum(1.5)
            if self.uc.sh_DATA.d['CH1A']>1.5:
                self.uc.sh_DATA.d['CH1A']=1.5
                self.uc.sb_CH1A.setValue(1.5)


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self,stopper):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        #
        self.stopper = stopper
        self.sh_DATA   = DATA()
        self.VI        = config_visa.VISA(self)
        # VISA ADDRESS of USB connected Keithley 2230-30-1
        self.b_buttons = BUTTONS(self)

        # Defaults Loading into GUI and Dumps Config into VI
        # self.b_buttons.switch_off()
        # Switch OFF

        self.sb_CH1V.setValue(self.sh_DATA.d['CH1V'])
        self.sb_CH2V.setValue(self.sh_DATA.d['CH2V'])
        self.sb_CH1A.setValue(self.sh_DATA.d['CH1A'])
        self.sb_CH2A.setValue(self.sh_DATA.d['CH2A'])
        if self.sh_DATA.d['paral_ind']==True:
            self.rbut_parall.setChecked(True)
            self.rbut_ind.setChecked(False)
            self.lcd_CH2V.setEnabled(False)
            self.lcd_CH2A.setEnabled(False)
            #self.VI.write_PARAL()
        else:
            self.rbut_parall.setChecked(False)
            self.rbut_ind.setChecked(True)
            self.lcd_CH2V.setEnabled(True)
            self.lcd_CH2A.setEnabled(True)
            #self.VI.write_CH1_CH2()





        # Button Calls
        self.but_off.clicked.connect(self.b_buttons.switch_off)
        self.but_on.clicked.connect(self.b_buttons.switch_on)
        self.but_discard.clicked.connect(self.b_buttons.discard)

        # Signals
        # self.sb_CH1V.valueChanged.connect(self.b_buttons.data_update)
        # self.sb_CH1A.valueChanged.connect(self.b_buttons.data_update)
        # self.sb_CH2V.valueChanged.connect(self.b_buttons.data_update)
        # self.sb_CH2A.valueChanged.connect(self.b_buttons.data_update)
        self.rbut_parall.clicked.connect(self.b_buttons.limits_update)
        self.rbut_ind.clicked.connect(self.b_buttons.limits_update)

        # Threads for Set / Query through VISA
    def closeEvent(self, event):
        self.stopper.set()
        self.b_buttons.switch_off()
        self.VI.inst.write('SYST:LOC')
        print "Bye bye"


if __name__ == "__main__":
    stopper = Event()
    lock = RLock()

    app = QtWidgets.QApplication(sys.argv)
    window = MyApp(stopper)
    window.show()
    thread_read_VI    = read_VI(window,stopper,lock)
    thread_UPDATE_LCD = UPDATE_LCD(window,stopper,lock)
    thread_read_VI.start()
    thread_UPDATE_LCD.start()

    res=app.exec_()
    thread_read_VI.join()
    thread_UPDATE_LCD.join()

    sys.exit(res)
