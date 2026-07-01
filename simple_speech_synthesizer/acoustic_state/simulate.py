from simple_speech_synthesizer.acoustic_state import types as this_layer_types
from simple_speech_synthesizer.realization import types as next_layer_types

from simple_speech_synthesizer.acoustic_state.load_low_level_character import load_low_level_character

from simple_speech_synthesizer.base.types import NdimensionalParameterSpace, NdimensionalParameterSpaceTarget, NdimensionalParameterSpaceSimulator

from simple_speech_synthesizer.base.types import Envelope, Point, Segment

from simple_speech_synthesizer.acoustic_state.count_formants import max_num_of_formants_in_targets

import numpy as np


def simulate_acoustic_state(input: this_layer_types.Input) -> next_layer_types.HighLevelEnvelopes:
    """
    NOTE: This is one Big Bad Function. It's very WET.
    Simulates low-level coarticulation by creating envelopes from acoustic target states.
    The simulation is done through a simplified PD controller, as of 2026. 06. 19.
    :param acoustic_targets: The acoustic_targets argument of this layer's Input class.
    :return: SimulatedEnvelopes.
    """

    synthesis_parameters = load_low_level_character(input.character_dir_path).synthesis_parameters

    ####### SIMULATION DESCRIPTION
    # Certain features will be grouped together in simulation spaces, like vowel_formant_frequencies (all tongue),
    # Tension and VocalTilt and F0 (all throat) etc.
    #### EDGE CASES FOR FORMANT TARGETS
    # Since the number of formants can change per phoneme, I have to handle blending between sometimes existing, sometimes non-existent formants
    # Let's say that F6 exists for some target, but the next target has no F6.
    # In this case, I'll set the target of the non-existent F6 formant to 0, and search for the next F6 formant in the targets later.
    # I'll target the frequency and bandwidth of that later F6 formant right now.
    # Once I get to that later F6 formant, I'll also set the importance to the right level, which will gently fade that formant into existence.
    ## IF there is no F6 formant later, I'll just permanently leave the importance at 0, effectively cancelling the F6 formant.

    # This method requires knowing the maximum amount of formants beforehand,
    # which means I'll have to compute count them. This is done with count_formants.py/max_num_of_formants_in_targets().

    """
    NOTE:
    ==========================
    The main problem with this whole thing is my data structures...
    This layer takes in SimplifiedFormants, which store their data as (freq, bandwidth, importance) blocks.
    But it uses the data in (F1, F2, F3) (Band1, Band2, Band3) (Imp1, Imp2, Imp3) format (data conversion #1)
    And it has to return it in FormantEnvelope arrays [(F_Env(freq_Env, band_Env, imp_Env)), ...] (data conversion #2)
    And everything has its own name...
    
    The resulting code is very convoluted and very not DRY.
    But I'll maybe fix it later (probably not, if I'm being honest. Maybe this whole project will warrant a rewrite anyway.)
    """

    max_vowel_formants, max_constriction_formants = max_num_of_formants_in_targets(input.acoustic_targets)

    vowel_formant_coarticulation_max_acc = synthesis_parameters["vowel_formant_coarticulation_max_acc"]
    vowel_formant_coarticulation_kp = synthesis_parameters["vowel_formant_coarticulation_kp"]
    vowel_formant_coarticulation_kd = synthesis_parameters["vowel_formant_coarticulation_kd"]
    constriction_formant_coarticulation_max_acc = synthesis_parameters["constriction_formant_coarticulation_max_acc"]
    constriction_formant_coarticulation_kp = synthesis_parameters["constriction_formant_coarticulation_kp"]
    constriction_formant_coarticulation_kd = synthesis_parameters["constriction_formant_coarticulation_kd"]
    percentage_type_parameter_coarticulation_max_acc = synthesis_parameters["percentage_type_parameter_coarticulation_max_acc"]
    percentage_type_parameter_coarticulation_kp = synthesis_parameters["percentage_type_parameter_coarticulation_kp"]
    percentage_type_parameter_coarticulation_kd = synthesis_parameters["percentage_type_parameter_coarticulation_kd"]
    dt = synthesis_parameters["dt"]

    # data conversion #1

    ### region VOWEL FORMANTS
    initial_pos = []
    for i in range(max_vowel_formants):
        if i < len(input.acoustic_targets[0].vowel_formants):
            initial_pos.append(input.acoustic_targets[0].vowel_formants[i].freq)
        else:
            for j in range(1, len(input.acoustic_targets)):
                ### Search for next available F6, F7 etc. formant that doesn't exist in the beginning
                ## We will find at least one of these formants somewhere, because max_vowel_formants guarantees it.
                if len(input.acoustic_targets[j].vowel_formants) > i:
                    initial_pos.append(input.acoustic_targets[j].vowel_formants[i].freq)
                    break
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(initial_pos) != max_vowel_formants:
        raise RuntimeError("SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 59 (freq)")
    ####### END OF FAILSAFE
    Vowel_formants_freq_space = NdimensionalParameterSpace(
        param_names=tuple([f"F{i}_freq" for i in range(1, max_vowel_formants + 1)]),
        param_pos=np.array(initial_pos),
        param_vel=np.zeros(max_vowel_formants),
        max_acc=vowel_formant_coarticulation_max_acc,
        current_t=0
    )

    # The same thing for bandwidth as formants
    initial_pos = []
    for i in range(max_vowel_formants):
        if i < len(input.acoustic_targets[0].vowel_formants):
            initial_pos.append(input.acoustic_targets[0].vowel_formants[i].bandwidth)
        else:
            for j in range(1, len(input.acoustic_targets)):
                if len(input.acoustic_targets[j].vowel_formants) > i:
                    initial_pos.append(input.acoustic_targets[j].vowel_formants[i].bandwidth)
                    break
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(initial_pos) != max_vowel_formants:
        raise RuntimeError("SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 81 (bandwidth)")
    ####### END OF FAILSAFE
    Vowel_formants_bandwidth_space = NdimensionalParameterSpace(
        param_names=tuple([f"F{i}_bandwidth" for i in range(1, max_vowel_formants + 1)]),
        param_pos=np.array(initial_pos),
        param_vel=np.zeros(max_vowel_formants),
        max_acc=vowel_formant_coarticulation_max_acc,
        current_t=0
    )

    # Something different for importance
    # As described above, if the specific i. formant doesn't exist for initial position,
    # it's importance is just... 0
    initial_pos = []
    for i in range(max_vowel_formants):
        if i < len(input.acoustic_targets[0].vowel_formants):
            initial_pos.append(input.acoustic_targets[0].vowel_formants[i].importance)
        else:
            initial_pos.append(0)
    Vowel_formants_importance_space = NdimensionalParameterSpace(
        param_names=tuple([f"F{i}_importance" for i in range(1, max_vowel_formants + 1)]),
        param_pos=np.array(initial_pos),
        param_vel=np.zeros(max_vowel_formants),
        max_acc=vowel_formant_coarticulation_max_acc,
        current_t=0
    )
    # endregion

    ### region CONSTRICTION FORMANTS (copy of above code essentially)
    initial_pos = []
    for i in range(max_constriction_formants):
        if i < len(input.acoustic_targets[0].constriction_formants):
            initial_pos.append(input.acoustic_targets[0].constriction_formants[i].freq)
        else:
            for j in range(1, len(input.acoustic_targets)):
                ### Search for next available F6, F7 etc. formant that doesn't exist in the beginning
                ## We will find at least one of these formants somewhere, because max_constriction_formants guarantees it.
                if len(input.acoustic_targets[j].constriction_formants) > i:
                    initial_pos.append(input.acoustic_targets[j].constriction_formants[i].freq)
                    break
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(initial_pos) != max_constriction_formants:
        raise RuntimeError("SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 123 (freq, constriction)")
    ####### END OF FAILSAFE
    Constriction_formants_freq_space = NdimensionalParameterSpace(
        param_names=tuple([f"F{i}_freq" for i in range(1, max_constriction_formants + 1)]),
        param_pos=np.array(initial_pos),
        param_vel=np.zeros(max_constriction_formants),
        max_acc=constriction_formant_coarticulation_max_acc,
        current_t=0
    )

    # The same thing for bandwidth as formants
    initial_pos = []
    for i in range(max_constriction_formants):
        if i < len(input.acoustic_targets[0].constriction_formants):
            initial_pos.append(input.acoustic_targets[0].constriction_formants[i].bandwidth)
        else:
            for j in range(1, len(input.acoustic_targets)):
                if len(input.acoustic_targets[j].constriction_formants) > i:
                    initial_pos.append(input.acoustic_targets[j].constriction_formants[i].bandwidth)
                    break
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(initial_pos) != max_constriction_formants:
        raise RuntimeError("SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 145 (bandwidth, constriction)")
    ####### END OF FAILSAFE
    Constriction_formants_bandwidth_space = NdimensionalParameterSpace(
        param_names=tuple([f"F{i}_bandwidth" for i in range(1, max_constriction_formants + 1)]),
        param_pos=np.array(initial_pos),
        param_vel=np.zeros(max_constriction_formants),
        max_acc=constriction_formant_coarticulation_max_acc,
        current_t=0
    )

    # Something different for importance
    # As described above, if the specific i. formant doesn't exist for initial position,
    # it's importance is just... 0
    initial_pos = []
    for i in range(max_constriction_formants):
        if i < len(input.acoustic_targets[0].constriction_formants):
            initial_pos.append(input.acoustic_targets[0].constriction_formants[i].importance)
        else:
            initial_pos.append(0)
    Constriction_formants_importance_space = NdimensionalParameterSpace(
        param_names=tuple([f"F{i}_importance" for i in range(1, max_constriction_formants + 1)]),
        param_pos=np.array(initial_pos),
        param_vel=np.zeros(max_constriction_formants),
        max_acc=constriction_formant_coarticulation_max_acc,
        current_t=0
    )
    # endregion

    # region one-dimensional spaces
    Voice_to_noise_ratio_space = NdimensionalParameterSpace(
        param_names=tuple(["Voice_to_noise_ratio"]),
        param_pos=np.array([input.acoustic_targets[0].voice_to_noise_ratio]),
        param_vel=np.zeros(1),
        max_acc=percentage_type_parameter_coarticulation_max_acc,
        current_t=0
    )
    Constriction_space = NdimensionalParameterSpace(
        param_names=tuple(["Constriction"]),
        param_pos=np.array([input.acoustic_targets[0].constriction]),
        param_vel=np.zeros(1),
        max_acc=percentage_type_parameter_coarticulation_max_acc,
        current_t=0
    )
    Nasality_space = NdimensionalParameterSpace(
        param_names=tuple(["Nasality"]),
        param_pos=np.array([input.acoustic_targets[0].nasality]),
        param_vel=np.zeros(1),
        max_acc=percentage_type_parameter_coarticulation_max_acc,
        current_t=0
    )
    # endregion

    # region The low-level coarticulation of global envelope targets (TODO)
    ##### TODO right now all global envelope targets are just treated as the finalized, low-level coarticulated global envelopes
    # endregion

    ### SIMULATION ###
    # MAIN POINT: Create Envelopes from the simulation
    #### TARGET CREATION IS DYNAMIC, BASED ON THE current_t

    # region 1. Creating simulations using abbreviations
    vf_freq_sim = NdimensionalParameterSpaceSimulator(Vowel_formants_freq_space)
    vf_band_sim = NdimensionalParameterSpaceSimulator(Vowel_formants_bandwidth_space)
    vf_impo_sim = NdimensionalParameterSpaceSimulator(Vowel_formants_importance_space)
    cf_freq_sim = NdimensionalParameterSpaceSimulator(Constriction_formants_freq_space)
    cf_band_sim = NdimensionalParameterSpaceSimulator(Constriction_formants_bandwidth_space)
    cf_impo_sim = NdimensionalParameterSpaceSimulator(Constriction_formants_importance_space)
    v_t_n_ratio_sim = NdimensionalParameterSpaceSimulator(Voice_to_noise_ratio_space)
    constriction_sim = NdimensionalParameterSpaceSimulator(Constriction_space)
    nasality_sim = NdimensionalParameterSpaceSimulator(Nasality_space)
    # endregion

    # region 2. Initializing Envelope point containers
    Vowel_formants_frequency_points = [[] for _ in range(max_vowel_formants)]  # 2d array
    Vowel_formants_bandwidth_points = [[] for _ in range(max_vowel_formants)]
    Vowel_formants_importance_points = [[] for _ in range(max_vowel_formants)]
    Constriction_formants_frequency_points = [[] for _ in range(max_constriction_formants)]
    Constriction_formants_bandwidth_points = [[] for _ in range(max_constriction_formants)]
    Constriction_formants_importance_points = [[] for _ in range(max_constriction_formants)]
    Voice_to_noise_ratio_points = []
    Constriction_points = []
    Nasality_points = []
    # endregion

    # 3. SIMULATING
    t = vf_freq_sim.parameter_space.current_t  # one of the many sims is used to keep track of the time
    last_target_i = None
    while vf_freq_sim.parameter_space.current_t < input.duration:
        # I) The current target is the last target available
        curr_target = None
        curr_target_i = None
        for i in range(len(input.acoustic_targets)):
            if input.acoustic_targets[i].t > t:
                curr_target = input.acoustic_targets[i - 1]
                curr_target_i = i - 1
                break
        if curr_target is None:  # FAILSAFE
            curr_target = input.acoustic_targets[-1]

        # II) Make the AcousticTarget into a ParameterSpaceTarget, but only if there is a new target to transform
        if last_target_i is None or last_target_i != curr_target_i:
            vf_freq_target, vf_bandwidth_target, vf_importance_target, cf_freq_target, cf_bandwidth_target, cf_importance_target, v_t_n_ratio_target, constriction_target, nasality_target = _II_calculate_NdimensionalTargets_from_acoustic_targets(curr_target, curr_target_i, max_vowel_formants,
                                                                    max_constriction_formants, input)

        # III) SIMULATE
        vf_freq_sim.simulate(vf_freq_target, dt, vowel_formant_coarticulation_kp, vowel_formant_coarticulation_kd)
        vf_band_sim.simulate(vf_bandwidth_target, dt, vowel_formant_coarticulation_kp, vowel_formant_coarticulation_kd)
        vf_impo_sim.simulate(vf_importance_target, dt, vowel_formant_coarticulation_kp, vowel_formant_coarticulation_kd)
        cf_freq_sim.simulate(cf_freq_target, dt, constriction_formant_coarticulation_kp, constriction_formant_coarticulation_kd)
        cf_band_sim.simulate(cf_bandwidth_target, dt, constriction_formant_coarticulation_kp, constriction_formant_coarticulation_kd)
        cf_impo_sim.simulate(cf_importance_target, dt, constriction_formant_coarticulation_kp, constriction_formant_coarticulation_kd)
        v_t_n_ratio_sim.simulate(v_t_n_ratio_target, dt, percentage_type_parameter_coarticulation_kp, percentage_type_parameter_coarticulation_kd)
        constriction_sim.simulate(constriction_target, dt, percentage_type_parameter_coarticulation_kp, percentage_type_parameter_coarticulation_kd)
        nasality_sim.simulate(nasality_target, dt, percentage_type_parameter_coarticulation_kp, percentage_type_parameter_coarticulation_kd)

        # IV) record simulation output to point lists (data conversion #2/a)
        for i, vf_freq_sim_pos in enumerate(vf_freq_sim.get_current_parameter_space().param_pos):
            Vowel_formants_frequency_points[i].append(Point(t, vf_freq_sim_pos))
        for i, vf_band_sim_pos in enumerate(vf_band_sim.get_current_parameter_space().param_pos):
            Vowel_formants_bandwidth_points[i].append(Point(t, vf_band_sim_pos))
        for i, vf_impo_sim_pos in enumerate(vf_impo_sim.get_current_parameter_space().param_pos):
            Vowel_formants_importance_points[i].append(Point(t, vf_impo_sim_pos))
        for i, cf_freq_sim_pos in enumerate(cf_freq_sim.get_current_parameter_space().param_pos):
            Constriction_formants_frequency_points[i].append(Point(t, cf_freq_sim_pos))
        for i, cf_band_sim_pos in enumerate(cf_band_sim.get_current_parameter_space().param_pos):
            Constriction_formants_bandwidth_points[i].append(Point(t, cf_band_sim_pos))
        for i, cf_impo_sim_pos in enumerate(cf_impo_sim.get_current_parameter_space().param_pos):
            Constriction_formants_importance_points[i].append(Point(t, cf_impo_sim_pos))
        Voice_to_noise_ratio_points.append(Point(t, v_t_n_ratio_sim.get_current_parameter_space().param_pos[0]))
        Constriction_points.append(Point(t, constriction_sim.get_current_parameter_space().param_pos[0]))
        Nasality_points.append(Point(t, nasality_sim.get_current_parameter_space().param_pos[0]))

        t = vf_freq_sim.parameter_space.current_t
        last_target_i = curr_target_i

    # region 4. Converting lists of Points to Envelopes and generating Segments (data conversion #2/b)
    connector_segments = tuple([Segment("linear")] * (len(Vowel_formants_frequency_points[0]) - 1))
    Vowel_formants = tuple([
        FormantEnvelope(Envelope(Vowel_formants_frequency_points[i], connector_segments),
                        Envelope(Vowel_formants_bandwidth_points[i], connector_segments),
                        Envelope(Vowel_formants_importance_points[i], connector_segments))
        for i in range(len(Vowel_formants_frequency_points))
    ])
    connector_segments = tuple([Segment("linear")] * (len(Constriction_formants_frequency_points[0]) - 1))
    Constriction_formants = tuple([
        FormantEnvelope(Envelope(Constriction_formants_frequency_points[i], connector_segments),
                        Envelope(Constriction_formants_bandwidth_points[i], connector_segments),
                        Envelope(Constriction_formants_importance_points[i], connector_segments))
        for i in range(len(Constriction_formants_frequency_points))
    ])
    connector_segments = tuple([Segment("linear")] * (len(Voice_to_noise_ratio_points) - 1))
    Voice_to_noise_ratio = Envelope(Voice_to_noise_ratio_points, connector_segments)
    connector_segments = tuple([Segment("linear")] * (len(Constriction_points) - 1))
    Constriction = Envelope(Constriction_points, connector_segments)
    connector_segments = tuple([Segment("linear")] * (len(Nasality_points) - 1))
    Nasality = Envelope(Nasality_points, connector_segments)
    # endregion

    output = next_layer_types.HighLevelEnvelopes(
            # SIMULATED
            Vowel_formants=Vowel_formants,
            Constriction_formants=Constriction_formants,
            Voice_to_noise_ratio=Voice_to_noise_ratio,
            Constriction=Constriction,
            Nasality=Nasality,
            ### TODO implement low-level coarticulation on global envelope targets (rn they are just treated as the finalized global envelopes)
            Volume=input.global_envelope_targets.Volume,
            F0=input.global_envelope_targets.F0,
            NasalityDelta=input.global_envelope_targets.NasalityDelta,
            BreathinessDelta=input.global_envelope_targets.BreathinessDelta,
            Tension=input.global_envelope_targets.Tension,
            VocalTilt=input.global_envelope_targets.VocalTilt,
            LipRoundingDelta=input.global_envelope_targets.LipRoundingDelta,
            GenderDelta=input.global_envelope_targets.GenderDelta
        )
    return output


