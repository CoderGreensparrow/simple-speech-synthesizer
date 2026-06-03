from pyo import *

s = Server(duplex=0)
output_select = pa_get_output_devices()
print(output_select)
i = output_select[0].index('Microsoft hangleképző - Output')
out_index = output_select[1][i]
print(out_index)
s.setOutputDevice(out_index)
s.boot().start()

vowels = {
    "ε": [717, 1858, 2879],
    "ɹ": [396, 1850, 2221],
    "a": [808, 1210, 3005],
    "o": [312, 593, 2934],
    "ə": [602, 1219, 2794]
}

F0 = 100
vowel = "ə"
F1 = vowels[vowel][0]
F2 = vowels[vowel][1]
F3 = vowels[vowel][2]
fundamental_sway = ButLP(BrownNoise(), freq=3, mul=3)
FM_jitter = ButLP(BrownNoise(), freq=15, mul=0.15)
vocal_amp_sway = ButLP(BrownNoise(), freq=25, mul=0.03)
vocal = Blit(freq=F0 + fundamental_sway + FM_jitter, harms=80, mul=1 + vocal_amp_sway)
body = ButLP(vocal, 400, mul=1)  # spectral "tilt" (spectral shaping of Blit)
body_high = ButHP(vocal, 3000, mul=0.01)
vocal = body + body_high
f0 = ButLP(Reson(vocal, F0 + fundamental_sway, 1, mul=1), (F0 + fundamental_sway) * 1.5)  # this thing... it may work
f1 = Reson(vocal, F1, 6, mul=0.5)
f2 = Reson(vocal, F2, 8, mul=0.3)
f3 = Reson(vocal, F3, 12, mul=0.1)
noise = Noise()
f0noise = ButLP(Reson(noise, F0 + fundamental_sway, 5, mul=1), (F0 + fundamental_sway) * 1.5)
f1noise = Reson(noise, F1, 30, mul=0.5)
f2noise = Reson(noise, F2, 40, mul=0.2)
f3noise = Reson(noise, F3, 60, mul=0.025)
sum = (f0 + f1 + f2 + f3) * 20 + (f0noise + f1noise + f2noise + f3noise) * 0.8
sum.out(0)
sum2 = sum * 1
sum2.out(1)

Scope([sum, vocal])
analyzer = Spectrum([sum, vocal], size=2**14)
analyzer.setFscaling(True)  # log
analyzer.setLowFreq(0)
analyzer.setHighFreq(10000)
analyzer.setGain(3)
s.gui(locals())