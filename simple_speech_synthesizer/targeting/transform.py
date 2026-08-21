"""
SYNTHESIS LAYER 2: Creates the acoustic targets for the nonexistent mouth.
It knows nothing about prosody. It takes prosody-included phonemic input data, and converts that to formant parameters and vocal amplitudes.
"""

from simple_speech_synthesizer.targeting import types as this_layer_types
from simple_speech_synthesizer.pyo_converter import types as next_layer_types

from simple_speech_synthesizer.base.load_character import load_character
from simple_speech_synthesizer.base.types import Targets, FormantTargets

from pprint import pprint

class Targeter:
    def __init__(self, input_: this_layer_types.Input):
        self.in_ = input_
        character = load_character(input_.character_dir_path)
        self.phoneme_d = character.phoneme_data
        self.articulation_d = character.articulation_data
        # OUTPUTS
        self.vowel_formant_freqs_targets = None
        self.constriction_HP_freq_targets = None
        self.constriction_peak_freq_targets = None
        self.constriction_peak_bandwidth_targets = None
        self.constriction_peak_boost_targets = None
        self.constriction_peak_overtone_importance_targets = None
        self.constriction_LP_freq_targets = None
        self.vowel_importance_targets = None
        self.aspiration_importance_targets = None
        self.constriction_importance_targets = None
        self.nasality_targets = None
        self.oral_closure_targets = None  # treated by manner function specifically
        self.stop_amp_targets = None  # treated by manner function specifically
        self.nasality_antiformant_freq_for_nasal_consonants_targets = None
        self.nasality_antiformant_bandwidth_for_nasal_consonants_targets = None
        self.nasality_antiformant_boost_for_nasal_consonants_targets = None

        # These contain information about
        # which constriciton parameters should be coarticulated or not (the keys).
        # And the values are the names of the parameters in the Input
        # (because the parameter names in the json and the Input are different).
        self.coarticulated_constriction_parameter_names = {
            "low_end": "constriction_HP_freq_targets",
            "high_end": "constriction_LP_freq_targets",
            "peak_frequency": "constriction_peak_freq_targets",
            "peak_bandwidth": "constriction_peak_bandwidth_targets"
        }
        self.non_coarticulated_constriction_parameter_names = {
            "boost": "constriction_peak_boost_targets",
            "overtone_importance": "constriction_peak_overtone_importance_targets"
        }
        self.nasalization_parameter_names = {
            "antiformant_freq": "nasality_antiformant_freq_for_nasal_consonants_targets",
            "antiformant_bandwidth": "nasality_antiformant_bandwidth_for_nasal_consonants_targets",
            "antiformant_boost": "nasality_antiformant_boost_for_nasal_consonants_targets",
        }
        self.passthrough_phoneme_parameter_names = {
            "vowel_formants_importance": "vowel_importance_targets",
            "aspiration_importance": "aspiration_importance_targets",
            "constriction_importance": "constriction_importance_targets",
            "nasality": "nasality_targets"
        }

        self.extra_parameter_names = [
            "vowel_formant_freqs_targets", "oral_closure_targets", "stop_amp_targets"
        ]  # this is just here to have a list of all internal parameter names at any given time, if I concatenate this with all above .values()
        self.all_internal_names = (list(self.extra_parameter_names) +
                                   list(self.coarticulated_constriction_parameter_names.values()) +
                                   list(self.non_coarticulated_constriction_parameter_names.values()) +
                                   list(self.nasalization_parameter_names.values()) +
                                   list(self.passthrough_phoneme_parameter_names.values()))
        # TODO: Potentially implement aspiration coarticulation coloring?

        self.simulate()

    def simulate(self):
        targets = {}
        for internal_name in self.all_internal_names:
            targets[internal_name + "_ts"] = list()
            targets[internal_name + "_vs"] = list()

        for phoneme_i, phoneme in enumerate(self.in_.phonemes):
            prev_phoneme_d = self.phoneme_d[self.in_.phonemes[phoneme_i - 1].ID] if phoneme_i - 1 >= 0 else None
            prev_articulation_d = self.articulation_d[prev_phoneme_d["phoneme"]] if prev_phoneme_d else None
            curr_phoneme_d = self.phoneme_d[phoneme.ID]
            curr_articulation_d = self.articulation_d[curr_phoneme_d["phoneme"]]
            next_phoneme_d = self.phoneme_d[self.in_.phonemes[phoneme_i + 1].ID] if phoneme_i + 1 < len(self.in_.phonemes) else None
            next_articulation_d = self.articulation_d[next_phoneme_d["phoneme"]] if next_phoneme_d else None

            # if some neighboring phonemes are missing, then they will be substituted in the calculation like so:
            # if one of them is missing, the neighbor that exists will function as both neighbors.
            # if both neighbors are missing, then the curr one will function as all 3, effectively cancelling coarticulation (with a bunch of extra steps)
            # this can be optimized later.
            if prev_phoneme_d and not next_phoneme_d:
                next_phoneme_d = prev_phoneme_d
                next_articulation_d = prev_articulation_d
            elif not prev_phoneme_d and next_phoneme_d:
                prev_phoneme_d = next_phoneme_d
                prev_articulation_d = next_articulation_d
            elif not prev_phoneme_d and not next_phoneme_d:
                prev_phoneme_d = next_phoneme_d = curr_phoneme_d
                prev_articulation_d = next_articulation_d = curr_articulation_d

            match curr_phoneme_d["manner"]:
                case "flow":
                    target_dicts = self._manner__flow(phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d, curr_phoneme_d)
                case "nasal":
                    target_dicts = self._manner__nasal(phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d, curr_phoneme_d)
                case "silence":
                    target_dicts = self._manner__silence(phoneme, prev_articulation_d, next_articulation_d, prev_phoneme_d, next_phoneme_d)
                case "stop":
                    target_dicts = self._manner__stop(phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d, curr_phoneme_d)


            for target_dict in target_dicts:
                for internal_name in self.all_internal_names:
                    targets[internal_name + "_ts"].append(target_dict[internal_name + "_t"])
                    targets[internal_name + "_vs"].append(target_dict[internal_name + "_v"])


        ### OUTPUTS
        self.vowel_formant_freqs_targets = FormantTargets(targets["vowel_formant_freqs_targets_ts"], targets["vowel_formant_freqs_targets_vs"])
        self.constriction_HP_freq_targets = Targets(targets["constriction_HP_freq_targets_ts"], targets["constriction_HP_freq_targets_vs"])
        self.constriction_peak_freq_targets = Targets(targets["constriction_peak_freq_targets_ts"], targets["constriction_peak_freq_targets_vs"])
        self.constriction_peak_bandwidth_targets = Targets(targets["constriction_peak_bandwidth_targets_ts"], targets["constriction_peak_bandwidth_targets_vs"])
        self.constriction_peak_boost_targets = Targets(targets["constriction_peak_boost_targets_ts"], targets["constriction_peak_boost_targets_vs"])
        self.constriction_peak_overtone_importance_targets = Targets(targets["constriction_peak_overtone_importance_targets_ts"], targets["constriction_peak_overtone_importance_targets_vs"])
        self.constriction_LP_freq_targets = Targets(targets["constriction_LP_freq_targets_ts"], targets["constriction_LP_freq_targets_vs"])
        self.vowel_importance_targets = Targets(targets["vowel_importance_targets_ts"], targets["vowel_importance_targets_vs"])
        self.aspiration_importance_targets = Targets(targets["aspiration_importance_targets_ts"], targets["aspiration_importance_targets_vs"])
        self.constriction_importance_targets = Targets(targets["constriction_importance_targets_ts"], targets["constriction_importance_targets_vs"])
        self.nasality_targets = Targets(targets["nasality_targets_ts"], targets["nasality_targets_vs"])
        self.oral_closure_targets = Targets(targets["oral_closure_targets_ts"], targets["oral_closure_targets_vs"])
        self.stop_amp_targets = Targets(targets["stop_amp_targets_ts"], targets["stop_amp_targets_vs"])
        self.nasality_antiformant_freq_for_nasal_consonants_targets = Targets(targets["nasality_antiformant_freq_for_nasal_consonants_targets_ts"], targets["nasality_antiformant_freq_for_nasal_consonants_targets_vs"])
        self.nasality_antiformant_bandwidth_for_nasal_consonants_targets = Targets(targets["nasality_antiformant_bandwidth_for_nasal_consonants_targets_ts"], targets["nasality_antiformant_bandwidth_for_nasal_consonants_targets_vs"])
        self.nasality_antiformant_boost_for_nasal_consonants_targets = Targets(targets["nasality_antiformant_boost_for_nasal_consonants_targets_ts"], targets["nasality_antiformant_boost_for_nasal_consonants_targets_vs"])


    def _simple_vowel_formant_freqs_targets_coarticulator(
            self, phoneme: this_layer_types.TimedPhoneme,
            prev_articulation_d, curr_articulation_d, next_articulation_d,
            curr_phoneme_d) -> tuple[float, list]:
        """
        Code excerpt for DRY.
        SPECIFICALLY coarticulates the vowel_formant_freqs, because they use FormantTargets.
        Outputs one FormantTarget (this is not a real data structure, just the name of a column of data in FormantTargets.)
        :param phoneme: The "phoneme" variable of the loop with phoneme_i and phoneme. The current TimedPhoneme.
        :param prev_articulation_d:
        :param curr_articulation_d:
        :param next_articulation_d:
        :param curr_phoneme_d:
        :return: Returns the NEW ITEMS OF vowel_formant_freqs_targets_ts, and vowel_formant_freqs_targets_vs that should be APPENDED TO A LIST OF THEM.
        """
        ### region vowel formants
        prev_vowel_formants = prev_articulation_d["vowel_formants"]
        curr_vowel_formants = curr_articulation_d["vowel_formants"]
        next_vowel_formants = next_articulation_d["vowel_formants"]
        coloring = curr_phoneme_d["vowel_coarticulation_coloring"]

        coarticulated_vowel_formants = []

        for formant_i in range(len(curr_vowel_formants)):  # we only need to coarticulate as much as the current vowel supports
            if formant_i < len(prev_vowel_formants) and formant_i < len(next_vowel_formants):
                # both-neighbor coarticulation
                coarticulated_vowel_formants.append(
                    ((coloring / 2) * prev_vowel_formants[formant_i]) +
                    ((1 - coloring) * curr_vowel_formants[formant_i]) +
                    ((coloring / 2) * next_vowel_formants[formant_i])
                )
            elif formant_i < len(prev_vowel_formants) and formant_i >= len(next_vowel_formants):
                # previous neighbor exists (prev taken twice)
                coarticulated_vowel_formants.append(
                    ((coloring / 2) * prev_vowel_formants[formant_i]) +
                    ((1 - coloring) * curr_vowel_formants[formant_i]) +
                    ((coloring / 2) * prev_vowel_formants[formant_i])
                )
            elif formant_i >= len(prev_vowel_formants) and formant_i < len(next_vowel_formants):
                # next neighbor exists (next taken twice)
                coarticulated_vowel_formants.append(
                    ((coloring / 2) * next_vowel_formants[formant_i]) +
                    ((1 - coloring) * curr_vowel_formants[formant_i]) +
                    ((coloring / 2) * next_vowel_formants[formant_i])
                )
            else:
                # no coarticulation
                coarticulated_vowel_formants.append(
                    curr_vowel_formants[formant_i]
                )

        """vowel_formant_freqs_targets_ts.append(phoneme.start)
        vowel_formant_freqs_targets_vs.append(coarticulated_vowel_formants)"""
        return phoneme.start, coarticulated_vowel_formants
        # endregion

    def _simple_target_coarticulator(
            self, phoneme: this_layer_types.TimedPhoneme,
            prev_datapoint, curr_datapoint, next_datapoint,
            coloring) -> tuple[float, float]:
        """
        Coarticulates everything that should have Targets as output.
        Outputs exactly one target (for use in a Targets class).
        :param phoneme: The current TImedPhoneme.
        :param prev_datapoint: Similar to its use in _simple_vowel_formant_freqs_targets_coarticulator, but it has to be given by the outside function, because this is a general function.
        :param curr_datapoint: same
        :param next_datapoint: same
        :param coloring: same
        :return: A t and a v.
        """
        coarticulated_datapoints = (
            ((coloring / 2) * prev_datapoint) +
            ((1 - coloring) * curr_datapoint) +
            ((coloring / 2) * next_datapoint)
        )
        return phoneme.start, coarticulated_datapoints

    def _passthrough_non_coarticulated_constriction_parameters(
            self, phoneme: this_layer_types.TimedPhoneme, curr_articulation_d) -> dict:
        """
        Calculates all the t and v of all NON-COARTICULATED CONSTRICTION parameters.
        The list of these parameters, along with the mapping to internal names, is found in __init__() under self.non_coarticulated_constriction_parameter_names.
        :param phoneme: The current TimedPhoneme.
        :param curr_articulation_d:
        :return: All the passthrough values with correct internal naming in a dict.
        """
        target_passthroughs = dict()
        for json_parameter_name, internal_parameter_name in self.non_coarticulated_constriction_parameter_names.items():
            t = phoneme.start
            v = curr_articulation_d["constriction"][json_parameter_name]
            target_passthroughs[internal_parameter_name + "_t"] = t
            target_passthroughs[internal_parameter_name + "_v"] = v
        return target_passthroughs

    def _passthrough_nasalization_parameters(  # THIS FUNC IS ALMOST THE SAME AS THE ABOVE ONE, SHOULD I DRY IT?
            self, phoneme: this_layer_types.TimedPhoneme, curr_articulation_d) -> dict:
        """
        Calculates all the t and v of all NON-COARTICULATED CONSTRICTION parameters.
        The list of these parameters, along with the mapping to internal names, is found in __init__() under self.non_coarticulated_constriction_parameter_names.
        :param phoneme: The current TimedPhoneme.
        :param curr_articulation_d:
        :return: All the passthrough values with correct internal naming in a dict.
        """
        target_passthroughs = dict()
        for json_parameter_name, internal_parameter_name in self.nasalization_parameter_names.items():
            t = phoneme.start
            v = curr_articulation_d["nasalization"][json_parameter_name]
            target_passthroughs[internal_parameter_name + "_t"] = t
            target_passthroughs[internal_parameter_name + "_v"] = v
        return target_passthroughs

    def _passthrough_phoneme_parameters(
            self, phoneme: this_layer_types.TimedPhoneme, curr_phoneme_d) -> dict:
        """
        Calculates all the t and v of all PHONEME (so phoneme_data.json) parameters that don't have any coarticulation, like
        vowel_formants_importance, constriction_importance etc.
        The list of these parameters, along with the mapping to internal names, is found in __init__() under self.passthrough_phoneme_parameter_names.
        :param phoneme: The current TimedPhoneme.
        :param curr_phoneme_d:
        :return: All the passthrough values with correct internal naming in a dict.
        """
        target_passthroughs = dict()
        for json_parameter_name, internal_parameter_name in self.passthrough_phoneme_parameter_names.items():
            t = phoneme.start
            v = curr_phoneme_d[json_parameter_name]
            target_passthroughs[internal_parameter_name + "_t"] = t
            target_passthroughs[internal_parameter_name + "_v"] = v
        return target_passthroughs

    def _manner__flow(
            self, phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d,
            curr_phoneme_d):
        target = dict()

        # vowel formants
        t, v = self._simple_vowel_formant_freqs_targets_coarticulator(phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d, curr_phoneme_d)
        target["vowel_formant_freqs_targets_t"] = t
        target["vowel_formant_freqs_targets_v"] = v
        # constriction parameters (generalized)
        for json_parameter_name, internal_parameter_name in self.coarticulated_constriction_parameter_names.items():
            t, v = self._simple_target_coarticulator(
                phoneme,
                prev_articulation_d["constriction"][json_parameter_name],
                curr_articulation_d["constriction"][json_parameter_name],
                next_articulation_d["constriction"][json_parameter_name],
                curr_phoneme_d["constriction_coarticulation_coloring"]
            )
            target[internal_parameter_name + "_t"] = t
            target[internal_parameter_name + "_v"] = v
        # passthrough non-coarticulated constriciton parameters
        target.update(
            self._passthrough_non_coarticulated_constriction_parameters(phoneme, curr_articulation_d)
        )
        # passthrough nasalization parameters (non-coarticulated)
        target.update(
            self._passthrough_nasalization_parameters(phoneme, curr_articulation_d)
        )
        # phoneme_data.json parameters (removed for DRY-ness)
        target.update(
            self._passthrough_phoneme_parameters(phoneme, curr_phoneme_d)
        )

        # HANDLE MANNER-SPECIFIC ORAL_CLOSURE
        # There is no one here though, because flow is for vowels, fricatives, liquids etc.
        target["oral_closure_targets_t"] = phoneme.start
        target["oral_closure_targets_v"] = 0
        target["stop_amp_targets_t"] = phoneme.start
        target["stop_amp_targets_v"] = 1

        # DICTIONARIFY OUTPUTS TO PASS THEM CLEANLY
        return (target,)

    def _manner__nasal(
            self, phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d,
            curr_phoneme_d):
        target = dict()
        """NOTE, THIS IS BASICALLY THE SAME AS _manner__flow, JUST WITH ORAL_CLOSURE = 1."""

        # vowel formants
        t, v = self._simple_vowel_formant_freqs_targets_coarticulator(phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d, curr_phoneme_d)
        target["vowel_formant_freqs_targets_t"] = t
        target["vowel_formant_freqs_targets_v"] = v
        # constriction parameters (generalized)
        for json_parameter_name, internal_parameter_name in self.coarticulated_constriction_parameter_names.items():
            t, v = self._simple_target_coarticulator(
                phoneme,
                prev_articulation_d["constriction"][json_parameter_name],
                curr_articulation_d["constriction"][json_parameter_name],
                next_articulation_d["constriction"][json_parameter_name],
                curr_phoneme_d["constriction_coarticulation_coloring"]
            )
            target[internal_parameter_name + "_t"] = t
            target[internal_parameter_name + "_v"] = v
        # passthrough non-coarticulated constriciton parameters
        target.update(
            self._passthrough_non_coarticulated_constriction_parameters(phoneme, curr_articulation_d)
        )
        # passthrough nasalization parameters (non-coarticulated)
        target.update(
            self._passthrough_nasalization_parameters(phoneme, curr_articulation_d)
        )
        # phoneme_data.json parameters (removed for DRY-ness)
        target.update(
            self._passthrough_phoneme_parameters(phoneme, curr_phoneme_d)
        )

        # HANDLE MANNER-SPECIFIC ORAL_CLOSURE
        # Nasals have oral closure *and* nasality (normally)
        target["oral_closure_targets_t"] = phoneme.start
        target["oral_closure_targets_v"] = 1
        target["stop_amp_targets_t"] = phoneme.start
        target["stop_amp_targets_v"] = 1

        # DICTIONARIFY OUTPUTS TO PASS THEM CLEANLY
        return (target,)

    def _manner__silence(
            self, phoneme, prev_articulation_d, next_articulation_d, prev_phoneme_d, next_phoneme_d):
        target1 = dict()
        target1_to_2 = dict()
        """This one is silent. It completely adapts itself to the previous and next phoneme, so much so that no change can be heard.
        Target1: This one mutes the current phoneme without changing frequencies and other parameters, only importances. (Specifically, the vowel_form_imp, asp_imp and constr_imp.)
        Target1_to_2: Right in the middle between 1 and 2 on the targeting timeline, we move the mouth from the current position to the next as anticipatory articulation (because we will be starting a new word or sentence.)
        There is no Target2, because that's the actual next phoneme we start with."""

        # TODO: DRY this code?
        # vowel formants
        t1 = phoneme.start
        t1_to_2 = (phoneme.end - phoneme.start) / 2
        v1 = prev_articulation_d["vowel_formants"]
        v1_to_2 = next_articulation_d["vowel_formants"]
        target1["vowel_formant_freqs_targets_t"] = t1
        target1["vowel_formant_freqs_targets_v"] = v1
        target1_to_2["vowel_formant_freqs_targets_t"] = t1_to_2
        target1_to_2["vowel_formant_freqs_targets_v"] = v1_to_2
        # constriction parameters (generalized)
        for json_parameter_name, internal_parameter_name in self.coarticulated_constriction_parameter_names.items():
            v1 = prev_articulation_d["constriction"][json_parameter_name]
            v1_to_2 = next_articulation_d["constriction"][json_parameter_name]
            target1[internal_parameter_name + "_t"] = t1
            target1[internal_parameter_name + "_v"] = v1
            target1_to_2[internal_parameter_name + "_t"] = t1_to_2
            target1_to_2[internal_parameter_name + "_v"] = v1_to_2
        # passthrough non-coarticulated constriciton parameters
        target1.update(
            self._passthrough_non_coarticulated_constriction_parameters(phoneme, prev_articulation_d)
        )
        target1_to_2.update(
            self._passthrough_non_coarticulated_constriction_parameters(phoneme, next_articulation_d)
        )
        # passthrough nasalization parameters (non-coarticulated)
        target1.update(
            self._passthrough_nasalization_parameters(phoneme, prev_articulation_d)
        )
        target1_to_2.update(
            self._passthrough_nasalization_parameters(phoneme, next_articulation_d)
        )
        # phoneme_data.json parameters (removed for DRY-ness)
        # CANNOT PASSTHROUGH ALL: MUST MUTE IMPORTANCES
        target1.update(
            self._passthrough_phoneme_parameters(phoneme, prev_phoneme_d)
        )
        target1_to_2.update(
            self._passthrough_phoneme_parameters(phoneme, next_phoneme_d)
        )
        target1["vowel_importance_targets_t"] = t1
        target1["vowel_importance_targets_v"] = 0
        target1["aspiration_importance_targets_t"] = t1
        target1["aspiration_importance_targets_v"] = 0
        target1["constriction_importance_targets_t"] = t1
        target1["constriction_importance_targets_v"] = 0
        target1_to_2["vowel_importance_targets_t"] = t1_to_2
        target1_to_2["vowel_importance_targets_v"] = 0
        target1_to_2["aspiration_importance_targets_t"] = t1_to_2
        target1_to_2["aspiration_importance_targets_v"] = 0
        target1_to_2["constriction_importance_targets_t"] = t1_to_2
        target1_to_2["constriction_importance_targets_v"] = 0

        # HANDLE MANNER-SPECIFIC ORAL_CLOSURE
        # Silence is passthrough
        match prev_phoneme_d["manner"]:
            case "flow":
                v1 = 0
            case "nasal":
                v1 = 1
            case "silence":
                v1 = 0
            case "stop":
                v1 = 0
        target1["oral_closure_targets_t"] = t1
        target1["oral_closure_targets_v"] = v1
        target1["stop_amp_targets_t"] = t1
        target1["stop_amp_targets_v"] = 1

        match next_phoneme_d["manner"]:
            case "flow":
                v1_to_2 = 0
            case "nasal":
                v1_to_2 = 1
            case "silence":
                v1_to_2 = 0
            case "stop":
                v1_to_2 = 1  # Only stops are special enough to have a difference at start and end (at start, they are orally closed, at end, they are not).
        target1_to_2["oral_closure_targets_t"] = t1_to_2
        target1_to_2["oral_closure_targets_v"] = v1_to_2
        target1_to_2["stop_amp_targets_t"] = t1_to_2
        target1_to_2["stop_amp_targets_v"] = 1

        # DICTIONARIFY OUTPUTS TO PASS THEM CLEANLY
        return (target1, target1_to_2)

    def _manner__stop(
            self, phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d,
            curr_phoneme_d):
        target = dict()

        # vowel formants
        t, v = self._simple_vowel_formant_freqs_targets_coarticulator(phoneme, prev_articulation_d, curr_articulation_d, next_articulation_d, curr_phoneme_d)
        target["vowel_formant_freqs_targets_t"] = t
        target["vowel_formant_freqs_targets_v"] = v
        # constriction parameters (generalized)
        for json_parameter_name, internal_parameter_name in self.coarticulated_constriction_parameter_names.items():
            t, v = self._simple_target_coarticulator(
                phoneme,
                prev_articulation_d["constriction"][json_parameter_name],
                curr_articulation_d["constriction"][json_parameter_name],
                next_articulation_d["constriction"][json_parameter_name],
                curr_phoneme_d["constriction_coarticulation_coloring"]
            )
            target[internal_parameter_name + "_t"] = t
            target[internal_parameter_name + "_v"] = v
        # passthrough non-coarticulated constriciton parameters
        target.update(
            self._passthrough_non_coarticulated_constriction_parameters(phoneme, curr_articulation_d)
        )
        # passthrough nasalization parameters (non-coarticulated)
        target.update(
            self._passthrough_nasalization_parameters(phoneme, curr_articulation_d)
        )
        # phoneme_data.json parameters (removed for DRY-ness)
        target.update(
            self._passthrough_phoneme_parameters(phoneme, curr_phoneme_d)
        )

        # HANDLE MANNER-SPECIFIC ORAL_CLOSURE
        # There is no one here though, because flow is for vowels, fricatives, liquids etc.
        target["oral_closure_targets_t"] = phoneme.start
        target["oral_closure_targets_v"] = 0
        target["stop_amp_targets_t"] = phoneme.start
        target["stop_amp_targets_v"] = 1

        # DICTIONARIFY OUTPUTS TO PASS THEM CLEANLY
        return (target,)



