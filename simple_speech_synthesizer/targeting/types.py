from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Envelope, Point, Segment

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
class EnvelopeTargets:
    """
    All targets that are stored as Envelopes.
    """
    Volume: Envelope  # general singing volume in dB (0 means maximum, negatives count down)
    F0: Envelope  # fundamental pitch
    NasalityDelta: Envelope  # modifies the original nasality (since each phoneme has different levels of it by default)
    BreathinessDelta: Envelope  # modifies the original breathiness
    Tension: Envelope  # softness - hardness modifier
    MachineGrowl: Envelope  # lets the Blit run rampant
    LipRoundingDelta: Envelope  # WIP, may not be implemented; modifies the formants for liprounding
    VocalGenderDelta: Envelope  # modifies the perceived gender of the sound (similar to how other vocal synths use a gender property)
    # Throat jitter
    ThroatJitter: Envelope  # global multiplier for the throat jitter settings


@dataclass(frozen=True)
class Input:
    """
    LAYER INPUT:
    The time t of each parameter is a float from 0 to `duration`, measured in elapsed seconds since the start of the utterance.
    :param character_dir_path: The path to the character's directory with the phoneme_data.json and manner_template.json (etc. if there are more) files.
    :param phonemes: All the phonemes as TimedPhoneme objects.
    :param envelope_targets: All the envelope targets as a single EnvelopeTargets object. THESE ARE PASSED DOWN WITHOUT MODIFICATION
    :param duration: The duration of the whole utterance, which is fixed by this point.
    """
    character_dir_path: str
    output_filepath: str
    duration: float
    phonemes: tuple[TimedPhoneme, ...]
    envelope_targets: EnvelopeTargets

    def __post_init__(self):
        for phoneme in self.phonemes:
            if not(0 <= phoneme.start < phoneme.end <= self.duration):
                raise ValueError("Phonemes out of range from [0, duration] in TARGETING LAYER Input.")
        """for envelope in self.global_envelopes.GETATTRIBUTESHERE:
            if not(0 <= envelope.min_t < envelope.max_t <= self.duration):
                raise ValueError("Envelope out of range from [0, duration] in TARGETING LAYER Input.")"""
        ## implement later
