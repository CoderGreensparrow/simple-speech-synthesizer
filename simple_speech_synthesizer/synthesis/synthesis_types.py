# The file had to be renamed to avoid conflict with the internal naming of pyo

from dataclasses import dataclass
from collections.abc import Sequence

import pyo

# TODO: Rn every interpolation type is Linseg, this may stay like this

@dataclass(frozen=True)
class Input:
    """
    The Inputs to this layer must be formatted as lists of points, or lists of lists of points, as demanded.
    The inputs are directly passed to pyo.Linseg (so the input has to be pyo-compatible).
    Except for scalar inputs.
    """
    # metaparams
    character_dir_path: str
    output_filepath: str
    duration: float
    # Phoneme synthesis
    Vowel_formant_freqs: Sequence[Sequence[tuple[float, float]]]
    Constriction_HP_freq: Sequence[tuple[float, float]]
    Constriction_peak_freq: Sequence[tuple[float, float]]
    Constriction_peak_bandwidth: Sequence[tuple[float, float]]
    Constriction_peak_boost: Sequence[tuple[float, float]]
    Constriction_peak_overtone_importance: Sequence[tuple[float, float]]
    Constriction_LP_freq: Sequence[tuple[float, float]]
    # (Technically global Envelopes)
    Voiced_component_importance: Sequence[tuple[float, float]]
    Constriction_component_importance: Sequence[tuple[float, float]]
    Aspiration_component_importance: Sequence[tuple[float, float]]
    # Global Envelopes
    Volume: Sequence[tuple[float, float]]
    F0: Sequence[tuple[float, float]]
    Spectral_tilt_cutoff_delta: Sequence[tuple[float, float]]
    Spectral_tilt_tension: Sequence[tuple[float, float]]
    #  Spectral_hill_freq_deltafactor: Sequence[tuple[float, float]]
    Spectral_hill_boost_delta: Sequence[tuple[float, float]]
    Vowel_Q_multiplier: Sequence[tuple[float, float]]
    Aspiration_volume_factor: Sequence[tuple[float, float]]
    Constriction_volume_factor: Sequence[tuple[float, float]]
    Nasal_murmur_importance: Sequence[tuple[float, float]]
    Nasality_LP_strength: Sequence[tuple[float, float]]
    Nasality_antiformant_boost: Sequence[tuple[float, float]]
    # scalar parameters
    F0_freq_sway: float  # these are percentages from 0 to 1 (unbounded)
    F0_freq_FM_jitter: float
    voice_source_amp_sway: float

