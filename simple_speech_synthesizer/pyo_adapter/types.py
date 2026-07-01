from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Envelope

import pyo

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
    Vowel_formant_freqs: tuple[Envelope, ...]
    Constriction_HP_freq: Envelope
    Constriction_peak_freq: Envelope
    Constriction_peak_bandwidth: Envelope
    Constriction_peak_boost: Envelope
    Constriction_peak_overtone_importance: Envelope
    Constriction_LP_freq: Envelope
    # (Technically global Envelopes)
    Voiced_component_importance: Envelope
    Constriction_component_importance: Envelope
    Aspiration_component_importance: Envelope
    # Global Envelopes
    Volume: Envelope
    F0: Envelope
    Spectral_tilt_cutoff_delta: Envelope
    Spectral_tilt_tension: Envelope
    #  Spectral_hill_freq_deltafactor: Envelope
    Spectral_hill_boost_delta: Envelope
    Vowel_Q_multiplier: Envelope
    Aspiration_volume_factor: Envelope
    Constriction_volume_factor: Envelope
    Nasal_murmur_importance: Envelope
    Nasality_LP_strength: Envelope
    Nasality_antiformant_boost: Envelope
    # Throat jitter
    F0_freq_sway: Envelope  # these are percentages from 0 to 1 (unbounded)
    F0_freq_FM_jitter: Envelope
    voice_source_amp_sway: Envelope

