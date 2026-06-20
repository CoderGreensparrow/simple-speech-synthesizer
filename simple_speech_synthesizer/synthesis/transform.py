import pyo

from simple_speech_synthesizer.synthesis import types as this_layer_types

# This is a bit hacky
class InitializedEnvelopesInput:
    def __init__(self, input: this_layer_types.Input):
        # metaparams
        self.output_filepath = input.output_filepath
        self.duration = input.duration
        # Phoneme synthesis
        self.Vowel_formant_freqs = [pyo.Linseg(freq) for freq in input.Vowel_formant_freqs]
        self.Vowel_formant_qs =    [pyo.Linseg(freq) for freq in input.Vowel_formant_qs]
        self.Vowel_formant_muls =  [pyo.Linseg(freq) for freq in input.Vowel_formant_muls]
        self.Constriction_formant_freqs = [pyo.Linseg(freq) for freq in input.Constriction_formant_freqs]
        self.Constriction_formant_qs =    [pyo.Linseg(freq) for freq in input.Constriction_formant_qs]
        self.Constriction_formant_muls =  [pyo.Linseg(freq) for freq in input.Constriction_formant_muls]
        self.Voiced_component_mul = pyo.Linseg(input.Voiced_component_mul)
        self.Voiceless_component_mul = pyo.Linseg(input.Voiceless_component_mul)
        # Global Envelopes
        self.Volume = pyo.Linseg(input.Volume)
        self.F0 = pyo.Linseg(input.F0)
        self.VocalTiltDelta = pyo.Linseg(input.VocalTiltDelta)
        self.Tension = pyo.Linseg(input.Tension)
        # scalar parameters
        self.F0_freq_sway = input.F0_freq_sway
        self.F0_freq_FM_jitter = input.F0_freq_FM_jitter
        self.voice_source_amp_sway = input.voice_source_amp_sway


def synthesize(input: this_layer_types.Input):
    """
    The actual synthesis part.
    :param input: The layer input.
    :return:
    """

    pyo_server_kwargs = {
        "sr": 48000,
        "nchnls": 2,
        "buffersize": 256,
        "duplex": 0,
        "audio": "offline"
    }
    if pyo_server_kwargs is not None:
        for key, val in pyo_server_kwargs.items():
            pyo_server_kwargs[key] = val
    s = pyo.Server(**pyo_server_kwargs)
    s.deactivateMidi()
    s.boot()
    s.recordOptions(dur=input.duration, filename=input.output_filepath)

    input = InitializedEnvelopesInput(input)

    # voice source + filter

    F0_freq_sway = pyo.ButLP(pyo.BrownNoise(), freq=3, mul=3 * input.F0_freq_sway)
    F0_freq_FM_jitter = pyo.ButLP(pyo.BrownNoise(), freq=15, mul=0.15 * input.F0_freq_FM_jitter)
    true_F0 = input.F0 + F0_freq_sway + F0_freq_FM_jitter

    voice_source_amp_sway = pyo.ButLP(pyo.BrownNoise(), freq=25, mul=0.03 * input.voice_source_amp_sway)

    raw_voice_source = pyo.Blit(freq=true_F0, harms=80, mul=1 + voice_source_amp_sway)
    spectral_tilted_voice_source = pyo.ButLP(raw_voice_source, 400, mul=1)  # spectral "tilt" (spectral shaping of Blit)
    high_freq_retention_voice_source = pyo.ButHP(raw_voice_source, 3000, mul=0.01)
    voice_source = spectral_tilted_voice_source + high_freq_retention_voice_source

    vowel_f0 = pyo.ButLP(
            pyo.Reson(voice_source, true_F0, 1, mul=0.6),
        true_F0 * 1.5)
    vowel_formants = list()
    for freq, q, mul in input.Vowel_formant_freqs, input.Vowel_formant_qs, input.Vowel_formant_muls:
        vowel_formants.append(
            pyo.Reson(voice_source, freq=freq, q=q, mul=mul)
        )

    voiced_component = vowel_f0 + sum(vowel_formants)
    voiced_component *= input.Voiced_component_mul

    # noise source + filter

    noise_source = pyo.Noise()

    constriction_f0 = pyo.ButLP(pyo.Reson(noise_source, true_F0, 5, mul=0), true_F0 * 1.5)  # TODO I have to parametrize F0 too, or change the architecture
    constriction_formants = list()
    for freq, q, mul in input.Constriction_formant_freqs, input.Constriction_formant_qs, input.Constriction_formant_muls:
        vowel_formants.append(
            pyo.Resonx(noise_source, freq=freq, q=q, mul=mul, stages=3)
        )

    voiceless_component = constriction_f0 + sum(constriction_formants)
    voiced_component *= input.Voiceless_component_mul

    # FULL SUM

    audio_out = voiced_component + voiceless_component
    audio_out.out(0)
    audio_out_2 = audio_out * 1
    audio_out_2.out(1)

    #### RECORD
    for env in input.Vowel_formant_freqs: env.play()
    for env in input.Vowel_formant_qs: env.play()
    for env in input.Vowel_formant_muls: env.play()
    for env in input.Constriction_formant_freqs: env.play()
    for env in input.Constriction_formant_qs: env.play()
    for env in input.Constriction_formant_muls: env.play()
    input.Voiced_component_mul.play()
    input.Voiceless_component_mul.play()
    input.Volume.play()
    input.F0.play()
    input.VocalTiltDelta.play()
    input.Tension.play()
    #### TODO !!!: How to properly exit after recording is done

    s.start()
    s.shutdown()

    return input.output_filepath


def transform(input: this_layer_types.Input) -> str:
    """
    The final layer in the synthesis stack.
    :param input: This layer's Input.
    :return: The filepath to the output audio.
    """
    synthesize(input)
    return input.output_filepath










if __name__ == "__main__":
    F0 = 119
    F1 = 538  # praat value; orig 610
    F2 = 1779  # praat value; orig 1900
    F3 = 2751  # praat value
    # parameters adapted from pyo_playground_e.py
    i = this_layer_types.Input(
        output_filepath=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\synthesis\testaudio.wav",
        duration=1.0,
        Vowel_formant_freqs=[[(0, F1), (1, F1)],
                             [(0, F2), (1, F2)],
                             [(0, F3), (1, F3)]],
        Vowel_formant_qs=[[(0, 6), (1, 6)],
                          [(0, 8), (1, 8)],
                          [(0, 12), (1, 12)]],
        Vowel_formant_muls=[[(0, 0.5), (1, 0.5)],
                          [(0, 0.4), (1, 0.4)],
                          [(0, 0.2), (1, 0.2)]],
        Constriction_formant_freqs=[[(0, F1), (1, F1)],
                                    [(0, F2), (1, F2)],
                                    [(0, F3), (1, F3)]],
        Constriction_formant_qs=[[(0, 30), (1, 30)],
                                 [(0, 40), (1, 40)],
                                 [(0, 60), (1, 60)]],
        Constriction_formant_muls=[[(0, 0.5), (1, 0.5)],
                                   [(0, 0.2), (1, 0.2)],
                                   [(0, 0.025), (1, 0.025)]],
        Voiced_component_mul=[(0, 20), (1, 20)],
        Voiceless_component_mul=[(0, 0.8), (1, 0.8)],
        Volume=[(0, 1), (1, 1)],  # TODO have this effect the volume
        F0=[(0, F0), (1, F0)],
        F0_freq_sway=1,
        F0_freq_FM_jitter=1,
        voice_source_amp_sway=1,
        VocalTiltDelta=[(0, 1), (1, 1)],
        Tension=[(0, 1), (1, 1)]
    )
    o = transform(i)