from simple_speech_synthesizer.acoustic_state import types as this_layer_types
from simple_speech_synthesizer.realization import types as next_layer_types
from simple_speech_synthesizer.base.garbage_collection_prevention_helpers import activate_layer_inputs

from simple_speech_synthesizer.base.load_low_level_character import load_low_level_character

import pyo

from simple_speech_synthesizer.global_debug_vars import _DEBUG_SYNTHESIS

from simple_speech_synthesizer.garbage_collection_prevention import anchor_pyo_objects

@anchor_pyo_objects
def transform(input_: this_layer_types.Input) -> next_layer_types.Input:
    """
    Interpolates the input with exponential portamento.
    :param input_: This layer's Input.
    :return: The next layer's Input.
    """
    activate_layer_inputs(input_)

    s_p = load_low_level_character(input_.character_dir_path).synthesis_parameters
    tongue_rt = s_p["acoustic_simulation_tongue_risetime"]
    tongue_ft = s_p["acoustic_simulation_tongue_falltime"]
    larynx_rt = s_p["acoustic_simulation_larynx_risetime"]
    larynx_ft = s_p["acoustic_simulation_larynx_falltime"]
    pharynx_rt = s_p["acoustic_simulation_pharynx_risetime"]
    pharynx_ft = s_p["acoustic_simulation_pharynx_falltime"]
    lip_rt = s_p["acoustic_simulation_lip_risetime"]
    lip_ft = s_p["acoustic_simulation_lip_falltime"]

    # ADDITIONAL COMPUTED VALUES
    Stop_amp = pyo.Port(
        # calculation: map range [0; 1] to [stop_amp_should_rise_after...; 1] then map the [0; 1] range of that to [1; max_stop_amp]
        __1:=pyo.Clip((input_.Full_closure / (1-s_p["stop_amp_should_rise_after_full_closure_hits_this"]) - 1/(1-s_p["stop_amp_should_rise_after_full_closure_hits_this"]) + 1)
                 * (1-s_p["max_stop_amp"]) + 1,
                 min=1, max=s_p["max_stop_amp"]).play(),
        risetime=s_p["stop_amp_risetime"],
        falltime=s_p["stop_amp_falltime"],
        init=1
    )

    ### OUTPUTS
    # Envelopes, simulated from acoustic targets
    Vowel_formant_freqs = [pyo.Port(seg, tongue_rt, tongue_ft) for seg in input_.Vowel_formant_freqs]
    Vowel_formant_importances = [pyo.Port(seg, tongue_rt, tongue_ft) for seg in input_.Vowel_formant_importances]
    Constriction_HP_freq = pyo.Port(input_.Constriction_HP_freq, tongue_rt, tongue_ft)
    Constriction_peak_freq = pyo.Port(input_.Constriction_peak_freq, tongue_rt, tongue_ft)
    Constriction_peak_bandwidth = pyo.Port(input_.Constriction_peak_bandwidth, tongue_rt, tongue_ft)
    Constriction_peak_boost = pyo.Port(input_.Constriction_peak_boost, tongue_rt, tongue_ft)
    Constriction_peak_overtone_importance = pyo.Port(input_.Constriction_peak_overtone_importance, tongue_rt, tongue_ft)
    Constriction_LP_freq = pyo.Port(input_.Constriction_LP_freq, tongue_rt, tongue_ft)
    #  Voice_to_noise_ratio: Envelope  This is replaced by individual Vowel, Aspiration and Constriction importances and Nasality
    Vowel_importance = pyo.Port(input_.Vowel_importance, pharynx_rt, pharynx_ft)
    Aspiration_importance = pyo.Port(input_.Aspiration_importance, pharynx_rt, pharynx_ft)
    Constriction_importance = pyo.Port(input_.Constriction_importance, tongue_rt, tongue_ft)
    Nasality = pyo.Port(input_.Nasality, larynx_rt, larynx_ft)
    Full_closure = pyo.Port(input_.Full_closure, tongue_rt, tongue_ft)
    Stop_amp = Stop_amp
    # TODO Maybe there should be a max_stop_amp slider, and not just a constant
    # Global envelopes
    Volume = pyo.Port(input_.Volume, pharynx_rt, pharynx_ft)
    F0 = pyo.Port(input_.F0, pharynx_rt, pharynx_ft)
    NasalityDelta = pyo.Port(input_.NasalityDelta, larynx_rt, larynx_ft)
    BreathinessDelta = pyo.Port(input_.BreathinessDelta, pharynx_rt, pharynx_ft)
    Tension = pyo.Port(input_.Tension, pharynx_rt, pharynx_ft)
    MachineGrowl = pyo.Port(input_.MachineGrowl, pharynx_rt, pharynx_ft)
    LipRoundingDelta = pyo.Port(input_.LipRoundingDelta, lip_rt, lip_ft)
    VocalGenderDelta = pyo.Port(input_.VocalGenderDelta, pharynx_rt, pharynx_ft)
    # Throat jitter
    ThroatJitter = pyo.Port(input_.ThroatJitter, pharynx_rt, pharynx_ft)

    output = next_layer_types.Input(
        server=input_.server,
        character_dir_path=input_.character_dir_path,
        output_filepath=input_.output_filepath,
        duration=input_.duration,
        # Envelopes, simulated from acoustic targets
        Vowel_formant_freqs=Vowel_formant_freqs,
        Vowel_formant_importances=Vowel_formant_importances,
        Constriction_HP_freq=Constriction_HP_freq,
        Constriction_peak_freq=Constriction_peak_freq,
        Constriction_peak_bandwidth=Constriction_peak_bandwidth,
        Constriction_peak_boost=Constriction_peak_boost,
        Constriction_peak_overtone_importance=Constriction_peak_overtone_importance,
        Constriction_LP_freq=Constriction_LP_freq,
        #  Voice_to_noise_ratio: Envelope  This is replaced by individual Vowel, Aspiration and Constriction importances and Nasality
        Vowel_importance=Vowel_importance,
        Aspiration_importance=Aspiration_importance,
        Constriction_importance=Constriction_importance,
        Nasality=Nasality,
        Full_closure=Full_closure,
        Stop_amp=Stop_amp,
        # Global envelopes
        Volume=Volume,
        F0=F0,
        NasalityDelta=NasalityDelta,
        BreathinessDelta=BreathinessDelta,
        Tension=Tension,
        MachineGrowl=MachineGrowl,
        LipRoundingDelta=LipRoundingDelta,
        VocalGenderDelta=VocalGenderDelta,
        # Throat jitter
        ThroatJitter=ThroatJitter
    )

    return output