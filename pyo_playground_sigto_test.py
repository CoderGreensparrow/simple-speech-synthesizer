"""

THIS IS AN ARCHIVED PLAYGROUND.

It produces a *good* /ε/ sound, therefore it can be used as a baseline.

"""

from pyo import *

"""s = Server().boot().start()

# The `mul` attribute multiplies each sample by its value.
a = Sine(freq=100, mul=0.1)

# The `add` attribute adds an offset to each sample.
# The multiplication is applied before the addition.
b = Sine(freq=100, mul=0.5, add=0.5)

# Using the range(min, max) method allows to automatically
# compute both `mul` and `add` attributes.
c = Sine(freq=100).range(-0.25, 0.5)

# Displays the waveforms
sc = Scope([a, b, c])

s.gui(locals())"""
# range seems nice

"""s = Server().boot()

# Creates a noise source
n = Noise()

# Creates an LFO oscillating +/- 500 around 1000 (filter's frequency)
lfo1 = Sine(freq=0.1, mul=500, add=1000)
# Creates an LFO oscillating between 2 and 8 (filter's Q)
lfo2 = Sine(freq=0.4).range(2, 8)
# Creates a dynamic bandpass filter applied to the noise source
bp1 = ButBP(n, freq=lfo1, q=lfo2).out()

# The LFO object provides more waveforms than just a sine wave

# Creates a ramp oscillating +/- 1000 around 12000 (filter's frequency)
lfo3 = LFO(freq=0.25, type=1, mul=1000, add=1200)
# Creates a square oscillating between 4 and 12 (filter's Q)
lfo4 = LFO(freq=4, type=2).range(4, 12)
# Creates a second dynamic bandpass filter applied to the noise source
bp2 = ButBP(n, freq=lfo3, q=lfo4).out(1)

s.gui(locals())"""  # nice stuff with low freq oscillators

# making an ε

s = Server(duplex=0)
output_select = pa_get_output_devices()
print(output_select)
i = output_select[0].index('Microsoft hangleképző - Output')
out_index = output_select[1][i]
print(out_index)
s.setOutputDevice(out_index)
s.boot().start()

source = Round(Sine(1/0.02, mul=0.5, add=0.5))
risetime = Sig(0.25, mul=0.01)
falltime = Sig(0.25, mul=0.01)
time = Sig(0.25, mul=0.01)
risetime.ctrl()
falltime.ctrl()
time.ctrl()
port = Port(source, risetime=risetime, falltime=falltime)
sigtochain = SigTo(SigTo(SigTo(SigTo(port, time=time), time=time), time=time), time=time)
out = sigtochain

scope = Scope([out, source])
scope.setLength(0.1)
analyzer = Spectrum([out], size=2**14)
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