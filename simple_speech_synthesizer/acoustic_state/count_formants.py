from simple_speech_synthesizer.acoustic_state.types import AcousticTarget

def max_num_of_formants_in_targets(acoustic_targets: tuple[AcousticTarget, ...]):
    """
    Counts the max number of vowel and constriction formants in the acoustic_targets separately.
    :param acoustic_targets: The acoustic_targets in this layer's Input.
    :return: The max_vowel_formants and max_constriction_formants.
    """

    max_vowel_formants = 0
    max_constriction_formants = 0

    for target in acoustic_targets:
        curr_vowel_formants = len(target.vowel_formants)
        if curr_vowel_formants > max_vowel_formants: max_vowel_formants = curr_vowel_formants
        curr_constriction_formants = len(target.constriction_formants)
        if curr_constriction_formants > max_constriction_formants: max_constriction_formants = curr_constriction_formants

    return max_vowel_formants, max_constriction_formants