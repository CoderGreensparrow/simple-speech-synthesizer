"""
LAYER 5: realization
Evaluates higher-level acoustic parameters into the lower-level ones.
So Nasality, Breathiness etc. gets all encoded in F0, F1, F2, noise_amp, voiced_amp etc.
It makes the higher-level data synthesizer-friendly.

The actual conversion from custom types (Envelope) to pyo's types happens in the layer below.
"""

from simple_speech_synthesizer.realization import types as this_layer_types
from simple_speech_synthesizer.synthesis import synthesis_types as next_layer_types
from simple_speech_synthesizer.base.load_low_level_character import load_low_level_character

from pyo import Max, Min

def transform(input_: this_layer_types.Input) -> next_layer_types.Input:
    """
    This layer applies the middle-level parameters to the low-level ones.
    :param input:
    :return:
    """
    s_p = load_low_level_character(input_.character_dir_path).synthesis_parameters

    ### INPUTS
    vowel_formant_freqs = input_.Vowel_formant_freqs
    vowel_formant_importances = input_.Vowel_formant_importances
    constriction_HP_freq = input_.Constriction_HP_freq
    constriction_peak_freq = input_.Constriction_peak_freq
    constriction_peak_bandwidth = input_.Constriction_peak_bandwidth
    constriction_peak_boost = input_.Constriction_peak_boost
    constriction_peak_overtone_importance = input_.Constriction_peak_overtone_importance
    constriction_LP_freq = input_.Constriction_LP_freq

    vowel_importance = input_.Vowel_importance
    constriction_importance = input_.Constriction_importance

    true_nasality = input_.Nasality + input_.NasalityDelta
    true_aspiration = input_.Aspiration_importance + input_.BreathinessDelta

    volume = input_.Volume
    f0 = input_.F0
    tension = input_.Tension
    machine_growl = input_.MachineGrowl
    lip_rounding_delta = input_.LipRoundingDelta
    vocal_gender_delta = input_.VocalGenderDelta

    throat_jitter = input_.ThroatJitter


    ### TRANSFORM
    # Whatever these equal to will be the output of this layer.
    # This architecture was chosen because everything affects everything.
    # To make it more readable, every time some modifier is applied, the following order must be used:
    # Nasality + Tension + Gender + Whatever else
    true_lip_rounding_factor = 1 + (lip_rounding_delta * s_p["lip_rounding_formant_effect_factor"])
    gender_formant_factor = 1 + (vocal_gender_delta * 0.5)  # -1 ultra-masculine, 1 ultra-feminine, 0 natural
    gender_hill_boost_factor = vocal_gender_delta * s_p["tension_induced_spectral_hill_boost"] * 0.5
    # TODO: These numbers here for gender shifting are just off the top of my head

    Vowel_formant_freqs = [sig * gender_formant_factor * true_lip_rounding_factor
                           for sig in vowel_formant_freqs]
    Vowel_formant_importances = vowel_formant_importances
    Constriction_HP_freq = constriction_HP_freq * gender_formant_factor * true_lip_rounding_factor
    Constriction_peak_freq = constriction_peak_freq * gender_formant_factor * true_lip_rounding_factor
    Constriction_peak_bandwidth = constriction_peak_bandwidth
    Constriction_peak_boost = constriction_peak_boost
    Constriction_peak_overtone_importance = constriction_peak_overtone_importance
    Constriction_LP_freq = constriction_LP_freq * gender_formant_factor * true_lip_rounding_factor
    Voiced_component_importance = vowel_importance
    Constriction_component_importance = constriction_importance
    Aspiration_component_importance = true_aspiration

    Volume = volume
    F0 = f0  # tension not added for correct singing
    Spectral_tilt_cutoff_delta = 0 + tension * s_p["tension_induced_spectral_tilt_freq_delta"]
    Spectral_tilt_tension = (0 + true_aspiration * s_p["aspiration_tension_scaling_factor"]
                             + tension * s_p["tension_induced_spectral_tilt_scaling_factor"])
    Spectral_hill_boost_delta = (0 + true_aspiration * s_p["spectral_hill_aspiration_boost"]
                                 + tension * s_p["tension_induced_spectral_hill_boost"]
                                 + gender_hill_boost_factor)
    Vowel_Q_multiplier = Max(1 - (0.5 * true_nasality), 0.0001)  # failsafe: don't get Q to 0
    Aspiration_volume_factor = s_p["default_Vowel_aspiration_as_a_factor_of_volume"]
    Constriction_volume_factor = s_p["default_Constriction_volume_as_a_factor_of_volume"]
    Nasal_murmur_importance = true_nasality * s_p["default_nasal_murmur_importance"]
    Nasality_LP_strength = true_nasality
    Nasality_antiformant_boost = true_nasality * s_p["default_nasal_antiformant_boost"]

    F0_freq_sway = throat_jitter  # magic numbers in synthesizer, these are just factors
    F0_freq_FM_jitter = throat_jitter
    voice_source_amp_sway = throat_jitter


    ### OUTPUT
    output = next_layer_types.Input(
        server=input_.server,
        character_dir_path=input_.character_dir_path,
        output_filepath=input_.output_filepath,
        duration=input_.duration,

        Vowel_formant_freqs=Vowel_formant_freqs,
        Vowel_formant_importances=Vowel_formant_importances,
        Constriction_HP_freq=Constriction_HP_freq,
        Constriction_peak_freq=Constriction_peak_freq,
        Constriction_peak_bandwidth=Constriction_peak_bandwidth,
        Constriction_peak_boost=Constriction_peak_boost,
        Constriction_peak_overtone_importance=Constriction_peak_overtone_importance,
        Constriction_LP_freq=Constriction_LP_freq,
        Voiced_component_importance=Voiced_component_importance,
        Constriction_component_importance=Constriction_component_importance,
        Aspiration_component_importance=Aspiration_component_importance,

        Volume=Volume,
        F0=F0,
        Spectral_tilt_cutoff_delta=Spectral_tilt_cutoff_delta,
        Spectral_tilt_tension=Spectral_tilt_tension,
        Spectral_hill_boost_delta=Spectral_hill_boost_delta,
        Vowel_Q_multiplier=Vowel_Q_multiplier,
        Aspiration_volume_factor=Aspiration_volume_factor,
        Constriction_volume_factor=Constriction_volume_factor,
        Nasal_murmur_importance=Nasal_murmur_importance,
        Nasality_LP_strength=Nasality_LP_strength,
        Nasality_antiformant_boost=Nasality_antiformant_boost,

        F0_freq_sway=F0_freq_sway,
        F0_freq_FM_jitter=F0_freq_FM_jitter,
        voice_source_amp_sway=voice_source_amp_sway
    )

    ### RETURN OUTPUT
    return output