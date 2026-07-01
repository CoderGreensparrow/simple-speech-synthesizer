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
    Constriction_HP_freq: Envelope
    Constriction_peak_freq: Envelope
    Constriction_peak_bandwidth: Envelope
    Constriction_peak_boost: Envelope
    Constriction_peak_overtone_importance: Envelope
    Constriction_LP_freq: Envelope
    #  Voice_to_noise_ratio: Envelope  This is replaced by individual Vowel, Aspiration and Constriction importances and Nasality
    Vowel_importance: Envelope
    Aspiration_importance: Envelope
    Constriction_importance: Envelope
    Nasality: Envelope
    # Global envelopes
    Volume: Envelope  # general singing volume in dB (0 means maximum, negatives count down)
    F0: Envelope  # fundamental pitch
    NasalityDelta: Envelope  # modifies the original nasality (since each phoneme has different levels of it by default)
    BreathinessDelta: Envelope  # modifies the original breathiness
    Tension: Envelope  # softness - hardness modifier
    MachineGrowl: Envelope  # lets the Blit run rampant
    LipRoundingDelta: Envelope  # WIP, may not be implemented; modifies the formants for liprounding
    VocalGenderDelta: Envelope  # modifies the perceived gender of the sound (similar to how other vocal synths use a gender property)


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