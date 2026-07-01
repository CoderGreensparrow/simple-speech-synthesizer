from pyo import Server, PyoObject
from collections.abc import Sequence

from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Envelope

'''@dataclass(frozen=True)
class FormantEnvelope:
    """
    Represents the grouping of the freq and bandwidth Envelopes of a formants.
    Technically, the two envelopes are still separate, this may just be an abstraction that will get
    unabstracted by the realization layer anyways.
    """
    freq: Envelope
    bandwidth: Envelope
    importance: Envelope'''  # TODO: rewrite all code relating to this and then delete it


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
    Vowel_formant_freqs: Sequence[PyoObject]
    Vowel_formant_importances: Sequence[PyoObject]
    Constriction_HP_freq: PyoObject
    Constriction_peak_freq: PyoObject
    Constriction_peak_bandwidth: PyoObject
    Constriction_peak_boost: PyoObject
    Constriction_peak_overtone_importance: PyoObject
    Constriction_LP_freq: PyoObject
    #  Voice_to_noise_ratio: Envelope  This is replaced by individual Vowel, Aspiration and Constriction importances and Nasality
    Vowel_importance: PyoObject
    Aspiration_importance: PyoObject
    Constriction_importance: PyoObject
    Nasality: PyoObject
    # Global envelopes
    Volume: PyoObject  # general singing volume in dB (0 means maximum, negatives count down)
    F0: PyoObject  # fundamental pitch
    NasalityDelta: PyoObject  # modifies the original nasality (since each phoneme has different levels of it by default)
    BreathinessDelta: PyoObject  # modifies the original breathiness
    Tension: PyoObject  # softness - hardness modifier
    MachineGrowl: PyoObject  # lets the Blit run rampant
    LipRoundingDelta: PyoObject  # WIP, may not be implemented; modifies the formants for liprounding
    VocalGenderDelta: PyoObject  # modifies the perceived gender of the sound (similar to how other vocal synths use a gender property)
    # Throat jitter
    ThroatJitter: PyoObject  # global multiplier for the throat jitter settings
