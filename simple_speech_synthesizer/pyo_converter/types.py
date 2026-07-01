from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Targets, Envelope

@dataclass(frozen=True)
class Input:
    character_dir_path: str
    output_filepath: str
    duration: float
    # Phoneme targets
    vowel_formant_freqs_targets: tuple[Targets, ...]
    vowel_formant_importances_targets: tuple[Targets, ...]
    constriction_HP_freq_targets: Targets
    constriction_peak_freq_targets: Targets
    constriction_peak_bandwidth_targets: Targets
    constriction_peak_boost_targets: Targets
    constriction_peak_overtone_importance_targets: Targets
    constriction_LP_freq_targets: Targets
    vowel_importance_targets: Targets
    aspiration_importance_targets: Targets
    constriction_importance_targets: Targets
    nasality_targets: Targets
    # Global envelopes
    Volume: Envelope  # general singing volume in dB (0 means maximum, negatives count down)
    F0: Envelope  # fundamental pitch
    NasalityDelta: Envelope  # modifies the original nasality (since each phoneme has different levels of it by default)
    BreathinessDelta: Envelope  # modifies the original breathiness
    Tension: Envelope  # softness - hardness modifier
    MachineGrowl: Envelope  # lets the Blit run rampant
    LipRoundingDelta: Envelope  # WIP, may not be implemented; modifies the formants for liprounding
    VocalGenderDelta: Envelope  # modifies the perceived gender of the sound (similar to how other vocal synths use a gender property)
    # Throat jitter
    ThroatJitter: Envelope  # global multiplier for the throat jitter settings