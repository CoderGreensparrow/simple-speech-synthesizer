#  from simple_speech_synthesizer.garbage_collection_prevention import GLOBAL_AUDIO_FORTRESS
"""This may be required to run correctly."""
from simple_speech_synthesizer.targeting.types import Input as InputTargeting
from simple_speech_synthesizer.targeting.transform import transform as transform_targeting
from simple_speech_synthesizer.pyo_converter.types import Input as InputPyoConverter
from simple_speech_synthesizer.pyo_converter.transform import transform as transform_pyo_converter
from simple_speech_synthesizer.acoustic_state.types import Input as InputAcousticState
from simple_speech_synthesizer.acoustic_state.transform import transform as transform_acoustic_state
from simple_speech_synthesizer.realization.types import Input as InputRealization
from simple_speech_synthesizer.realization.transform import transform as transform_realization
from simple_speech_synthesizer.synthesis.synthesis_types import Input as InputSynthesis
from simple_speech_synthesizer.synthesis.transform import transform as transform_synthesis

def process_targeting(input: InputTargeting, full_stack: bool = True):
    """
    Process the TARGETING layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return:
    """
    output = transform_targeting(input)
    if full_stack:
        output = process_pyo_converter(output)
    return output

def process_pyo_converter(input: InputPyoConverter) -> str:
    """
    Process the TARGETING layer. ALWAYS runs full stack.
    :param input: Input of the layer with the layer's own Input class.
    :return: The output filepath.
    """
    output = transform_pyo_converter(input)
    output = process_acoustic_state(output)
    return output

def process_acoustic_state(input: InputAcousticState):
    """
    Process the ACOUSTIC STATE (parametric simulation) layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return:
    """
    output = transform_acoustic_state(input)
    output = process_realization(output)
    return output

def process_realization(input: InputRealization):
    """
    Process the REALIZATION (middle-level parameter to synthesizer-level parameter converter) layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return:
    """
    output = transform_realization(input)
    output = process_synthesis(output)
    return output

def process_synthesis(input: InputSynthesis) -> str:
    """
    Process the SYNTHESIS (last) layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return: The filepath of the outputted audio file
    """
    output_filepath = transform_synthesis(input)
    return output_filepath


if __name__ == "__main__":
    from simple_speech_synthesizer.targeting.types import Input, TimedPhoneme, EnvelopeTargets
    from simple_speech_synthesizer.base.types import Envelope, Point, Segment

    from simple_speech_synthesizer.base.types import Envelope, Point, Segment

    i = Input(
        character_dir_path=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\characters\Greensparrow",
        output_filepath=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\testaudio.wav",
        duration=4,
        phonemes=(
            TimedPhoneme("<sil>", 0, 0.5),
            TimedPhoneme("hun_a", 0.5, 1),
            TimedPhoneme("hun_n", 1, 1.5),
            TimedPhoneme("hun_cs", 1.5, 2),
            TimedPhoneme("hun_a", 2, 2.5),
            TimedPhoneme("<sil>", 2.5, 3),
            TimedPhoneme("hun_a", 3, 3.11),
            TimedPhoneme("hun_n", 3.11, 3.25),
            TimedPhoneme("hun_cs", 3.25, 3.352),
            TimedPhoneme("hun_a", 3.352, 3.44),
            TimedPhoneme("<sil>", 3.44, 4),
        ),
        envelope_targets=EnvelopeTargets(
            Volume=Envelope((Point(0, -3), Point(3, -3)), (Segment("linear"),)),
            F0=Envelope((Point(0, 140), Point(3, 140), Point(3.25, 120)), (Segment("linear"), Segment("linear"),)),
            NasalityDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            BreathinessDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            Tension=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            MachineGrowl=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            LipRoundingDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            VocalGenderDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            ThroatJitter=Envelope((Point(0, 1), Point(3, 1)), (Segment("linear"),))
        )
    )
    o = process_targeting(i, full_stack=True)
    print(o)