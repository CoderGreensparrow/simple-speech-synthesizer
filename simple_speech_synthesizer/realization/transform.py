"""
LAYER 4: realization
Evaluates higher-level acoustic parameters into the lower-level ones.
So Nasality, Breathiness etc. gets all encoded in F0, F1, F2, noise_amp, voiced_amp etc.
It makes the higher-level data synthesizer-friendly.

The actual conversion from custom types (Envelope) to pyo's types happens in the layer below.
"""

from simple_speech_synthesizer.realization import types as this_layer_types
from simple_speech_synthesizer.pyo_adapter import types as next_layer_types
from simple_speech_synthesizer.base.load_low_level_character import load_low_level_character


def transform(input: this_layer_types.Input) -> next_layer_types.Input:
    """
    This layer applies the middle-level parameters to the low-level ones.
    :param input:
    :return:
    """