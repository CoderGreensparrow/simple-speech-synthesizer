"""
Functions for generating the subtargets for different manners of articulation with arguments from manner_data.json
**These are the true targeting functions.**
The functions are organized under a single class that can generate each manner of articulation by just selecting the right base_function.
"""

from simple_speech_synthesizer.targeting import types as this_layer_types
from simple_speech_synthesizer.acoustic_state import OLD_ORDER_types as next_layer_types

from simple_speech_synthesizer.acoustic_state.OLD_ORDER_types import AcousticTarget, SimplifiedFormant

from simple_speech_synthesizer.targeting.load_character import Character


def create_acoustic_targets(input: this_layer_types.Input, character: Character) -> tuple[next_layer_types.AcousticTarget, ...]:
    """
    Generates all targets (essentially the main function of the targeting layer).
    Calls a helper function create_one_phoneme for each phoneme.
    That helper function calls the appropriate manner-specific subtarget generator function.
    """
    acoustic_targets = list()
    for i in range(len(input.phonemes)):
        acoustic_targets.extend(
            create_one_phoneme(
                input.phonemes[i-1].ID if i - 1 > 0 else None,
                input.phonemes[i].ID,
                input.phonemes[i+1].ID if i + 1 < len(input.phonemes) else None,
                input.phonemes[i],
                character
            )
        )
    return acoustic_targets

