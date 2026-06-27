from pyo import *


# Magic Gemini code that calculates human-like formant scaling for a frequency.
def calculate_q(freq, tension_mul=1.0):
    """
    Calculates a natural human-like Q factor
    based on the formant frequency.
    """
    # 1. Calculate natural human bandwidth expansion (with a 50Hz floor)
    bandwidth = 50.0 + (0.05 * freq)

    # 2. Convert to Q factor and apply your global tension modifier
    base_q = freq / bandwidth
    return base_q * tension_mul

    # Example Usage in your parallel bank:
    # f1_q = calculate_q(F1)  --> If F1=500,  Bw=75,  Q ≈ 6.6
    # f3_q = calculate_q(F3)  --> If F3=3000, Bw=200, Q ≈ 15.0


s = Server(duplex=0)
output_select = pa_get_output_devices()
print(output_select)
i = output_select[0].index('Microsoft hangleképző - Output')
out_index = output_select[1][i]
print(out_index)
s.setOutputDevice(out_index)
s.boot().start()

vowels = {
    "ε": [538, 1779, 2751],
    "ɹ": [396, 1850, 2221],
    "a": [808, 1210, 3005],
    "o": [312, 593, 2934],
    "ə": [602, 1219, 2794],
    "i": [450, 2460, 2922],  # i'm trying to imitate a vtuber saying iiiii, I should also TODO try to have the program imitate the vtuber
    "vtuber_i": [450, 3264, 3760]
}

F0 = 119
vowel = "ε"
F1 = vowels[vowel][0]
F2 = vowels[vowel][1]
F3 = vowels[vowel][2]
TENSION = Sig(0)
TENSION.ctrl()
fundamental_sway = ButLP(BrownNoise(), freq=3, mul=3)
FM_jitter = ButLP(BrownNoise(), freq=15, mul=0.15)
vocal_amp_sway = ButLP(BrownNoise(), freq=25, mul=0.03)
vocal = Blit(freq=F0 + fundamental_sway + FM_jitter, harms=80, mul=1 + vocal_amp_sway)
body_12db = ButLP(vocal, 400, mul=1)  # spectral "tilt" (spectral shaping of Blit)
body_6db = Tone(vocal, 400, mul=1)  # spectral "tilt" (spectral shaping of Blit)
body = (body_12db * (1-TENSION)) + (body_6db * TENSION)
body_high = ButHP(vocal, F3, mul=0.01)
tension_middle = ButBP(body, (F1 + F2) / 2, ((F1 + F2) / 2) / (F2 - F1), mul=0)
tension_middle.ctrl()
raw_vocal = body + body_high + tension_middle
vocal_raw = EQ(raw_vocal, F1, 0.5, 0)  # feminine spectral "hill"
vocal_raw.ctrl()
reverbed_vocal = Freeverb(
    vocal_raw,
    size=0.15,    # Very small room size to avoid massive echoes
    damp=0.85,    # Heavily muffle the high frequencies of the reflections
    bal=0.12      # Keep it subtle! Just 12% wet mix to smear the edges
)
vocal = Chorus(
    reverbed_vocal,
    depth=1,
    feedback=0.02,
    bal=0
)
H1_H2_TILT = Sig(0.15, 10)
H1_H2_TILT.ctrl()
f0 = ButLP(
    Reson(vocal, F0 + fundamental_sway, 1, mul=0.5), (F0 + fundamental_sway) * H1_H2_TILT
)  # this thing... it may work
f1 = Reson(vocal, F1, calculate_q(F1), mul=1)  # orig Q: 20
f2 = Reson(vocal, F2, calculate_q(F2), mul=1)  # orig Q: 25
f3 = Reson(vocal, F3, calculate_q(F3), mul=1)  # orig Q: 30
f4fix = Reson(vocal, 4000, calculate_q(4000), mul=0)  # orig Q: 30
noise = Noise()
f0noise = Biquadx(Reson(noise, F0 + fundamental_sway, 5, mul=1), (F0 + fundamental_sway) * 1.5)
f1noise = Reson(noise, F1, 30, mul=0.5)
f2noise = Reson(noise, F2, 40, mul=0.2)
f3noise = Reson(noise, F3, 60, mul=0.025)
sum = (f0 + f1 + f2 + f3 + f4fix) * 20 + (f0noise + f1noise + f2noise + f3noise) * 0.8
reverb_sum = Freeverb(
    sum,
    size=0.15,    # Very small room size to avoid massive echoes
    damp=0.85,    # Heavily muffle the high frequencies of the reflections
    bal=0.12      # Keep it subtle! Just 12% wet mix to smear the edges
)
filtered_sum = Chorus(
    reverb_sum,
    depth=1,
    feedback=0.02,
    bal=0.02
)
filtered_sum.ctrl()

filtered_sum.out(0)
sum2 = filtered_sum * 1
sum2.out(1)

f4fix.ctrl()
Scope([sum, vocal])
analyzer = Spectrum([sum, vocal], size=2**14)
analyzer.setFscaling(True)  # log
analyzer.setLowFreq(0)
analyzer.setHighFreq(10000)
analyzer.setGain(3)
s.gui(locals())