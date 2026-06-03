from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Envelope, Point, Segment

@dataclass(frozen=True)
class SimplifiedFormant:
    """
    Formant information without formant amplitude/gain.
    When used as a delta, each component acts as a delta on another SimplifiedFormant object's corresponding parameters.
    """
    freq: float
    """in Hz"""
    bandwidth: float
    """in Hz"""

    def __post_init__(self):
        if self.freq < 0:
            raise ValueError("freq must be positive in SimplifiedFormant")
        if self.bandwidth < 0:
            raise ValueError("bandwidth must be positive in SimplifiedFormant")


@dataclass(frozen=True)
class AcousticTarget:
    """
    The acoustic state parameters of the nonexistent mouth, at least one target at one t point in time.
    TECHNICALLY, this is a "POINT-IN-TIME TARGET", which means the dynamics of the mouth will aim for the next,
    the next, and then the next target, as t time progresses.
    This is the first type of target used, the other one is "ENVELOPE TARGETS", aka. the GlobalEnvelopeTarget class.
    :param t: The timecode of the acoustic state target.
    :param formants: The list of formants to be applied at that point in time, in order F1, F2, F3 etc.
    :param vocal_ratio: How much the vocal chords are activated in the synthesis, range from 0 to 1, where 0 means no voiceless component of the phoneme, 1 means fully engaged voiced component of the phoneme.
    :param noise_ratio: How much noise (breathiness, voiceless component) are activated in synthesis, range from 0 to 1, where 0 means no voiceless component, and 1 means fully engaged voiceless component.
    """
    t: float
    formants: tuple[SimplifiedFormant, ...]
    vocal_ratio: float
    noise_ratio: float

    def __post_init__(self):
        if not (0 <= self.vocal_ratio <= 1 and 0 <= self.noise_ratio <= 1):
            raise ValueError("vocal_ratio and noise_ratio must be between 0 and 1 in AcousticTarget")


@dataclass(frozen=True)
class GlobalEnvelopeTargets:
    """
    Every other parameter that requires a "global" envelope (envelopes at an utterance level).
    TECHNICALLY, this is an "ENVELOPE TARGET", which means that this won't be exactly the envelope followed, but
    the dynamics of the mouth will try to follow along to these curves.
    This is the second type of target used, the other is "POINT-IN-TIME TARGETS", aka. the AcousticTarget class.
    :param Volume: Semantic volume of the singing, so not in dB, but rather a range of values from 0 to 2, where -1 means pp (pianissimo), 0 is normal volume, 1 means fortissimo (these are relative, and depend on the character selected).
    :param F0: Fundamental pitch envelope in Hz.
    :param NasalityDelta: Adds or removes some nasality from the formants. TO BE DEFINED LATER.
    :param BreathinessDelta: Adds or removes some breathiness. TO BE DEFINED LATER.
    :param Tension: Controls vocal chord tension. TO BE DEFINED LATER.
    :param VocalTilt: Adds or removes some vocal tilt. TO BE DEFINED LATER, possibly Hz.
    :param LipRoundingDelta: Adds or removes some lip rounding. TO BE DEFINED LATER.
    :param GenderDelta: Genderbends the vocals. TO BE DEFINED LATER.
    """
    Volume: Envelope  # general singing volume
    F0: Envelope  # fundamental pitch
    NasalityDelta: Envelope  # modifies the original nasality (since each phoneme has different levels of it by default)
    BreathinessDelta: Envelope  # modifies the original breathiness
    Tension: Envelope  # vocal chord tension
    VocalTilt: Envelope  # vocal tilt
    LipRoundingDelta: Envelope  # modifies LipRound (lass rounded than normal, more rounded than normal)
    GenderDelta: Envelope  # modifies the perceived gender of the sound (similar to how other vocal synths use a gender property)


@dataclass(frozen=True)
class Input:
    """
    LAYER INPUT:
    GlobalEnvelopeTargets is passed to here without ANY modifications from the previous layer!
    The time t of each parameter is a float from 0 to `duration`, measured in elapsed seconds since the start of the utterance.
    :param acoustic_targets: All the acoustic state targets in a tuple.
    :param global_envelopes: All the global envelopes as a single GlobalEnvelopeTargets object. PASSED UNMODIFIED FROM THE LAST LAYER.
    :param duration: The duration of the whole utterance, which is fixed by this point. PASSED UNMODIFIED FROM THE LAST LAYER.
    """
    acoustic_targets: tuple[AcousticTarget, ...]
    global_envelope_targets: GlobalEnvelopeTargets
    duration: float

    def __post_init__(self):
        for prev, curr in zip(self.acoustic_targets, self.acoustic_targets[1:]):
            if curr.t <= prev.t:
                raise ValueError("Acoustic targets must be strictly increasing in time.")


if __name__ == "__main__":
    i = Input(
        acoustic_targets=(
            AcousticTarget(0, (SimplifiedFormant(330, 100),), 1, 0),
            AcousticTarget(1, (SimplifiedFormant(330, 100),), 1, 0),
            AcousticTarget(2, (SimplifiedFormant(330, 100),), 1, 0),
            AcousticTarget(3, (SimplifiedFormant(330, 100),), 1, 0),
            AcousticTarget(4, (SimplifiedFormant(330, 100),), 1, 0),
            AcousticTarget(5, (SimplifiedFormant(330, 100),), 1, 0),
            AcousticTarget(6, (SimplifiedFormant(330, 100),), 1, 0),
        ),
        global_envelope_targets=GlobalEnvelopeTargets(
            Volume=Envelope((Point(0, 0), Point(2, 0)), (Segment("linear"),)),
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