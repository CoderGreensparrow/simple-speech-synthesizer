# The file had to be renamed to avoid conflict with the internal naming of pyo

from dataclasses import dataclass
from collections.abc import Sequence

from pyo import Server, Linseg

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
    Vowel_formant_freqs: Sequence[Linseg]
    Vowel_formant_importances: Sequence[Linseg]
    Constriction_HP_freq: Linseg
    Constriction_peak_freq: Linseg
    Constriction_peak_bandwidth: Linseg
    Constriction_peak_boost: Linseg
    Constriction_peak_overtone_importance: Linseg
    Constriction_LP_freq: Linseg
    # (Technically global Envelopes)
    Voiced_component_importance: Linseg
    Constriction_component_importance: Linseg
    Aspiration_component_importance: Linseg
    # Global Envelopes
    Volume: Linseg
    F0: Linseg
    Spectral_tilt_cutoff_delta: Linseg
    Spectral_tilt_tension: Linseg
    #  Spectral_hill_freq_deltafactor: Linseg
    Spectral_hill_boost_delta: Linseg
    Vowel_Q_multiplier: Linseg
    Aspiration_volume_factor: Linseg
    Constriction_volume_factor: Linseg
    Nasal_murmur_importance: Linseg
    Nasality_LP_strength: Linseg
    Nasality_antiformant_boost: Linseg
    # Throat jitter
    F0_freq_sway: Linseg  # these are percentages from 0 to 1 (unbounded)
    F0_freq_FM_jitter: Linseg
    voice_source_amp_sway: Linseg

