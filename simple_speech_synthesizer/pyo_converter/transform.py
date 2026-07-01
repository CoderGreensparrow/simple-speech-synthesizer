"""
LAYER 3: adapter layer between the rest of the model and the pyo synthesizer.

This layer:
1. Initializes the pyo server
2. Converts the target points to a step function as a control signal for the acoustic state
3. Converts the Envelopes to pyo envelopes for further work.
"""

import pyo

import dataclasses

from simple_speech_synthesizer.pyo_converter import middle_level_types_USE_LATER as this_layer_types
from simple_speech_synthesizer.synthesis import synthesis_types as next_layer_types

from simple_speech_synthesizer.base.types import Envelope

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

def staircase_targets(input: this_layer_types.Input):
    """
    Generate a pyo staircase waveformed control signal from the targets.
    :return:
    """
    input.Vowel_formant


def transform(input: this_layer_types.Input) -> next_layer_types.Input:
    s = start_pyo()

    """This was old code that converted low-level parameters to pyo objects."""
    '''input_all_attrs = {f.name: getattr(input, f.name) for f in dataclasses.fields(input)}
    # The above code performs a manual shallow copy of a dataclass.
    # It may also be used with @dataclass(frozen=True, slots=True). That slots argument would break vars().
    attr_overrides = {}

    for key, val in input_all_attrs.items():
        if (isinstance(val, tuple) or isinstance(val, list)) and isinstance(val[0], Envelope):  # Vowel_formant_freqs exception
            attr_overrides[key] = []
            for single_envelope in val:
                attr_overrides[key].append([(point.t, point.v) for point in single_envelope.points])
        elif isinstance(val, Envelope):
            attr_overrides[key] = [(point.t, point.v) for point in val.points]

    input_all_attrs.update(attr_overrides)
    return next_layer_types.Input(**input_all_attrs)'''