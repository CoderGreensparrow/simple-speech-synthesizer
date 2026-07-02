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


def transform(input_: this_layer_types.Input) -> next_layer_types.Input:
    """
    This layer applies the middle-level parameters to the low-level ones.
    :param input:
    :return:
    """
    s_p = load_low_level_character(input_.character_dir_path).synthesis_parameters
    out = {}

    ### INPUTS
    vowel_formant_freqs = input_.Vowel_formant_freqs
    vowel_formant_importances = input_.Vowel_formant_importances
    something = input_.Constriction_HP_freq
    something = input_.Constriction_peak_freq
    something = input_.Constriction_peak_bandwidth
    something = input_.Constriction_peak_boost
    something = input_.Constriction_peak_overtone_importance
    something = input_.Constriction_LP_freq
    something = input_.Vowel_importance
    something = input_.Aspiration_importance
    something = input_.Constriction_importance

    volume = input_.Volume
    f0 = input_.F0
    true_nasality = input_.Nasality + input_.NasalityDelta
    true_aspiration = input_.Aspiration_importance + input_.BreathinessDelta
    tension = input_.Tension
    machine_growl = input_.MachineGrowl
    lip_rounding_delta = input_.LipRoundingDelta
    vocal_gender_delta = input_.VocalGenderDelta

    ### OUTPUTS
    out[""]

    ### RETURN OUTPUT
    return next_layer_types.Input(**out)