def transform(input_: this_layer_types.Input) -> next_layer_types.Input:
    """
    Entry point, transform function for the TARGETING layer.
    :param input: layer input specified in the layer's types.
    :return: next layer input.
    """

    targets = Targeter(input_)
    output = next_layer_types.Input(
        character_dir_path=input_.character_dir_path,
        output_filepath=input_.output_filepath,
        duration=input_.duration,
        # Phoneme targets
        vowel_formant_freqs_targets=targets.vowel_formant_freqs_targets,
        constriction_HP_freq_targets=targets.constriction_HP_freq_targets,
        constriction_peak_freq_targets=targets.constriction_peak_freq_targets,
        constriction_peak_bandwidth_targets=targets.constriction_peak_bandwidth_targets,
        constriction_peak_boost_targets=targets.constriction_peak_boost_targets,
        constriction_peak_overtone_importance_targets=targets.constriction_peak_overtone_importance_targets,
        constriction_LP_freq_targets=targets.constriction_LP_freq_targets,
        vowel_importance_targets=targets.vowel_importance_targets,
        aspiration_importance_targets=targets.aspiration_importance_targets,
        constriction_importance_targets=targets.constriction_importance_targets,
        nasality_targets=targets.nasality_targets,
        oral_closure_targets=targets.oral_closure_targets,
        stop_amp_targets=targets.stop_amp_targets,
        nasality_antiformant_freq_for_nasal_consonants_targets=targets.nasality_antiformant_freq_for_nasal_consonants_targets,
        nasality_antiformant_bandwidth_for_nasal_consonants_targets=targets.nasality_antiformant_bandwidth_for_nasal_consonants_targets,
        nasality_antiformant_boost_for_nasal_consonants_targets=targets.nasality_antiformant_boost_for_nasal_consonants_targets,
        # Global envelopes
        Volume=input_.envelope_targets.Volume,
        F0=input_.envelope_targets.F0,
        NasalityDelta=input_.envelope_targets.NasalityDelta,
        BreathinessDelta=input_.envelope_targets.BreathinessDelta,
        Tension=input_.envelope_targets.Tension,
        MachineGrowl=input_.envelope_targets.MachineGrowl,
        LipRoundingDelta=input_.envelope_targets.LipRoundingDelta,
        VocalGenderDelta=input_.envelope_targets.VocalGenderDelta,
        # Throat jitter
        ThroatJitter=input_.envelope_targets.ThroatJitter
    )
    return output





if __name__ == "__main__":
    from simple_speech_synthesizer.base.types import Envelope, Point, Segment
    i = this_layer_types.Input(
        character_dir_path=r"../characters/Greensparrow",
        output_filepath=r"../testaudio.wav",
        duration=3,
        phonemes=(
            this_layer_types.TimedPhoneme("hun_s", 0, 1),
            this_layer_types.TimedPhoneme("hun_a", 1, 2),
            this_layer_types.TimedPhoneme("hun_s", 2, 3),
        ),
        envelope_targets=this_layer_types.EnvelopeTargets(
            Volume=Envelope((Point(0, -6), Point(3, -6)), (Segment("linear"),)),
            F0=Envelope((Point(0, 120), Point(3, 120)), (Segment("linear"),)),
            NasalityDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            BreathinessDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            Tension=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            MachineGrowl=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            LipRoundingDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            VocalGenderDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            ThroatJitter=Envelope((Point(0, 1), Point(3, 1)), (Segment("linear"),))
        )
    )
    o = transform(i)
    pprint(o)