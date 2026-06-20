import pyo

# TODO: Rn every interpolation type is Linseg, this may stay like this

class Input:
    # metaparams
    output_filepath: str
    duration: float
    # Phoneme synthesis
    Vowel_formant_freqs: tuple[pyo.Linseg, ...]
    Vowel_formant_qs: tuple[pyo.Linseg, ...]
    Vowel_formant_muls: tuple[pyo.Linseg, ...]
    Constriction_formant_freqs: tuple[pyo.Linseg, ...]
    Constriction_formant_qs: tuple[pyo.Linseg, ...]
    Constriction_formant_muls: tuple[pyo.Linseg, ...]
    Voiced_component_mul: pyo.Linseg
    Voiceless_component_mul: pyo.Linseg
    # Global Envelopes
    Volume: pyo.Linseg
    F0: pyo.Linseg
    VocalTiltDelta: pyo.Linseg
    Tension: pyo.Linseg
    # scalar parameters
    F0_freq_sway: float  # these are percentages from 0 to 1 (unbounded)
    F0_freq_FM_jitter: float
    voice_source_amp_sway: float

