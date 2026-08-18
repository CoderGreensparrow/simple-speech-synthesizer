import pyo

from simple_speech_synthesizer.synthesis import synthesis_types as this_layer_types
from simple_speech_synthesizer.base.garbage_collection_prevention_helpers import activate_layer_inputs

from simple_speech_synthesizer.base.load_low_level_character import load_low_level_character

from simple_speech_synthesizer.global_debug_vars import _DEBUG_SYNTHESIS, _DEBUG_SYNTHESIS_NAN_SEARCH, SEND_TO_THE_SCOPE, SEND_TO_THE_SPECTRUM
from simple_speech_synthesizer.garbage_collection_prevention import anchor_pyo_objects, GLOBAL_AUDIO_FORTRESS

import time, math

AMPLITUDE_CORRECTION = -9

# Gemini code that calculates human-like formant scaling for a frequency.
@anchor_pyo_objects
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

# Modified code of the above one for aspiration
@anchor_pyo_objects
def calculate_aspiration_q(freq, noise_floor=15.0, noise_slope=0.012):
    """
    Calculates the ultra-tight, highly focused Q factors
    specifically required to make random noise sound like vocal air.
    """
    # 1. Much lower floor (15Hz) and a tiny slope (1.2%)
    # to replicate your 18Hz to 46Hz empirical sweet spot.
    bandwidth = noise_floor + (noise_slope * freq)

    # 2. Return the noise-specific Q
    return freq / bandwidth

