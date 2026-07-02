"""

THIS IS AN ARCHIVED PLAYGROUND.

It produces a *good* /ε/ sound, therefore it can be used as a baseline.

"""

from pyo import *

# making an ε

s = Server(duplex=0)
output_select = pa_get_output_devices()
print(output_select)
i = output_select[0].index('Microsoft hangleképző - Output')
out_index = output_select[1][i]
print(out_index)
s.setOutputDevice(out_index)
s.boot().start()

source1 = Sine(200)
source2 = Sine(300)
source3 = Sine(400)
source4 = Sine(500)
voice = Sig(0.5, mul=5, add=-1)
voice.ctrl()
selector = Selector([source1, source2, source3, source4], voice=voice)
out = selector * 0.05
out.out(0)
out2 = out * 1
out2.out(1)

scope = Scope([selector])
scope.setLength(0.1)
analyzer = Spectrum([selector], size=2**14)
analyzer.setFscaling(True)  # log
analyzer.setLowFreq(0)
analyzer.setHighFreq(10000)
analyzer.setGain(3)
s.gui(locals())

"""i 	240 	2400 	2160
y 	235 	2100 	1865
e 	390 	2300 	1910
ø 	370 	1900 	1530
ɛ 	610 	1900 	1290
œ 	585 	1710 	1125
a 	850 	1610 	760
ɶ 	820 	1530 	710
ɑ 	750 	940 	190
ɒ 	700 	760 	60
ʌ 	600 	1170 	570
ɔ 	500 	700 	200
ɤ 	460 	1310 	850
o 	360 	640 	280
ɯ 	300 	1390 	1090
u 	250 	595 	345 """