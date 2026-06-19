from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Envelope, Point, Segment

from simple_speech_synthesizer.acoustic_state.types import GlobalEnvelopeTargets

@dataclass(frozen=True)
class TimedPhoneme:
    """
    Phoneme class used by targeting. Features all information required for targeting.
    """
    ID: str
    start: float  # time elapsed since start of current utterance block
    end: float  # similarly

    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError("The start and end of a TimePhoneme must be in order in time and not be equal. (start < end)")

@dataclass(frozen=True)
class Input:
    """
    LAYER INPUT:
    The time t of each parameter is a float from 0 to `duration`, measured in elapsed seconds since the start of the utterance.
    :param character_dir_path: The path to the character's directory with the phoneme_data.json and manner_template.json (etc. if there are more) files.
    :param phonemes: All the phonemes as TimedPhoneme objects.
    :param global_envelope_targets: All the global envelopes as a single GlobalEnvelopeTargets object.
    :param duration: The duration of the whole utterance, which is fixed by this point.
    """
    character_dir_path: str
    phonemes: tuple[TimedPhoneme, ...]
    global_envelope_targets: GlobalEnvelopeTargets
    duration: float

    def __post_init__(self):
        for phoneme in self.phonemes:
            if not(0 <= phoneme.start < phoneme.end <= self.duration):
                raise ValueError("Phonemes out of range from [0, duration] in TARGETING LAYER Input.")
        """for envelope in self.global_envelopes.GETATTRIBUTESHERE:
            if not(0 <= envelope.min_t < envelope.max_t <= self.duration):
                raise ValueError("Envelope out of range from [0, duration] in TARGETING LAYER Input.")"""
        ## implement later


if __name__ == "__main__":
    i = Input(
        phonemes=(TimedPhoneme("t", 0, 0.1), TimedPhoneme("a", 0.1, 0.7), TimedPhoneme("s", 0.7, 0.8)),
        global_envelope_targets=GlobalEnvelopeTargets(
            F0=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            NasalityDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            BreathinessDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            Tension=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            VocalTilt=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            LipRoundingDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),)),
            GenderDelta=Envelope((Point(0, 0), Point(2, 0.5)), (Segment("polynomial", {"exponent": 1/2}),))
        ),
        duration=0.8
    )
    print(i)