from pyo import *

# making an s but simpler

s = Server(duplex=0)
output_select = pa_get_output_devices()
print(output_select)
i = output_select[0].index('Microsoft hangleképző - Output')
out_index = output_select[1][i]
print(out_index)
s.setOutputDevice(out_index)
s.boot().start()

F0 = 105
F1 = 6612 # praat value; orig 610
F2 = 11665 # praat value; orig 1900
F3 = 14286 # praat value
fundamental_sway = ButLP(BrownNoise(), freq=3, mul=3)
FM_jitter = ButLP(BrownNoise(), freq=15, mul=0.15)
vocal_amp_sway = ButLP(BrownNoise(), freq=25, mul=0.03)
vocal = Blit(freq=F0 + fundamental_sway + FM_jitter, harms=80, mul=1 + vocal_amp_sway)
body = ButLP(vocal, 400, mul=1)  # spectral "tilt" (spectral shaping of Blit)
body_high = ButHP(vocal, 3000, mul=0.01)
vocal = body + body_high
f0 = ButLP(Reson(vocal, F0 + fundamental_sway, 1, mul=0.6), (F0 + fundamental_sway) * 1.5)  # this thing... it may work
f1 = Reson(vocal, F1, 6, mul=0.5)                 # originally mul=0.6 above wasn't there
f2 = Reson(vocal, F2, 8, mul=0.4)  # orig: 0.3
f3 = Reson(vocal, F3, 12, mul=0.2)  # orig: 0.1
noise = Noise()
f0noise = ButLP(Reson(noise, F0 + fundamental_sway, 5, mul=0), (F0 + fundamental_sway) * 1.5)
random_high_noise_for_realism = ButHP(noise, 1700, mul=0.05)
f1noise = Resonx(noise, F1, 3, mul=0.5, stages=3)
f2noise = Resonx(noise, F2, 4, mul=0.5, stages=3)
f3noise = Resonx(noise, F3, 6, mul=0.3, stages=3)

hp_filter = ButHP(noise, 1700, mul=0.2)
peak = EQ(hp_filter, 3300, q=3300/1000, boost=26)
peak_2 = EQ(peak, 3300 * 2, q=3300/1000/2, boost=15)
lp_filter = MoogLP(peak_2, 14500)

#  sum = (f0 + f1 + f2 + f3) * 0 + (f0noise + f1noise + f2noise + f3noise + random_high_noise_for_realism) * 0.8
sum = lp_filter * 0.1
sum.out(0)
sum2 = sum * 1
sum2.out(1)

f1noise.ctrl()
f2noise.ctrl()
f3noise.ctrl()
random_high_noise_for_realism.ctrl()

Scope([sum, vocal])
analyzer = Spectrum([sum, vocal], size=2**14)
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