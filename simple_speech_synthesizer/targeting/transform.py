"""
SYNTHESIS LAYER 2: Creates the acoustic targets for the nonexistent mouth.
It knows nothing about prosody. It takes prosody-included phonemic input data, and converts that to formant parameters and vocal amplitudes.
"""

from simple_speech_synthesizer.targeting import types as this_layer_types
from simple_speech_synthesizer.acoustic_state import OLD_ORDER_types as next_layer_types

from simple_speech_synthesizer.targeting.load_character import load_character
from simple_speech_synthesizer.targeting.target_generator import create_acoustic_targets


def transform(input: this_layer_types.Input) -> next_layer_types.Input:
    """
    Entry point, transform function for the TARGETING layer.
    :param input: layer input specified in the layer's types.
    :return: next layer input.
    """
    character = load_character(input.character_dir_path)
    acoustic_targets = create_acoustic_targets(input, character)
    output = next_layer_types.Input(
        character_dir_path=input.character_dir_path,
        acoustic_targets=acoustic_targets,
        global_envelope_targets=input.global_envelope_targets,
        duration=input.duration
    )
    return output





if __name__ == "__main__":
    from simple_speech_synthesizer.targeting.types import Input, TimedPhoneme, GlobalEnvelopeTargets
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