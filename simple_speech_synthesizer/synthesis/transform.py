import pyo

from simple_speech_synthesizer.synthesis import types as this_layer_types

class Synthesizer:

    def __init__(self):
        """
        The Synthesizer audio block.
        It's an enclosed thing that takes in parameter Envelopes (see base/types),
        and returns out audio based on them.
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
        self.s = pyo.Server(**pyo_server_kwargs)
        self.s.deactivateMidi()
        self.s.boot()
        self.s.start()

    def synthesize(self, input: this_layer_types.Input):
        """
        The actual synthesis part.
        :param input: The layer input.
        :return:
        """

        self.s.recordOptions(dur=input.duration, filename=input.output_filepath)

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

        constriction_f0 = pyo.ButLP(pyo.Reson(noise_source, true_F0, 5, mul=0), true_F0 * 1.5)
        constriction_formants = list()
        for freq, q, mul in input.Constriction_formant_freqs, input.Constriction_formant_qs, input.Constriction_formant_muls:
            vowel_formants.append(
                pyo.Resonx(noise_source, freq=freq, q=q, mul=mul, stages=3)
            )

        voiceless_component = constriction_f0 + sum(constriction_formants)
        voiced_component *= input.Voiceless_component_mul

        # FULL SUM

        audio_out = voiced_component + voiceless_component

        #### RECORD
        self.s.recstart()
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
        self.s.gui()


def transform(input: this_layer_types.Input) -> str:
    """
    The final layer in the synthesis stack.
    :param input: This layer's Input.
    :return: The filepath to the output audio.
    """
    s = Synthesizer()
    s.synthesize(input)
    return input.output_filepath