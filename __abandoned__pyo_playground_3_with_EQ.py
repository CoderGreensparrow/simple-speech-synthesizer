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
    "ə": [602, 1219, 2794],
    "i": [450, 2460, 2922]  # i'm trying to imitate a vtuber saying iiiii, I should also TODO try to have the program imitate the vtuber
}

F0 = 407
vowel = "i"
F1 = vowels[vowel][0]
F2 = vowels[vowel][1]
F3 = vowels[vowel][2]
TENSION = Sig(0)
TENSION.ctrl()
fundamental_sway = ButLP(BrownNoise(), freq=3, mul=3)
FM_jitter = ButLP(BrownNoise(), freq=15, mul=0.15)
vocal_amp_sway = ButLP(BrownNoise(), freq=25, mul=0.03)
vocal = Blit(freq=F0 + fundamental_sway + FM_jitter, harms=70, mul=1 + vocal_amp_sway)
body_48db = ButLP(ButLP(vocal, 400, mul=1), 400, 1)  # spectral "tilt" (spectral shaping of Blit)
body_6db = Tone(vocal, 400, mul=1)  # spectral "tilt" (spectral shaping of Blit)
body = (body_48db * (1-TENSION)) + (body_6db * TENSION)
formant_source = EQ(vocal, F3, q=0.5, boost=8, mul=0.001)
formant_source.ctrl()
formant_source_reverb = Freeverb(
    formant_source,
    size=0.15,    # Very small room size to avoid massive echoes
    damp=0.85,    # Heavily muffle the high frequencies of the reflections
    bal=0.12      # Keep it subtle! Just 12% wet mix to smear the edges
)
formant_source_filtered = Chorus(
    formant_source_reverb,
    depth=1,
    feedback=0.1,
    bal=0.1
)
"""tension_middle = ButBP(body, (F1 + F2) / 2, ((F1 + F2) / 2) / (F2 - F1), mul=0)
tension_middle.ctrl()"""  # for masculine vocals, introduces lower speactral energy, but technically I have to do this some other way LOL
f0 = EQ(formant_source_filtered, F0 + fundamental_sway, 20, boost=30)  # this thing... it may work
f0_h2 = EQ(f0, (F0 + fundamental_sway) * 2, 20, boost=20)  # this thing... it may work
f1 = EQ(f0_h2, F1, 20, boost=16)
f2 = EQ(f1, F2, 25, boost=16)
f3 = EQ(f2, F3, 30, boost=16)
f4fix = EQ(f3, 4000, 30, boost=16)
noise = Noise()
f0noise = ButLP(Reson(noise, F0 + fundamental_sway, 5, mul=1), (F0 + fundamental_sway) * 1.5)
f1noise = Reson(noise, F1, 30, mul=0.5)
f2noise = Reson(noise, F2, 40, mul=0.2)
f3noise = Reson(noise, F3, 60, mul=0.025)
sum = (f0 + f4fix) * 20 + (f0noise + f1noise + f2noise + f3noise) * 0.02
reverb_sum = Freeverb(
    sum,
    size=0.15,    # Very small room size to avoid massive echoes
    damp=0.85,    # Heavily muffle the high frequencies of the reflections
    bal=0.12      # Keep it subtle! Just 12% wet mix to smear the edges
)
filtered_sum = Chorus(
    reverb_sum,
    depth=1,
    feedback=0.1,
    bal=0.1
)

COMPARATOR = Sig(1)
COMPARATOR.ctrl()
comparison_sum = (sum * COMPARATOR) + (filtered_sum * (1-COMPARATOR))

comparison_sum.out(0)
sum2 = comparison_sum * 1
sum2.out(1)

f4fix.ctrl()
Scope([sum, vocal])
analyzer = Spectrum([sum], size=2**14)
analyzer.setFscaling(True)  # log
analyzer.setLowFreq(0)
analyzer.setHighFreq(10000)
analyzer.setGain(3)
s.gui(locals())