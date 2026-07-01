"""
LAYER 3: adapter layer between the rest of the model and the pyo synthesizer.

This layer:
1. Initializes the pyo server
2. Converts the target points to a step function as a control signal for the acoustic state
3. Converts the Envelopes to pyo envelopes for further work.
"""

import pyo

import dataclasses

from simple_speech_synthesizer.pyo_converter import types as this_layer_types
from simple_speech_synthesizer.synthesis import synthesis_types as next_layer_types

from simple_speech_synthesizer.base.types import FormantTargets, Targets, Envelope

from simple_speech_synthesizer.global_debug_vars import _DEBUG_SYNTHESIS


def start_pyo() -> pyo.Server:
    pyo_server_kwargs = {
        "sr": 48000,
        "nchnls": 2,
        "buffersize": 256,
        "duplex": 0,
        "audio": "offline" if not _DEBUG_SYNTHESIS else "portaudio"
    }
    s = pyo.Server(**pyo_server_kwargs)
    s.deactivateMidi()
    s.boot()
    return s

def _targets_to_step(targets: Targets, input_duration: float) -> pyo.Linseg:
    stepped_targets = []
    for i, point in enumerate(zip(targets.ts, targets.vs)):
        if i == 0 and targets.ts[0] > 0:  # if there is no initial data point (at t=0), there will be
            stepped_targets.append((0, point[1]))

        if i < len(targets.ts) - 1:
            stepped_targets.append((point[0], point[1]))
            stepped_targets.append((targets.ts[i+1], point[1]))
        elif i == len(targets.ts) - 1:
            stepped_targets.append((point[0], point[1]))
            stepped_targets.append((input_duration, point[1]))  # pull the signal out till the end
    return pyo.Linseg(tuple(stepped_targets))


