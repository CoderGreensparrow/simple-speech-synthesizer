import pyo

from simple_speech_synthesizer.synthesis import synthesis_types as this_layer_types
from simple_speech_synthesizer.base.load_low_level_character import load_low_level_character

from time import sleep

_DEBUG = False

# This is a bit hacky, the reason I have to convert them to a pyo object here is because
# pyo doesn't allow the creation of pyo objects unless a server is launched already
class InitializedEnvelopesInput:
    def __init__(self, input: this_layer_types.Input):
        # metaparams
        self.character_dir_path = input.character_dir_path
        self.output_filepath = input.output_filepath
        self.duration = input.duration
        # Phoneme synthesis
        self.Vowel_formant_freqs = [pyo.Linseg(raw_env) for raw_env in input.Vowel_formant_freqs]
        self.Constriction_formant_freqs = [pyo.Linseg(raw_env) for raw_env in input.Constriction_formant_freqs]
        self.Constriction_formant_bandwidths = [pyo.Linseg(raw_env) for raw_env in input.Constriction_formant_bandwidths]
        self.Constriction_formant_muls =  [pyo.Linseg(raw_env) for raw_env in input.Constriction_formant_muls]
        self.Voiced_component_importance = pyo.Linseg(input.Voiced_component_importance)
        """
        importance means semantic amplitude, 1 means full power, 0 means None.
        """
        self.Voiceless_component_importance = pyo.Linseg(input.Voiceless_component_importance)
        # Global Envelopes
        self.Volume = pyo.Linseg(input.Volume)
        """The amplitude of the voice_source in decibels, as per the convention in audio processing.
        So 0 dB is the largest.
        -6 dB is half of that.
        -20 dB is a tenth etc."""
        self.F0 = pyo.Linseg(input.F0)
        ### VOWEL STUFFS
        self.Spectral_tilt_cutoff_delta = pyo.Linseg(input.Spectral_tilt_cutoff_delta)
        """Also called vocal tilt.
        Controls the cutoff point, adjusted from a character-specific default cutoff point, for the vocal tilt filters (ButLP-Tone crossfade)"""
        self.Spectral_tilt_tension = pyo.Linseg(input.Spectral_tilt_tension)
        """Controls the TENSION, the crossfade between the ButLP and the Tone filters. (-12 db/octave cutoff vs -6 db/octave)
        Default is 0, which means no tension."""
        #  self.Spectral_hill_freq_deltafactor = pyo.Linseg(input.Spectral_hill_freq_deltafactor)
        """Shifts the default spectral hill frequency, by multiplying it (being a factor).
        The spectral hill refers to a modification of the descent of the vocal tilt.
        It allows for brighter and anime-like, or lower and masculine formants.
        When applied to the top of the vocal tilt, it reverses some of its effects, effectively flatting out the voice source spectrum in the highs."""
        self.Spectral_hill_boost_delta = pyo.Linseg(input.Spectral_hill_boost_delta)
        self.Vowel_Q_tension_deltafactor = pyo.Linseg(input.Vowel_Q_tension_deltafactor)
        """
        A multiplier for all the Q values of all formants.
        """
        ### CONSONANT STUFFS (none yet)
        # scalar parameters
        self.F0_freq_sway = input.F0_freq_sway
        self.F0_freq_FM_jitter = input.F0_freq_FM_jitter
        self.voice_source_amp_sway = input.voice_source_amp_sway


