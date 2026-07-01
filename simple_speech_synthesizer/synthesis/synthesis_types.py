# The file had to be renamed to avoid conflict with the internal naming of pyo

from dataclasses import dataclass
from collections.abc import Sequence

from pyo import Server, PyoObject

# TODO: Rn every interpolation type is Linseg, this may stay like this
#       NOTE: Everything WILL stay like this... I will NOT implement different interpolations, it doesn't make sense.

@dataclass(frozen=True)
class Input:
    """
    The Inputs to this layer must be formatted as lists of points, or lists of lists of points, as demanded.
    The inputs are directly passed to pyo.Linseg (so the input has to be pyo-compatible).
    Except for scalar inputs.
    """
    server: Server
    # metaparams
    character_dir_path: str
    output_filepath: str
    duration: float
    # Phoneme synthesis
    Vowel_formant_freqs: Sequence[PyoObject]
    Vowel_formant_importances: Sequence[PyoObject]
    Constriction_HP_freq: PyoObject
    Constriction_peak_freq: PyoObject
    Constriction_peak_bandwidth: PyoObject
    Constriction_peak_boost: PyoObject
    Constriction_peak_overtone_importance: PyoObject
    Constriction_LP_freq: PyoObject
    # (Technically global Envelopes)
    Voiced_component_importance: PyoObject
    Constriction_component_importance: PyoObject
    Aspiration_component_importance: PyoObject
    # Global Envelopes
    Volume: PyoObject
    F0: PyoObject
    Spectral_tilt_cutoff_delta: PyoObject
    Spectral_tilt_tension: PyoObject
    #  Spectral_hill_freq_deltafactor: PyoObject
    Spectral_hill_boost_delta: PyoObject
    Vowel_Q_multiplier: PyoObject
    Aspiration_volume_factor: PyoObject
    Constriction_volume_factor: PyoObject
    Nasal_murmur_importance: PyoObject
    Nasality_LP_strength: PyoObject
    Nasality_antiformant_boost: PyoObject
    # Throat jitter
    F0_freq_sway: PyoObject  # these are percentages from 0 to 1 (unbounded)
    F0_freq_FM_jitter: PyoObject
    voice_source_amp_sway: PyoObject