def _II_calculate_NdimensionalTargets_from_acoustic_targets(curr_target, curr_target_i, max_vowel_formants, max_constriction_formants, input):
    """
    INTERNAL FUNCTION, part of the non-dry code is here.
    CACHED FUNCTION FOR CURR_TARGET_I. (If function output was computed once for curr_target_i, that is returned.)
    """
    # II) Make the AcousticTarget into a ParameterSpaceTarget
    # region a) targets of vowel_formants
    # THE CODE IS PRETTY MUCH A COPY OF THE LOGIC AT INITIAL_POS...
    pos = [curr_target.vowel_formants[i].freq for i in range(len(curr_target.vowel_formants))]
    if len(pos) < max_vowel_formants:
        for i in range(len(pos), max_vowel_formants):
            found_formant = False
            for j in range(curr_target_i + 1, len(input.acoustic_targets)):
                if len(input.acoustic_targets[j].vowel_formants) >= i + 1:
                    found_formant = True
                    pos.append(input.acoustic_targets[j].vowel_formants[i].freq)
                    break
                    # TODO I hope I'm not off by one above
            if not found_formant:
                pos.append(20000)  # random high placeholder since there are no more such formants
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(pos) != max_vowel_formants:
        raise RuntimeError("SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 257 (SIMULATION, vowel, freq)")
    ####### END OF FAILSAFE
    vf_freq_target = NdimensionalParameterSpaceTarget(np.array(pos))

    pos = [curr_target.vowel_formants[i].bandwidth for i in range(len(curr_target.vowel_formants))]
    if len(pos) < max_vowel_formants:
        for i in range(len(pos), max_vowel_formants):
            found_formant = False
            for j in range(curr_target_i + 1, len(input.acoustic_targets)):
                if len(input.acoustic_targets[j].vowel_formants) >= i + 1:
                    found_formant = True
                    pos.append(input.acoustic_targets[j].vowel_formants[i].bandwidth)
                    break
                    # TODO I hope I'm not off by one above
            if not found_formant:
                pos.append(100)  # random default placeholder since there are no more such formants
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(pos) != max_vowel_formants:
        raise RuntimeError(
            "SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 276 (SIMULATION, vowel, bandwidth)")
    ####### END OF FAILSAFE
    vf_bandwidth_target = NdimensionalParameterSpaceTarget(np.array(pos))

    pos = [curr_target.vowel_formants[i].importance for i in range(len(curr_target.vowel_formants))]
    if len(pos) < max_vowel_formants:
        for i in range(len(pos), max_vowel_formants):
            pos.append(0)  # if no formant exists, it should be silent
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(pos) != max_vowel_formants:
        raise RuntimeError(
            "SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 287 (SIMULATION, vowel, importance)")
    ####### END OF FAILSAFE
    vf_importance_target = NdimensionalParameterSpaceTarget(np.array(pos))
    # endregion

    # region b) targets of constriction_formants (SAME CODE AS ABOVE, IF ERRORS ARE THERE, THEY ARE HERE TOO)
    pos = [curr_target.constriction_formants[i].freq for i in range(len(curr_target.constriction_formants))]
    if len(pos) < max_constriction_formants:
        for i in range(len(pos), max_constriction_formants):
            found_formant = False
            for j in range(curr_target_i + 1, len(input.acoustic_targets)):
                if len(input.acoustic_targets[j].constriction_formants) >= i + 1:
                    found_formant = True
                    pos.append(input.acoustic_targets[j].constriction_formants[i].freq)
                    break
                    # TODO I hope I'm not off by one above
            if not found_formant:
                pos.append(20000)  # random high placeholder since there are no more such formants
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(pos) != max_constriction_formants:
        raise RuntimeError(
            "SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 309 (SIMULATION, constriction, freq)")
    ####### END OF FAILSAFE
    cf_freq_target = NdimensionalParameterSpaceTarget(np.array(pos))

    pos = [curr_target.constriction_formants[i].bandwidth for i in
           range(len(curr_target.constriction_formants))]
    if len(pos) < max_constriction_formants:
        for i in range(len(pos), max_constriction_formants):
            found_formant = False
            for j in range(curr_target_i + 1, len(input.acoustic_targets)):
                if len(input.acoustic_targets[j].constriction_formants) >= i + 1:
                    found_formant = True
                    pos.append(input.acoustic_targets[j].constriction_formants[i].bandwidth)
                    break
                    # TODO I hope I'm not off by one above
            if not found_formant:
                pos.append(100)  # random default placeholder since there are no more such formants
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(pos) != max_constriction_formants:
        raise RuntimeError(
            "SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 327 (SIMULATION, constriction, bandwidth)")
    ####### END OF FAILSAFE
    cf_bandwidth_target = NdimensionalParameterSpaceTarget(np.array(pos))

    pos = [curr_target.constriction_formants[i].importance for i in
           range(len(curr_target.constriction_formants))]
    if len(pos) < max_constriction_formants:
        for i in range(len(pos), max_constriction_formants):
            pos.append(0)  # if no formant exists, it should be silent
    ####### FAILSAFE (aka. if not every formant was found that something IS BAD...)
    if len(pos) != max_constriction_formants:
        raise RuntimeError(
            "SOMETHING GONE WRONG WITH FINDING FORMANTS AT LINE 337 (SIMULATION, constriction, importance)")
    ####### END OF FAILSAFE
    cf_importance_target = NdimensionalParameterSpaceTarget(np.array(pos))
    # endregion

    # region c) targets of one-dimensional spaces
    v_t_n_ratio_target = NdimensionalParameterSpaceTarget(np.array([curr_target.voice_to_noise_ratio]))
    constriction_target = NdimensionalParameterSpaceTarget(np.array([curr_target.constriction]))
    nasality_target = NdimensionalParameterSpaceTarget(np.array([curr_target.nasality]))
    # endregion

    return vf_freq_target, vf_bandwidth_target, vf_importance_target, cf_freq_target, cf_bandwidth_target, cf_importance_target, v_t_n_ratio_target, constriction_target, nasality_target