@anchor_pyo_objects
def synthesize(input: this_layer_types.Input):
    """
    The actual synthesis part.
    :param input: The layer input.
    :return:
    """

    s = input.server

    s_p = load_low_level_character(input.character_dir_path).synthesis_parameters

    input_Volume = input.Volume + AMPLITUDE_CORRECTION

    ### VOICE SOURCE
    F0_freq_sway = pyo.ButLP(pyo.BrownNoise(), freq=3, mul=3 * input.F0_freq_sway)
    F0_freq_FM_jitter = pyo.ButLP(pyo.BrownNoise(), freq=15, mul=0.15 * input.F0_freq_FM_jitter)
    true_F0 = input.F0 + F0_freq_sway + F0_freq_FM_jitter

    voice_source_amp_sway = pyo.ButLP(pyo.BrownNoise(), freq=25, mul=0.03 * input.voice_source_amp_sway)

    raw_blit_source = pyo.Blit(freq=true_F0, harms=70, mul=1 + voice_source_amp_sway)
    spectral_tilted_6db_rolloff_blit_source = pyo.Tone(raw_blit_source, s_p["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)
    spectral_tilted_12db_rolloff_blit_source = pyo.ButLP(raw_blit_source, s_p["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)
    spectral_tilted_18db_rolloff_blit_source = pyo.Tone(spectral_tilted_12db_rolloff_blit_source, s_p["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)
    spectral_tilted_24db_rolloff_blit_source = pyo.ButLP(spectral_tilted_12db_rolloff_blit_source, s_p["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)
    # TODO: decide if the MoogLP and ButLP should be Tone(Tone(...)) (of previous layers etc.) instead

    #  OLD CROSSFADE: spectral_tilted_blit_source = (spectral_tilted_12db_rolloff_blit_source * (1-input.Spectral_tilt_tension)) + (spectral_tilted_6db_rolloff_blit_source * input.Spectral_tilt_tension)
    spectral_tilted_blit_source = pyo.Selector([spectral_tilted_24db_rolloff_blit_source,
                                                       spectral_tilted_18db_rolloff_blit_source,
                                                       spectral_tilted_12db_rolloff_blit_source,
                                                       spectral_tilted_6db_rolloff_blit_source],
                                               (input.Spectral_tilt_tension + 1) / 2 * 3)
    high_freq_retention_blit_source = pyo.ButHP(raw_blit_source, 3000, mul=0.005)
    partial_voice_source = spectral_tilted_blit_source + high_freq_retention_blit_source
    unbalanced_voice_source = pyo.EQ(partial_voice_source,
                                     freq=s_p["spectral_hill_freq"],  # SPECTRAL HILL DELTAFACTOR REMOVED
                                     q=s_p["spectral_hill_freq"] / s_p["spectral_hill_bandwidth"],
                                     # TODO that spectral_hill_bandwidth was just a quick fix, that may not be the best implementation method
                                     boost=s_p["spectral_hill_boost"] + input.Spectral_hill_boost_delta)
    amp_multiplier = pyo.DBToA(input_Volume)
    voice_source = pyo.Balance(unbalanced_voice_source, pyo.Sine(true_F0, mul=amp_multiplier))

    # TODO potential chorus effect could be applied here for a multiple singers effect

    ### VOICE FILTER
    vowel_f0 = pyo.ButLP(
        pyo.Reson(voice_source, true_F0, 1 * input.Nasality_F0_Q_factor, mul=s_p["FO_mul"] * input.Nasality_F0_importance_factor),
            true_F0 * input.H1_H2_balance
    )  # TODO implement H1_H2_balance correctly (there are weird cancelling artifacts...
    vowel_formants = list()
    for j, freq in enumerate(input.Vowel_formant_freqs):
        calculated_freq = freq
        calculated_q = calculate_q(freq, s_p["vowel_Q_floor"], s_p["vowel_Q_slope"]) * input.Vowel_Q_multiplier
        calculated_importance = input.Vowel_formant_importances[j]
        if j == 0:  # F1
            calculated_freq = pyo.Max(calculated_freq, true_F0 + s_p["F0_F1_min_difference"])
            calculated_q *= input.Nasality_F1_Q_factor
            calculated_importance *= input.Nasality_F1_importance_factor
        else:
            calculated_importance *= input.Nasality_F2_and_higher_importance_factor
        vowel_formants.append(
            pyo.Reson(voice_source,
                      freq=calculated_freq,
                      q=calculated_q,
                      mul=calculated_importance)
        )

    ##### NASAL FORMANTS INSERTED IN VOWEL FORMANTS
    nasal_murmur_freq = s_p["default_oral_constriction_nasal_murmur_freq"]  # should this be in realization?
    for j, freq in enumerate([input.Nasality_nasal_formant_N1_freq, input.Nasality_nasal_formant_N2_freq, nasal_murmur_freq]):
        """NO MINIMUM BETWEEN F0 AND N1???
        calculated_freq = freq
        if j == 0:
            calculated_freq = pyo.Max(calculated_freq, true_F0 + s_p["F0_F1_min_difference"])"""
        vowel_formants.append(  # they are not treated differently, as they are still pyo.Reson objects acting upon the same source
            pyo.Reson(voice_source,
                      freq=freq,
                      q=calculate_q(freq, s_p["vowel_Q_floor"], s_p["vowel_Q_slope"]) * input.Vowel_Q_multiplier,
                      mul=[input.Nasality_nasal_formant_N1_importance, input.Nasality_nasal_formant_N2_importance, input.Nasal_murmur_importance][j])
        )

    raw_voiced_component = vowel_f0 + sum(vowel_formants)  # aka. without aspiration and nasality

    ### VOWEL OUTPUT
    raw_voiced_component = raw_voiced_component * input.Voiced_component_importance

    # TODO: There's still a whistle left because of the aspiration...
    ### ASPIRATION SOURCE (this is also passed to the same filters for efficiency)
    raw_noise_source = pyo.Noise()
    # aspiration has less spectral tilt
    spectral_tilted_6db_rolloff_noise_source = pyo.Tone(raw_noise_source, s_p["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)
    spectral_tilted_12db_rolloff_noise_source = pyo.ButLP(raw_noise_source, s_p["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)
    spectral_tilted_18db_rolloff_noise_source = pyo.Tone(spectral_tilted_12db_rolloff_noise_source, s_p["spectral_tilt_cutoff"] + input.Spectral_tilt_cutoff_delta, mul=1)

    spectral_tilted_noise_source = pyo.Selector([spectral_tilted_18db_rolloff_noise_source,
                                                 spectral_tilted_12db_rolloff_noise_source,
                                                 spectral_tilted_6db_rolloff_noise_source,
                                                 raw_noise_source],
                                                (input.Spectral_tilt_tension + 1) / 2 * 3)
    high_freq_retention_noise_source = pyo.ButHP(raw_noise_source, 3000, mul=0.005)
    partial_aspiration_source = spectral_tilted_noise_source + high_freq_retention_noise_source
    unbalanced_noise_source = pyo.EQ(partial_aspiration_source,
                                     freq=s_p["spectral_hill_freq"],
                                     q=s_p["spectral_hill_freq"] / s_p["spectral_hill_bandwidth"],
                                     boost=s_p["spectral_hill_aspiration_boost"] + input.Spectral_hill_boost_delta)
    amp_multiplier = pyo.DBToA(input_Volume) * input.Aspiration_volume_factor
    aspiration_source = pyo.Balance(unbalanced_noise_source, pyo.FastSine(true_F0, mul=amp_multiplier))

    ### ASPIRATION FILTER
    aspiration_f0 = pyo.ButLP(
        pyo.Reson(aspiration_source, true_F0, 1, mul=s_p["F0_aspiration_mul"]),
            true_F0 * input.H1_H2_balance
    )  # TODO implement H1_H2_balance correctly (there are weird cancelling artifacts...
    aspiration_formants = list()
    for j, freq in enumerate(input.Vowel_formant_freqs):
        calculated_freq = freq
        calculated_q = calculate_q(freq, s_p["aspiration_Q_floor"], s_p["aspiration_Q_slope"]) #  * input.Vowel_Q_multiplier
        calculated_importance = input.Vowel_formant_importances[j]
        if j == 0:  # F1
            calculated_freq = pyo.Max(calculated_freq, true_F0 + s_p["F0_F1_min_difference"])
            calculated_q *= input.Nasality_F1_Q_factor
            calculated_importance *= input.Nasality_F1_importance_factor
        else:
            calculated_importance *= input.Nasality_F2_and_higher_importance_factor
        aspiration_formants.append(
            pyo.Reson(aspiration_source,
                      freq=calculated_freq,
                      q=calculated_q,
                      mul=calculated_importance)
        )

    ##### NASAL FORMANTS INSERTED IN ASPIRATION FORMANTS    # Should there be nasal murmur here?
    for j, freq in enumerate([input.Nasality_nasal_formant_N1_freq, input.Nasality_nasal_formant_N2_freq]):
        """NO MINIMUM BETWEEN F0 AND N1???
        calculated_freq = freq
        if j == 0:
            calculated_freq = pyo.Max(calculated_freq, true_F0 + s_p["F0_F1_min_difference"])"""
        aspiration_formants.append(
            # they are not treated differently, as they are still pyo.Reson objects acting upon the same source
            pyo.Reson(aspiration_source,
                      freq=freq,
                      q=calculate_q(freq, s_p["aspiration_Q_floor"], s_p["aspiration_Q_slope"]),
                      mul=[input.Nasality_nasal_formant_N1_importance, input.Nasality_nasal_formant_N2_importance][j])
        )

    dark_aspiration_component = aspiration_f0 + sum(aspiration_formants)
    # THIS IS PRETTY BODGY, it's based on the sound in pyo_playground_e.py
    brightness_loss_compensation = pyo.ButBP(
        raw_noise_source,
        freq=s_p["spectral_hill_freq"],
        q=s_p["spectral_hill_freq"] / s_p["spectral_hill_bandwidth"],
        mul=1)
    amp_multiplier = pyo.DBToA(input_Volume) * input.Aspiration_volume_factor * s_p["aspiration_brightness_loss_compensation_factor"]
    aspiration_component = dark_aspiration_component + pyo.Balance(brightness_loss_compensation, pyo.FastSine(true_F0, mul=amp_multiplier))

    aspiration_component = aspiration_component * input.Aspiration_component_importance

    ### VOWEL + ASPIRATION = FULL_VOICED_WITHOUT_GLOBAL_NASALITY (but nasal formants are there)
    full_voiced_component_without_global_nasality = raw_voiced_component + aspiration_component

    ##### VOWEL_NASALALITY LP (AND NO ANTIFORMANT)
    nasal_lp_applied = pyo.ButLP(full_voiced_component_without_global_nasality,
                                           freq=input.Nasality_LP_freq)
    nasal_lp_crossfade = pyo.Selector([full_voiced_component_without_global_nasality,
                                       nasal_lp_applied],
                                      voice=input.Nasality_LP_strength)

    full_voiced_component = pyo.EQ(nasal_lp_crossfade,
                              freq=input.Nasality_antiformant_freq,
                              q=input.Nasality_antiformant_freq / input.Nasality_antiformant_bandwidth,
                              boost=input.Nasality_antiformant_boost)
    #full_voiced_component = nasal_lp_crossfade  # vowel + aspiration + nasal formants for both + global nasalaity properties

    # CONSTRICTION SOURCE
    constriction_source = pyo.Noise()

    constr1_hp_filter     = pyo.Biquadx(constriction_source, freq=input.Constriction_HP_freq * 1.25, stages=3, type=1)
    constr2_lp_filter     = pyo.Biquadx(constr1_hp_filter, freq=input.Constriction_LP_freq * 0.75, stages=3, type=0)
    amp_multiplier = pyo.DBToA(input_Volume) * input.Constriction_volume_factor
    constr3_balanced      = pyo.Balance(constr2_lp_filter, pyo.FastSine(true_F0, mul=amp_multiplier))
    constr4_peak          = pyo.EQ(constr3_balanced,
                                   freq=input.Constriction_peak_freq,
                                   q=input.Constriction_peak_freq / input.Constriction_peak_bandwidth,
                                   boost=input.Constriction_peak_boost)
    constr5_peak_overtone = pyo.EQ(constr4_peak,
                                   freq=input.Constriction_peak_freq * 2,  # TODO maybe shake that 2 around a bit...
                                   q=input.Constriction_peak_freq / input.Constriction_peak_bandwidth * 2,  # TODO and that division by 2 could be parametrized
                                   boost=input.Constriction_peak_boost * input.Constriction_peak_overtone_importance)
    constriction_component = constr5_peak_overtone * input.Constriction_component_importance

    ### Effects + FULL SUM OUT

    non_effected_sum = full_voiced_component + constriction_component

    reverb_sum = pyo.Freeverb(
        non_effected_sum,
        size=0.15,  # Very small room size to avoid massive echoes
        damp=0.85,  # Heavily muffle the high frequencies of the reflections
        bal=0.12  # Keep it subtle! Just 12% wet mix to smear the edges
    )
    audio_out = pyo.Chorus(
        reverb_sum,
        depth=1,
        feedback=0.8,
        bal=0.01
    )

    #### ROUTE OUTPUT
    audio_out.out(0)
    audio_out_2 = audio_out * 1
    audio_out_2.out(1)

    #### PLAY ALL THE ENVELOPES
    '''for env in input.Vowel_formant_freqs: env.play()
    for env in input.Vowel_formant_importances: env.play()
    """input.Constriction_HP_freq.play()
    input.Constriction_peak_freq.play()
    input.Constriction_peak_bandwidth.play()
    input.Constriction_peak_boost.play()
    input.Constriction_peak_overtone_importance.play()
    input.Constriction_LP_freq.play()
    input.Voiced_component_importance.play()
    input.Constriction_component_importance.play()
    input.Aspiration_component_importance.play()
    input.Volume.play()
    input.F0.play()
    input.Spectral_tilt_cutoff_delta.play()
    input.Spectral_tilt_tension.play()
    #  input.Spectral_hill_freq_deltafactor.play()
    input.Spectral_hill_boost_delta.play()
    input.Vowel_Q_multiplier.play()
    input.Aspiration_volume_factor.play()
    input.Constriction_volume_factor.play()
    input.Nasal_murmur_importance.play()
    input.Nasality_LP_strength.play()
    input.Nasality_antiformant_boost.play()  # This should be removed if the code below works
    input.F0_freq_sway.play()
    input.F0_freq_FM_jitter.play()
    input.voice_source_amp_sway.play()"""
    input_all_attributes = vars(input)
    for key, attr in input_all_attributes.items():
        if isinstance(attr, pyo.PyoObject):
            attr.play()'''
    activate_layer_inputs(input)

    #### RECORD
    s.recordOptions(dur=input.duration, filename=input.output_filepath)
    s.start()

    ###### DEBUG
    if _DEBUG_SYNTHESIS:
        print("=== RUNNING SYNTHESIS DEBUG ===")
        print("Length of collected PyoObjectBases:", len(GLOBAL_AUDIO_FORTRESS))
    if _DEBUG_SYNTHESIS and not _DEBUG_SYNTHESIS_NAN_SEARCH:
        GUI_debug(s, audio_out)
    elif _DEBUG_SYNTHESIS and _DEBUG_SYNTHESIS_NAN_SEARCH:
        NAN_search(s)

    return input.output_filepath

    # TODO: there are still some magic numbers left in the synth (like the F0 multiplier is just... a character trait?
    #       and there are even more things, like how the multiplier of the F0noise is just... 1, and its Q value is fixed...

@anchor_pyo_objects
def transform(input: this_layer_types.Input) -> str:
    """
    The final layer in the synthesis stack.
    :param input: This layer's Input.
    :return: The audio_out and audio_out_2, which will be anchored to the global execution layer in orchestrator.py to prevent Python garbage collection.
    """
    output_filepath = synthesize(input)
    return output_filepath


def GUI_debug(s: pyo.Server, audio_out):
    to_scope = [audio_out] + SEND_TO_THE_SCOPE
    to_spectrum = [audio_out] + SEND_TO_THE_SPECTRUM
    scope = pyo.Scope(to_scope, length=0.75)
    analyzer = pyo.Spectrum(to_spectrum, size=2 ** 14)
    analyzer.setFscaling(True)  # log
    analyzer.setLowFreq(0)
    analyzer.setHighFreq(10000)
    analyzer.setGain(0)
    s.gui(locals())

def NAN_search(s: pyo.Server):
    # Gemini code
    print("=== NaN Tracker Active. Watching the DSP graph... ===")
    try:
        while True:
            time.sleep(0.1)  # Sample frequently to catch it early

            found_bad_obj = False
            for obj in GLOBAL_AUDIO_FORTRESS:
                try:
                    # Read the current buffer value of the node
                    val = obj.get()

                    # Check if this specific node has collapsed into NaN or Infinity
                    if math.isnan(val) or math.isinf(val):
                        found_bad_obj = True
                        print(f"\n=== MATH EXPLOSION DETECTED! ===")
                        print(f"Node Type: {type(obj).__name__}")
                        print(f"Memory Address: {hex(id(obj))}")

                        # If the object has parameters you can read, print them:
                        if hasattr(obj, 'freq'):
                            print(f" -> Current Freq Parameter: {obj.freq}")
                        if hasattr(obj, 'mul'):
                            print(f" -> Current Mul Parameter: {obj.mul}")

                except Exception:
                    # Some internal structural base objects might not support .get(), skip them safely
                    continue
            if found_bad_obj:
                print("\nHalting synthesis.")
                return  # Exit the program immediately

    except KeyboardInterrupt:
        print("\nStopping audio server gracefully...")
        s.stop()





if __name__ == "__main__":
    vowels = {
        "ε": [538, 1779, 2751],
        "ɹ": [396, 1850, 2221],
        "a": [808, 1210, 3005],
        "o": [312, 593, 2934],
        "ə": [602, 1219, 2794],
        "i": [450, 2460, 2922],
        "vtuber_i": [450, 3264, 3760]
    }
    F0 = 119
    F1 = 312  # praat value; orig 610
    F2 = 593  # praat value; orig 1900
    F3 = 2934  # praat value
    # 538, 1779, 2751
    # parameters adapted from pyo_playground_e.py
    i = this_layer_types.Input(
        server=pyo.Server(),
        character_dir_path=r"..\characters\Greensparrow",
        output_filepath=r"testaudio.wav",
        duration=3.0,
        Vowel_formant_freqs=[[(0, F1), (3, F1)],  # it's <a> rn
                             [(0, F2), (3, F2)],
                             [(0, F3), (3, F3)]],
        Vowel_formant_importances=[[(0, 1), (3, 1)],
                                   [(0, 1), (3, 1)],
                                   [(0, 1), (3, 1)],],
        Constriction_HP_freq=[(0, 1500), (3, 1500)],
        Constriction_LP_freq=[(0, 14000), (3, 14000)],
        Constriction_peak_freq=[(0, 3400), (3, 3400)],
        Constriction_peak_bandwidth=[(0, 1500), (3, 1500)],
        Constriction_peak_boost=[(0, 20), (3, 20)],
        Constriction_peak_overtone_importance=[(0, 0.4), (3, 0.4)],
        Constriction_volume_factor=[(0, 0.15), (3, 0.15)],
        Voiced_component_importance=[(0, 1), (3, 1)],
        Constriction_component_importance=[(0, 0), (3, 0)],
        Aspiration_component_importance=[(0, 1), (3, 0.5)],
        Volume=[(0, -6), (3, -6)],
        F0=[(0, F0), (3, F0)],
        F0_freq_sway=1,
        F0_freq_FM_jitter=1,
        voice_source_amp_sway=1,
        Spectral_tilt_cutoff_delta=[(0, 0), (3, 0)],
        Spectral_tilt_tension=[(0, 0), (3, 0)],
        #  Spectral_hill_freq_deltafactor=[(0, 1), (3, 1)],
        Spectral_hill_boost_delta=[(0, 0), (3, 0)],
        Vowel_Q_multiplier=[(0, 1), (3, 0.5)],
        Nasal_murmur_importance=[(0, 0), (3, 0.5)],
        Nasality_LP_strength=[(0, 0), (3, 0.5)],
        Nasality_antiformant_boost=[(0, -0), (3, -5)],
        Aspiration_volume_factor=[(0, 0.4), (3, 0.4)]
    )
    o = transform(i)