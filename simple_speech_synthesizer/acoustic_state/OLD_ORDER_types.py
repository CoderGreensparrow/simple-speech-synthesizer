from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Envelope, Point, Segment

@dataclass(frozen=True)
class SimplifiedFormant:
    """
    Formant information with formant amplitude/gain.
    When used as a delta, each component acts as a delta on another SimplifiedFormant object's corresponding parameters.
    """
    freq: float
    """in Hz"""
    bandwidth: float
    """in Hz"""
    importance: float
    """semantic amplitude"""

    def __post_init__(self):
        if self.freq < 0:
            raise ValueError(f"freq must be positive in SimplifiedFormant; given {self.freq}")
        if self.bandwidth < 0:
            raise ValueError(f"bandwidth must be positive in SimplifiedFormant; given {self.bandwidth}")
        if 0 < self.importance and self.importance > 1:
            raise ValueError(f"importance must be between 0 and 1 (percentage) in SimplifiedFormant; given {self.importance}")


@dataclass(frozen=True)
class AcousticTarget:
    """
    The acoustic state parameters of the nonexistent mouth, at least one target at one t point in time.
    TECHNICALLY, this is a "POINT-IN-TIME TARGET", which means the dynamics of the mouth will aim for the next,
    the next, and then the next target, as t time progresses.
    This is the first type of target used, the other one is "ENVELOPE TARGETS", aka. the GlobalEnvelopeTarget class.

    IMPORTANT SYSTEM KNOWLEDGE:
    I. CONSTRICTION
    - the voice source is affected by both vowel_formants (strongly) and constriction_formants (weaker), latter introduced by constriction.
    - the noise source is affected WEAKLY by the vowel_formants all the time, and by constriction_formants STRONGLY, latter introduced by constriction.
    So overall, constriction is only a semantic volume of how much constriction is happening.

    II. NASALITY
    'Nasality needs no special system of formants for each consonant.
    I just take an existing set of parameters, lower the importance of lower frequency formants,
    up the bandwidth of vowel formants, add a "nasal formant" (or nasal murmur) around 250 Hz,
    apply some dampening to everything that is higher frequency than about 500 Hz (I just observed this on a spectrogram of me saying nasal stuff),
    and BAM, nasality implemented.
    This means I could have nasality as just a single slider that does all of that on a low level.'

    This also means PHONEMES ARE STORED NOT AS VOWELS OR CONSONANTS SEPARATELY, rather
    as ***TONGUE POSITIONS*** or SOMETHING SIMILAR, where /i/ and /ç/ have the same vowel_ and constriction_formants,
    just differing levels of voice_to_noise_ratio and constriction. (Or they are just duplicated in the lookup table with only those two parameters differing.)

    :param t: The timecode of the acoustic state target.
    :param vowel_formants: The list of formants to be applied at that point in time, in order F1, F2, F3 etc. These are VOWEL-LIKE in quality.
    :param constriction_formants: The lise of "formants" or spectral peaks to be applied at t, in order S1, S2, S3 etc. These are FRICATIVE-LIKE resonances.
    :param voice_to_noise_ratio: The ratio of "how much is this a voiced vowel" (at 0) to "how much is this a fully voiceless consonant" (at 1) with "voiced consonants" somewhere in between the two. Essentially controls the ratio of volume between the two sources: vocal source and noise source.
    :param constriction: float from 0 to 1. Percentage that sets how much "constriction" happens for consonants. It essentially acts like a global semantic volume for the contriction_peaks.
    :param nasality: float from 0 to 1, controls a simple set of modifications to all of the existing sound.
    """
    t: float
    vowel_formants: tuple[SimplifiedFormant, ...]
    constriction_formants: tuple[SimplifiedFormant, ...]
    voice_to_noise_ratio: float
    constriction: float
    nasality: float

    def __post_init__(self):
        if not (0 <= self.voice_to_noise_ratio <= 1):
            raise ValueError("voice_to_noise_ratio must be between 0 and 1 in AcousticTarget")


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
    :param global_envelope_targets: All the global envelopes as a single GlobalEnvelopeTargets object. PASSED UNMODIFIED FROM THE LAST LAYER.
    :param duration: The duration of the whole utterance, which is fixed by this point. PASSED UNMODIFIED FROM THE LAST LAYER.
    """
    character_dir_path: str
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