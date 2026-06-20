from simple_speech_synthesizer.targeting.types import Input as InputTargeting
from simple_speech_synthesizer.targeting.transform import transform as transform_targeting
from simple_speech_synthesizer.acoustic_state.types import Input as InputAcousticState
from simple_speech_synthesizer.acoustic_state.transform import transform as transform_acoustic_state
from simple_speech_synthesizer.realization.types import Input as InputRealization

def process_targeting(input: InputTargeting, full_stack: bool = True):
    """
    Process the TARGETING layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return:
    """
    output = transform_targeting(input)
    if full_stack:
        output = process_acoustic_state(output, full_stack=True)
    return output

def process_acoustic_state(input: InputAcousticState, full_stack: bool = True):
    """
    Process the ACOUSTIC STATE (parametric simulation) layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return:
    """
    output = transform_acoustic_state(input)
    if full_stack:
        ...
        #  output = process_realization(output, full_stack=True)
    return output




if __name__ == "__main__":
    from simple_speech_synthesizer.targeting.types import Input, TimedPhoneme, GlobalEnvelopeTargets
    from simple_speech_synthesizer.base.types import Envelope, Point, Segment

    i = Input(
        character_dir_path=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\characters\Greensparrow",
        phonemes=(TimedPhoneme("s", 0, 0.089), TimedPhoneme("a", 0.089, 0.089+0.165), TimedPhoneme("s", 0.089+0.165, 0.089+0.165+0.11)),
        global_envelope_targets=GlobalEnvelopeTargets(
            F0=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1 / 2}),)),
            NasalityDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1 / 2}),)),
            BreathinessDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1 / 2}),)),
            Tension=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1 / 2}),)),
            VocalTilt=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1 / 2}),)),
            LipRoundingDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1 / 2}),)),
            GenderDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1 / 2}),)),
            Volume=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1 / 2}),)),
        ),
        duration=0.089+0.165+0.11
    )
    o = process_targeting(i, full_stack=True)

    import matplotlib.pyplot as plt

    for i in range(len(o.high_level_envelopes.Vowel_formants)):
        x = [point.t for point in o.high_level_envelopes.Vowel_formants[i].freq.points]
        y = [point.v for point in o.high_level_envelopes.Vowel_formants[i].freq.points]
        plt.scatter(x, y)

    x = [point.t for point in o.high_level_envelopes.Constriction.points]
    y = [point.v for point in o.high_level_envelopes.Constriction.points]
    plt.scatter(x, y)

    plt.show()