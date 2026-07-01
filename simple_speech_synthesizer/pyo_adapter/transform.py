"""
LAYER 5: adapter layer between the rest of the model and the pyo synthesizer.
It essentially converts all the Envelope objects (custom type) to pyo's types of envelopes.
"""

import dataclasses

from simple_speech_synthesizer.pyo_adapter import types as this_layer_types
from simple_speech_synthesizer.synthesis import synthesis_types as next_layer_types

from simple_speech_synthesizer.base.types import Envelope

def transform(input: this_layer_types.Input) -> next_layer_types.Input:
    input_all_attrs = {f.name: getattr(input, f.name) for f in dataclasses.fields(input)}
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
    return next_layer_types.Input(**input_all_attrs)