def _formant_targets_to_steps(formant_targets: FormantTargets, input_duration: float) -> tuple[list[pyo.Linseg], list[pyo.Linseg]]:
    """
    Converts the FormantTargets to step function control signal lists.
    Specifically, 2 control signal lists: a formant_freq list and a formant_importance_list.
    :param formant_targets: A FormantTargets object, where the number of formants per target CAN BE VARIABLE.
    :param input_duration: this_layer_types.Input.duration
    :return: The 2 control signal lists.
    """
    max_num_formants = max(len(points) for points in formant_targets.vs)

    PLACEHOLDER_FREQ_IF_THERE_IS_NO_DATA = 500

    # Each of the lists within stepped_formant_* will be converted to pyo.Linsegs.
    stepped_formant_targets = [[] for _ in range(max_num_formants)]
    stepped_formant_importances = [[] for _ in range(max_num_formants)]
    for i in range(len(formant_targets.ts)):
        if i == 0:  # 1. if there are no initial data points (at t=0), there will be
            for formant_i in range(max_num_formants):
                current_num_formants = len(formant_targets.vs[0])
                if formant_i < current_num_formants:
                    stepped_formant_targets[formant_i].append((0, formant_targets.vs[0][formant_i]))
                else:
                    stepped_formant_targets[formant_i].append((0, PLACEHOLDER_FREQ_IF_THERE_IS_NO_DATA))  # placeholder freq, will be overridden anyway
                stepped_formant_importances[formant_i].append((0, 0))  # everything is muted if this is the case.

        if i < len(formant_targets.ts) - 1:  # the actual interesting part
            """stepped_targets.append((point[0], point[1]))
            stepped_targets.append((targets.ts[i + 1][0], targets.vs[i + 1][1]))"""

            # 2. Add in current points at new values (compared to the previous cycle)
            #    and check if there are any importances in need of adjusting
            #    which means are there any formants which (dis)appear right now.
            current_num_formants = len(formant_targets.vs[i])
            for formant_i in range(max_num_formants):
                if formant_i < current_num_formants:
                    stepped_formant_targets[formant_i].append((formant_targets.ts[i], formant_targets.vs[i][formant_i]))
                    stepped_formant_targets[formant_i].append((formant_targets.ts[i+1], formant_targets.vs[i][formant_i]))
                    stepped_formant_importances[formant_i].append((formant_targets.ts[i], 1))
                    stepped_formant_importances[formant_i].append((formant_targets.ts[i+1], 1))
                else:
                    if i != 0:  # so if this formant should be PHASED OUT OF EXISTENCE, then it should take on the last known value
                        stepped_formant_targets[formant_i].append((formant_targets.ts[i], stepped_formant_targets[formant_i][-1][1]))
                        stepped_formant_targets[formant_i].append((formant_targets.ts[i+1], stepped_formant_targets[formant_i][-2][1]))
                    else:  # exception: so if the first value for the formant_ith formant is non-existent, there is no frequency to phase out of
                        stepped_formant_targets[formant_i].append((formant_targets.ts[i], PLACEHOLDER_FREQ_IF_THERE_IS_NO_DATA))
                        stepped_formant_targets[formant_i].append((formant_targets.ts[i+1], PLACEHOLDER_FREQ_IF_THERE_IS_NO_DATA))
                    stepped_formant_importances[formant_i].append((formant_targets.ts[i], 0))
                    stepped_formant_importances[formant_i].append((formant_targets.ts[i+1], 0))

                    # 2.5. if there WILL BE NEXT CYCLE this formant PHASED INTO EXISTENCE,
                    #      their frequencies should be updated before they actually reach their fade in.
                    # ALSOALSO, this switch will overwrite whatever i+1 thing was inserted above. So that's popped.
                    if formant_i <= len(formant_targets.vs[i+1]) - 1:
                        avg_t = (formant_targets.ts[i] + formant_targets.ts[i+1]) / 2
                        stepped_formant_targets[formant_i].insert(-1, (avg_t, formant_targets.vs[i+1][formant_i]))
                        stepped_formant_importances[formant_i].insert(-1, (avg_t, 0))
                        stepped_formant_targets[formant_i].pop(-1)
                        stepped_formant_importances[formant_i].pop(-1)
        # 3. Add last control points and pad out till input_duration, that's where the true last control points are
        elif i == len(formant_targets.ts) - 1:
            current_num_formants = len(formant_targets.vs[-1])
            for formant_i in range(max_num_formants):
                # add in final switch and extend it till input_duration
                if formant_i < current_num_formants:
                    stepped_formant_targets[formant_i].append((formant_targets.ts[i], formant_targets.vs[i][formant_i]))
                    stepped_formant_targets[formant_i].append((input_duration, formant_targets.vs[-1][formant_i]))
                    stepped_formant_importances[formant_i].append((formant_targets.ts[i], 1))
                    stepped_formant_importances[formant_i].append((input_duration, 1))
                else:
                    stepped_formant_targets[formant_i].append((formant_targets.ts[i], stepped_formant_targets[formant_i][-1][1]))
                    stepped_formant_targets[formant_i].append((input_duration, stepped_formant_targets[formant_i][-1][1]))
                    stepped_formant_importances[formant_i].append((formant_targets.ts[i], 0))
                    stepped_formant_importances[formant_i].append((input_duration, 0))

    _DEBUG_RETURN = True
    normal_return = ([pyo.Linseg(points) for points in stepped_formant_targets],
            [pyo.Linseg(points) for points in stepped_formant_importances])
    debug_return = (stepped_formant_targets, stepped_formant_importances)
    return normal_return if not _DEBUG_RETURN else debug_return


def targets_to_step_functions(input_: this_layer_types.Input):
    """
    Generate a pyo step function control signal from the targets.
    MultiTargets are also treated correctly, so that extra formant fading in and out of existence is handled here.
    :return:
    """
    input_all_attrs = {f.name: getattr(input_, f.name) for f in dataclasses.fields(input_)}
    # The above code performs a manual shallow copy of a dataclass.
    # It may also be used with @dataclass(frozen=True, slots=True). That slots argument would break vars().
    attr_overrides = {}

    for key, val in input_all_attrs.items():
        if isinstance(val, FormantTargets):
            attr_overrides[key] = []
        elif isinstance(val, Targets):
            attr_overrides[key] = _targets_to_step(val, input_.duration)

    input_all_attrs.update(attr_overrides)
    return next_layer_types.Input(**input_all_attrs)


def transform(input_: this_layer_types.Input) -> next_layer_types.Input:
    s = start_pyo()


    """This was old code that converted low-level parameters to pyo objects."""




if __name__ == "__main__":
    from pprint import pprint
    s = start_pyo()
    in_ = FormantTargets(
        [2],
        [[200, 500, 800]]
    )
    duration = 15
    o = _formant_targets_to_steps(in_, duration)
    pprint(o)