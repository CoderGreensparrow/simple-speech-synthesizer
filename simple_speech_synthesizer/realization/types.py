from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Envelope

@dataclass(frozen=True)
class FormantEnvelope:
    """
    Represents the grouping of the freq and bandw Envelopes of a formants.
    Technically, the two envelopes are still separate, this may just be an abstraction that will get
    unabstracted by the realization layer anyways.
    """
    freq: Envelope
    bandwidth: Envelope
    importance: Envelope


@dataclass(frozen=True)
class HighLevelEnvelopes:
    """
    Every single parameter of the synthesizer, now all converted to envelopes by the last layer,
    passed in this one single input class.
    All envelopes come from the simulation now, even the ones with envelopes (those envelopes where "envelope targets",
    which controlled the simulation, where the simulation tried to recreate the envelopes.
    """
    # Envelopes, simulated from acoustic targets
    Vowel_formants: tuple[FormantEnvelope, ...]
    Constriction_formants: tuple[FormantEnvelope, ...]
    Voice_to_noise_ratio: Envelope
    Constriction: Envelope
    Nasality: Envelope
    # Global envelopes
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
    The stuff from GlobalEnvelopeTargets is passed to here without ANY modifications from the previous layer!
    :param high_level_envelopes: All the acoustic state envelopes (global, and simulated) in an object.
    :param duration: The duration of the whole utterance, which is fixed by this point. PASSED UNMODIFIED FROM THE LAST LAYER.
    """
    character_dir_path: str
    high_level_envelopes: HighLevelEnvelopes
    duration: float