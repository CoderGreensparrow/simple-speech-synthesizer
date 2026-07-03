from pyo import PyoObject, Server
from typing import Any
from simple_speech_synthesizer.global_debug_vars import _PRINT_ACTIVATE_LAYER_INPUTS

# Gemini code that I've looked through and it should be fine
def activate_layer_inputs(input_dataclass: Any) -> None:
    """
    Shallow-scans the attributes of a layer's input dataclass.
    Calls .play() on any direct PyoObjects or PyoObjects stored in flat lists/tuples.
    """
    if not hasattr(input_dataclass, "__dict__"):
        return

    for attr_name, value in vars(input_dataclass).items():
        # Case 1: The attribute itself is a pyo signal/object
        if isinstance(value, PyoObject):
            if _PRINT_ACTIVATE_LAYER_INPUTS: print(attr_name, value)
            value.play()

        # Case 2: The attribute is a list/tuple of pyo signals (like formant frequencies)
        elif isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, PyoObject):
                    if _PRINT_ACTIVATE_LAYER_INPUTS: print(attr_name, type(value), item)
                    item.play()
