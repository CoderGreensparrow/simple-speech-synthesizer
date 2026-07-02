"""
SYNTHESIS LAYER 2: Creates the acoustic targets for the nonexistent mouth.
It knows nothing about prosody. It takes prosody-included phonemic input data, and converts that to formant parameters and vocal amplitudes.
"""

from simple_speech_synthesizer.targeting import types as this_layer_types
from simple_speech_synthesizer.pyo_converter import types as next_layer_types

from simple_speech_synthesizer.base.load_character import load_character
from simple_speech_synthesizer.base.types import Targets, FormantTargets


def transform(input_: this_layer_types.Input) -> next_layer_types.Input:
    """
    Entry point, transform function for the TARGETING layer.
    :param input: layer input specified in the layer's types.
    :return: next layer input.
    """
    character = load_character(input_.character_dir_path)

    # magic

    output = next_layer_types.Input(
        character_dir_path=input_.character_dir_path,
        output_filepath=input_.output_filepath,
        duration=input_.duration,
        # Phoneme targets
        vowel_formant_freqs_targets=,
        constriction_HP_freq_targets=,
        constriction_peak_freq_targets=,
        constriction_peak_bandwidth_targets=,
        constriction_peak_boost_targets=,
        constriction_peak_overtone_importance_targets=,
        constriction_LP_freq_targets=,
        vowel_importance_targets=,
        aspiration_importance_targets=,
        constriction_importance_targets=,
        nasality_targets=,
        full_closure_targets=,
        # Global envelopes
        Volume=input_.envelope_targets.Volume,
        F0=input_.envelope_targets.F0,
        NasalityDelta=input_.envelope_targets.NasalityDelta,
        BreathinessDelta=input_.envelope_targets.BreathinessDelta,
        Tension=input_.envelope_targets.Tension,
        MachineGrowl=input_.envelope_targets.MachineGrowl,
        LipRoundingDelta=input_.envelope_targets.LipRoundingDelta,
        VocalGenderDelta=input_.envelope_targets.VocalGenderDelta,
        # Throat jitter
        ThroatJitter=input_.envelope_targets.ThroatJitter
    )
    return output





if __name__ == "__main__":
    from simple_speech_synthesizer.targeting.OLD_types import Input, TimedPhoneme, GlobalEnvelopeTargets
    from simple_speech_synthesizer.base.types import Envelope, Point, Segment
    i = Input(
        character_dir_path=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\characters\Greensparrow",
        phonemes=(TimedPhoneme("s", 0, 0.1), TimedPhoneme("a", 0.1, 0.7), TimedPhoneme("s", 0.7, 0.8)),
        global_envelope_targets=GlobalEnvelopeTargets(
            F0=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            NasalityDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            BreathinessDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            Tension=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            VocalTilt=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            LipRoundingDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            GenderDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            Volume=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
        ),
        duration=0.8
    )
    t = transform(i)
    for j in t.acoustic_targets:
        print(j)