# Gemini code that calculates human-like formant scaling for a frequency.
def calculate_q(freq, floor=50.0, slope=0.05):
    """
    Calculates a natural human-like Q factor
    based on the formant frequency.
    TENSION IS NOT MULTIPLIED HERE.
    """
    # 1. Calculate natural human bandwidth expansion (with a 50Hz default floor)
    bandwidth = floor + (slope * freq)

    # 2. Convert to Q factor and apply your global tension modifier
    base_q = freq / bandwidth
    return base_q

    # Example Usage in your parallel bank:
    # f1_q = calculate_q(F1)  --> If F1=500,  Bw=75,  Q ≈ 6.6
    # f3_q = calculate_q(F3)  --> If F3=3000, Bw=200, Q ≈ 15.0


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
        "audio": "offline" if not _DEBUG else "portaudio"
    }
    s = pyo.Server(**pyo_server_kwargs)
    s.deactivateMidi()
    s.boot()
    s.recordOptions(dur=input.duration, filename=input.output_filepath)

    input = InitializedEnvelopesInput(input)
    synthesis_parameters = load_low_level_character(input.character_dir_path).synthesis_parameters

    ### VOICE SOURCE
    F0_freq_sway = pyo.ButLP(pyo.BrownNoise(), freq=3, mul=3 * input.F0_freq_sway)
    F0_freq_FM_jitter = pyo.ButLP(pyo.BrownNoise(), freq=15, mul=0.15 * input.F0_freq_FM_jitter)
    true_F0 = input.F0 + F0_freq_sway + F0_freq_FM_jitter

    voice_source_amp_sway = pyo.ButLP(pyo.BrownNoise(), freq=25, mul=0.03 * input.voice_source_amp_sway)

    raw_blit_source = pyo.Blit(freq=true_F0, harms=70, mul=1 + voice_source_amp_sway)
    spectral_tilted_6db_rolloff_blit_source = pyo.Tone(raw_blit_source, synthesis_parameters["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)
    spectral_tilted_12db_rolloff_blit_source = pyo.ButLP(raw_blit_source, synthesis_parameters["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)
    spectral_tilted_blit_source = (spectral_tilted_12db_rolloff_blit_source * (1-input.Spectral_tilt_tension)) + (spectral_tilted_6db_rolloff_blit_source * input.Spectral_tilt_tension)
    high_freq_retention_blit_source = pyo.ButHP(raw_blit_source, 3000, mul=0.005)
    partial_voice_source = spectral_tilted_blit_source + high_freq_retention_blit_source
    unbalanced_voice_source = pyo.EQ(partial_voice_source,
                                     freq=synthesis_parameters["spectral_hill_freq"],  # SPECTRAL HILL DELTAFACTOR REMOVED
                                     q=synthesis_parameters["spectral_hill_freq"] / synthesis_parameters["spectral_hill_bandwidth"],
                                     # TODO that spectral_hill_bandwidth was just a quick fix, that may not be the best implementation method
                                     boost=synthesis_parameters["spectral_hill_boost"] + input.Spectral_hill_boost_delta)
    amp_multiplier = pyo.DBToA(input.Volume)
    voice_source = pyo.Balance(unbalanced_voice_source, pyo.SineLoop(true_F0, mul=amp_multiplier))

    # TODO potential chorus effect could be applied here for a multiple singers effect

    ### VOICE FILTER
    vowel_f0 = pyo.ButLP(
            pyo.Reson(voice_source, true_F0, 1, mul=synthesis_parameters["FO_mul"]),
        true_F0 * synthesis_parameters["H1_H2_balance"])  # TODO implement H1_H2_balance correctly (there are weird cancelling artifacts...
    vowel_formants = list()
    for j, freq in enumerate(input.Vowel_formant_freqs):
        calculated_freq = freq
        if j == 0:
            calculated_freq = pyo.Max(calculated_freq, true_F0 + synthesis_parameters["F0_F1_min_difference"])
        vowel_formants.append(
            pyo.Reson(voice_source,
                      freq=calculated_freq,
                      q=calculate_q(freq, synthesis_parameters["vowel_Q_floor"], synthesis_parameters["vowel_Q_slope"]) * input.Vowel_Q_tension_deltafactor,
                      mul=1)
        )

    voiced_component = vowel_f0 + sum(vowel_formants)
    voiced_component = voiced_component * input.Voiced_component_importance

    # noise source + filter

    noise_source = pyo.Noise()

    """constriction_f0 = pyo.Biquadx(
        pyo.Reson(noise_source, true_F0, 5, mul=1), true_F0 * synthesis_parameters["H1_H2_balance"]
    )"""  # TODO implement formant constriction, aka. breathiness
    constriction_formants = list()
    for freq, bandwidth, mul in zip(input.Constriction_formant_freqs, input.Constriction_formant_bandwidths, input.Constriction_formant_muls):
        constriction_formants.append(
            pyo.Resonx(noise_source, freq=freq, q=freq / bandwidth, mul=mul, stages=3)
        )

    voiceless_component = sum(constriction_formants)  # + constriction_f0
    voiceless_component = voiceless_component * input.Voiceless_component_importance

    # FULL SUM

    audio_out = voiced_component + voiceless_component
    audio_out.out(0)
    audio_out_2 = audio_out * 1
    audio_out_2.out(1)

    #### RECORD
    for env in input.Vowel_formant_freqs: env.play()
    for env in input.Constriction_formant_freqs: env.play()
    for env in input.Constriction_formant_bandwidths: env.play()
    for env in input.Constriction_formant_muls: env.play()
    input.Voiced_component_importance.play()
    input.Voiceless_component_importance.play()
    input.Volume.play()
    input.F0.play()
    input.Spectral_tilt_cutoff_delta.play()
    input.Spectral_tilt_tension.play()
    #  input.Spectral_hill_freq_deltafactor.play()
    input.Spectral_hill_boost_delta.play()
    input.Vowel_Q_tension_deltafactor.play()

    s.start()
    if _DEBUG:
        pyo.Scope([audio_out])
        analyzer = pyo.Spectrum([audio_out], size=2 ** 14)
        analyzer.setFscaling(True)  # log
        analyzer.setLowFreq(0)
        analyzer.setHighFreq(10000)
        analyzer.setGain(3)
        s.gui(locals())
    else:
        s.shutdown()

    return input.output_filepath

    # TODO: there are still some magic numbers left in the synth (like the F0 multiplier is just... a character trait?
    #       and there are even more things, like how the multiplier of the F0noise is just... 1, and its Q value is fixed...

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
        character_dir_path=r"..\characters\Greensparrow",
        output_filepath=r"testaudio.wav",
        duration=3.0,
        Vowel_formant_freqs=[[(0, F1), (3, F1)],
                             [(0, F2), (3, F2)],
                             [(0, F3), (3, F3)]],
        Constriction_formant_freqs=[[(0, F1), (3, F1)],
                                    [(0, F2), (3, F2)],
                                    [(0, F3), (3, F3)]],
        Constriction_formant_bandwidths=[[(0, 30), (3, 30)],
                                 [(0, 30), (3, 30)],
                                 [(0, 30), (3, 30)]],
        Constriction_formant_muls=[[(0, 0.5), (3, 0.5)],
                                   [(0, 0.2), (3, 0.2)],
                                   [(0, 0.025), (3, 0.025)]],
        Voiced_component_importance=[(0, 1), (3, 1)],
        Voiceless_component_importance=[(0, 0.02), (3, 0.02)],
        Volume=[(0, -12), (3, -12)],  # TODO have this effect the volume
        F0=[(0, F0), (3, F0)],
        F0_freq_sway=1,
        F0_freq_FM_jitter=1,
        voice_source_amp_sway=1,
        Spectral_tilt_cutoff_delta=[(0, 0), (3, 0)],
        Spectral_tilt_tension=[(0, 0), (3, 0)],
        #  Spectral_hill_freq_deltafactor=[(0, 1), (3, 1)],
        Spectral_hill_boost_delta=[(0, 0), (3, 0)],
        Vowel_Q_tension_deltafactor=[(0, 1), (3, 1)]
    )
    o = transform(i)