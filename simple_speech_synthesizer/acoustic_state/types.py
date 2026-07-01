from dataclasses import dataclass
from collections.abc import Sequence

from pyo import Server, Linseg

@dataclass(frozen=True)
class Input:
    """
    LAYER INPUT:
    The stuff from GlobalEnvelopeTargets is passed to here without ANY modifications from the previous layer!
    :param high_level_envelopes: All the acoustic state envelopes (global, and simulated) in an object.
    :param duration: The duration of the whole utterance, which is fixed by this point. PASSED UNMODIFIED FROM THE LAST LAYER.
    """
    server: Server
    character_dir_path: str
    output_filepath: str
    duration: float
    # Envelopes, simulated from acoustic targets
    Vowel_formant_freqs: Sequence[Linseg]
    Vowel_formant_importances: Sequence[Linseg]
    Constriction_HP_freq: Linseg
    Constriction_peak_freq: Linseg
    Constriction_peak_bandwidth: Linseg
    Constriction_peak_boost: Linseg
    Constriction_peak_overtone_importance: Linseg
    Constriction_LP_freq: Linseg
    #  Voice_to_noise_ratio: Envelope  This is replaced by individual Vowel, Aspiration and Constriction importances and Nasality
    Vowel_importance: Linseg
    Aspiration_importance: Linseg
    Constriction_importance: Linseg
    Nasality: Linseg
    # Global envelopes
    Volume: Linseg  # general singing volume in dB (0 means maximum, negatives count down)
    F0: Linseg  # fundamental pitch
    NasalityDelta: Linseg  # modifies the original nasality (since each phoneme has different levels of it by default)
    BreathinessDelta: Linseg  # modifies the original breathiness
    Tension: Linseg  # softness - hardness modifier
    MachineGrowl: Linseg  # lets the Blit run rampant
    LipRoundingDelta: Linseg  # WIP, may not be implemented; modifies the formants for liprounding
    VocalGenderDelta: Linseg  # modifies the perceived gender of the sound (similar to how other vocal synths use a gender property)
    # Throat jitter
    ThroatJitter: Linseg  # global multiplier for the throat jitter settings
