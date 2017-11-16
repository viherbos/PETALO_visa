import visa
import pyvisa
import time
from PyQt5 import QtCore, QtWidgets, uic




rm = visa.ResourceManager('@py')
#A=rm.list_resources()
inst = rm.open_resource('USB0::1510::8752::9030149::0::INSTR')
inst.timeout = 3000
# Keithley 2230
#identity = inst.query("*IDN?")
#status  = inst.query_ascii_values('STATUS:OPER?')
inst.write('SYST:REM')
inst.write('*CLS')
inst.write('*ESE 0')

print inst.query("*IDN?")
inst.write("INSTrument:COMbine:PARAllel")
inst.write("VOLTage 12V")
inst.write("CURRent 1.5A")
print inst.query("INSTrument:COMbine?")
inst.write("INSTrument:SELect PARAllel")
inst.write("OUTPUT ON")

inst.write("INSTrument:SELect CH1")
current = inst.query('MEASure:CURRent?')
voltage = inst.query('MEASure:VOLTage?')
print ("Corriente: %s" % current)
print ("Voltaje: %s" % voltage)
inst.write("INSTrument:SELect CH2")
current = inst.query('MEASure:CURRent?')
voltage = inst.query('MEASure:VOLTage?')
print ("Corriente: %s" % current)
print ("Voltaje: %s" % voltage)


time.sleep(5)

inst.write("OUTPUT OFF")


current = inst.query('MEASure:CURRent?')
voltage = inst.query('MEASure:VOLTage?')
print ("Corriente: %s" % current)
print ("Voltaje: %s" % voltage)




#print inst.write("APPLY CH1,5V,1.5A")
#print inst.write("OUTPut:ENABle 1")
#print inst.write("OUTPUT ON")