def create_one_phoneme(prev_phoneme_ID: str | None, curr_phoneme_ID: str, next_phoneme_ID: str | None,
                       curr_phoneme: this_layer_types.TimedPhoneme, character: Character) -> tuple[AcousticTarget, ...]:
    """
    Generates non-changing targets, like vowels, fricatives, liquids etc., one singular phoneme.
    Calls the appropriate helper, manner-specific subtarget generator function.

    IMPORTANT: This is the place where high-level coarticulation happens.
    This function calculates the average of the vowel_formants of prev_phoneme, curr_phoneme and next_phoneme,
    and does the same to constriciton_formants.
    Then it calls the appropriate manner function.

    :param prev_phoneme_ID: Previous phoneme ID, if exists.
    :param curr_phoneme_ID: Current phoneme ID, if exists.
    :param next_phoneme_ID: Next phoneme ID, if exists.
    :param curr_phoneme: The current TimedPhoneme.
    :return: A list of AcousticTarget objects that is ready to be used by the lower layer.
    """

    # HIGH-LEVEL COARTICULATION

    ##### Phoneme blending rules
    # Not every phoneme has two surrounding phonemes.
    # Those that do not are handled a bit different.
    # Phonemes with only one partner have all of the "partner weight" (the weight that would distribute between the two surrounding phonemes)
    # put on the one singular partner.
    # Phonemes without partners are not coarticulated.

    ##### COARTICULATION CALCULATION ON FORMANT LEVEL
    # Each formant is averaged, which means that for each corresponding F1, F2, F3,
    # the frequencies, bandwidths and importances are taken with a mathematical weighted average.
    # The weight is determined by the vowel_coarticulation_coloring (V) and constriction_coarticulation_coloring (C) parameters.
    # Prev, curr, next weigths in order: V/2, 1-V, V/2
    # Since vowel_formants and constriction_formants' lengths are variable,
    # I account for that by only coarticulating formants that have corresponding other formants in the other surrounding phonemes.
    # So if /a/ has 5 vowel_formants, but /n/ only has 3, then the first 3 are coarticulated in /nan/, but the last two are not and kept unchanged, passed on without coarticulation.***
    # ***(other possible implementation: don't let it pass on without modification, coarticulate it with the non-existent formants in a way where those have importance=0, so the result is an attenuated formant. Freq and bandwidth are still passed on untouched.)

    # prev acoustic_params, IF EXISTS
    if prev_phoneme_ID is not None:
        acoustic_manner_params = character.phoneme_data[prev_phoneme_ID]
        prev_acoustic_params = character.acoustic_data[acoustic_manner_params["acoustic_parameter"]]
    # curr acoustic_params and manner_params
    acoustic_manner_params = character.phoneme_data[curr_phoneme_ID]
    curr_acoustic_params = character.acoustic_data[acoustic_manner_params["acoustic_parameter"]]
    curr_manner_params = character.manner_data[acoustic_manner_params["manner"]]
    # next acoustic_params, IF EXISTS
    if next_phoneme_ID is not None:
        acoustic_manner_params = character.phoneme_data[next_phoneme_ID]
        next_acoustic_params = character.acoustic_data[acoustic_manner_params["acoustic_parameter"]]

    V = curr_acoustic_params["vowel_coarticulation_coloring"]

    # CASES:
    # 1. If both surrounding phonemes exist: normal calculation.
    # 2. If one of the phonemes doesn't exist
    if prev_phoneme_ID is not None and next_phoneme_ID is None:
        next_acoustic_params = prev_acoustic_params
    elif prev_phoneme_ID is None and next_phoneme_ID is not None:
        prev_acoustic_params = next_acoustic_params
    # 3. if neither exists
    else:
        prev_acoustic_params = curr_acoustic_params
        next_acoustic_params = curr_acoustic_params


    # VOWEL FORMANTS
    vowel_formants = list()
    for i in range(len(curr_acoustic_params["vowel_formants"])):
        # a) if both surrounding formants exist (like F1 for i=0)
        if i < len(prev_acoustic_params["vowel_formants"]) and i < len(next_acoustic_params["vowel_formants"]):
            prev_formant = prev_acoustic_params["vowel_formants"][i]
            curr_formant = curr_acoustic_params["vowel_formants"][i]
            next_formant = next_acoustic_params["vowel_formants"][i]
        # b) if only one of the surrounding formants exist (like in /kan/, /a/ and /n/ have 4 formants, but /k/ has 3, then /a/'s F4 has to use only one formant for coarticulation.
        elif i < len(prev_acoustic_params["vowel_formants"]) or i < len(next_acoustic_params["vowel_formants"]):
            if i < len(prev_acoustic_params["vowel_formants"]):  # if its prev
                prev_formant = prev_acoustic_params["vowel_formants"][i]
                next_formant = prev_acoustic_params["vowel_formants"][i]
            else:  # if its next
                prev_formant = next_acoustic_params["vowel_formants"][i]
                next_formant = next_acoustic_params["vowel_formants"][i]
            curr_formant = curr_acoustic_params["vowel_formants"][i]
        # c) there's only one formant for this index: the current one.
        else:
            prev_formant = curr_acoustic_params["vowel_formants"][i]
            curr_formant = curr_acoustic_params["vowel_formants"][i]
            next_formant = curr_acoustic_params["vowel_formants"][i]
        # this may be some terrible code, but it can be updated later
        coarticulated_freq = (V / 2 * prev_formant["freq"] + (1 - V) * curr_formant["freq"] + V / 2 * next_formant["freq"])
        coarticulated_bandwidth = (V / 2 * prev_formant["bandwidth"] + (1 - V) * curr_formant["bandwidth"] + V / 2 * next_formant["bandwidth"])
        coarticulated_importance = (V / 2 * prev_formant["importance"] + (1 - V) * curr_formant["importance"] + V / 2 * next_formant["importance"])

        vowel_formants.append({
            "freq": coarticulated_freq,
            "bandwidth": coarticulated_bandwidth,
            "importance": coarticulated_importance
        })


    # CONSTRICITON FORMANTS (not DRY)
    constriction_formants = list()
    for i in range(len(curr_acoustic_params["constriction_formants"])):
        # a) if both surrounding formants exist (like F1 for i=0)
        if i < len(prev_acoustic_params["constriction_formants"]) and i < len(next_acoustic_params["constriction_formants"]):
            prev_formant = prev_acoustic_params["constriction_formants"][i]
            curr_formant = curr_acoustic_params["constriction_formants"][i]
            next_formant = next_acoustic_params["constriction_formants"][i]
        # b) if only one of the surrounding formants exist (like in /kan/, /a/ and /n/ have 4 formants, but /k/ has 3, then /a/'s F4 has to use only one formant for coarticulation.
        elif i < len(prev_acoustic_params["constriction_formants"]) or i < len(next_acoustic_params["constriction_formants"]):
            if i < len(prev_acoustic_params["constriction_formants"]):  # if its prev
                prev_formant = prev_acoustic_params["constriction_formants"][i]
                next_formant = prev_acoustic_params["constriction_formants"][i]
            else:  # if its next
                prev_formant = next_acoustic_params["constriction_formants"][i]
                next_formant = next_acoustic_params["constriction_formants"][i]
            curr_formant = curr_acoustic_params["constriction_formants"][i]
        # c) there's only one formant for this index: the current one.
        else:
            prev_formant = curr_acoustic_params["constriction_formants"][i]
            curr_formant = curr_acoustic_params["constriction_formants"][i]
            next_formant = curr_acoustic_params["constriction_formants"][i]
        # yes this is pretty inefficient for the last case
        coarticulated_freq = (V / 2 * prev_formant["freq"] + (1 - V) * curr_formant["freq"] + V / 2 * next_formant["freq"])
        coarticulated_bandwidth = (V / 2 * prev_formant["bandwidth"] + (1 - V) * curr_formant["bandwidth"] + V / 2 * next_formant["bandwidth"])
        coarticulated_importance = (V / 2 * prev_formant["importance"] + (1 - V) * curr_formant["importance"] + V / 2 * next_formant["importance"])

        constriction_formants.append({
            "freq": coarticulated_freq,
            "bandwidth": coarticulated_bandwidth,
            "importance": coarticulated_importance
        })


    # FINALIZED ACOUSTIC PARAMS IN THE JSON file's format
    coarticulated_acoustic_params = {
        "vowel_formants": vowel_formants,
        "constriction_formants": constriction_formants,
    }


    # CALLING MANNER FUNCTION
    only_manner_parameters = curr_manner_params["parameters"]
    if curr_manner_params["base_function"] == "flow":
        return flow(curr_phoneme, coarticulated_acoustic_params, only_manner_parameters)


