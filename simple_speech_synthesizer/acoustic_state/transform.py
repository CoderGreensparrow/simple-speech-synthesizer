"""
SYNTHESIS LAYER 4: Simulates the nonexistent mouth (acoustic parameter simulation only).
It knows nothing about phonemes, only acousto-linguistic parameters of the mouth, and targets to reach with the parameters that have mass to them.
The heart of the coarticulation engine.
"""

from simple_speech_synthesizer.acoustic_state import types as this_layer_types
from simple_speech_synthesizer.realization import types as next_layer_types

from simple_speech_synthesizer.acoustic_state.simulate import simulate_acoustic_state

def transform(input: this_layer_types.Input) -> next_layer_types.Input:
    high_level_envelopes = simulate_acoustic_state(input)
    output = next_layer_types.Input(
        character_dir_path=input.character_dir_path,
        high_level_envelopes=high_level_envelopes,
        duration=input.duration
    )
    return output