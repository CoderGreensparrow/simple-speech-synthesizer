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
from simple_speech_synthesizer.acoustic_state import types as next_layer_types

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
        if i == 0:
            stepped_targets.append((point[0], point[1]))
        elif i == len(targets.ts) - 1:
            stepped_targets.append((input_duration, point[1]))  # pull the signal out till the end
        else:
            stepped_targets.append((point[0], point[1]))
            stepped_targets.append((targets.ts[i + 1][0], targets.vs[i + 1][1]))
    return pyo.Linseg(tuple(stepped_targets))

def _formant_targets_to_steps(formant_targets: FormantTargets, input_duration: float) -> tuple[tuple[pyo.Linseg, ...], tuple[pyo.Linseg, ...]]:
    """
    Converts the FormantTargets to step function control signal lists.
    Specifically, 2 control signal lists: a formant_freq list and a formant_importance_list.
    :param formant_targets: A FormantTargets object, where the number of formants per target CAN BE VARIABLE.
    :param input_duration: this_layer_types.Input.duration
    :return: The 2 control signal lists.
    """
    # PYTHONIC WORK METHOD
    # It will dynamically add more pyo.Linseg data to the finalized Linseg data
    # Each of the lists within stepped_formant_* will be converted to pyo.Linsegs.
    stepped_formant_targets = []
    stepped_formant_importances = []
    for i, points in enumerate(zip(formant_targets.ts, formant_targets.vs)):
        if i == 0:  # adding first control points (to all separate formant Linsegs)
            for point in points:
                stepped_formant_targets.append([(point[0], point[1])])
                stepped_formant_importances.append([(point[0], 1)])  # full power for all formants at first
        elif i == len(formant_targets.ts) - 1:  # adding last control points (max out duration)
            for j, point in enumerate(points):
                stepped_formant_targets[-1].append((input_duration, point[1]))
                stepped_formant_importances[-1].append((input_duration, stepped_formant_importances[-1][j][1]))  # same control points for importance as the 1 to last
        else:  # the actual interesting part
            stepped_targets.append((point[0], point[1]))
            stepped_targets.append((targets.ts[i + 1][0], targets.vs[i + 1][1]))

            # 1. Add in current points at new values (compared to the previous cycle)
            for point in points:
                stepped_formant_targets.append([(point[0], point[1])])

            # 2. Add in next points at the same values as the current ones


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