def flow(phoneme: this_layer_types.TimedPhoneme, acoustic_params, manner_params):
    """
    INTERNAL, manner function, basic airflow (vowels, fricatives, nasals, liquids etc.)
    :param phoneme: The TimedPhoneme object of the current phoneme.
    :param acoustic_params: The acoustic params. Only needed ones are vowel_formants and constriction_formants.
    :param manner_params: The "parameters" field of the manner's params. (So the base_function is not needed.)
    :return: A list of acoustic targets ready to be used. Here's where the real targeting happens.
    """
    vowel_formants = list()
    for vowel_formant in acoustic_params["vowel_formants"]:
        vowel_formants.append(
            SimplifiedFormant(vowel_formant["freq"],
                              vowel_formant["bandwidth"],
                              vowel_formant["importance"]))
    constriction_formants = list()
    for constriction_formant in acoustic_params["constriction_formants"]:
        constriction_formants.append(
            SimplifiedFormant(constriction_formant["freq"],
                              constriction_formant["bandwidth"],
                              constriction_formant["importance"]))
    voice_to_noise_ratio = manner_params["voice_to_noise_ratio"]
    constriction = manner_params["constriction"]
    nasality = manner_params["nasality"]
    return tuple([
        AcousticTarget(
            t=phoneme.start,
            vowel_formants=tuple(vowel_formants),
            constriction_formants=tuple(constriction_formants),
            voice_to_noise_ratio=voice_to_noise_ratio,
            constriction=constriction,
            nasality=nasality
        )
    ])