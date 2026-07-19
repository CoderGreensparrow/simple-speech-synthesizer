import functools
import gc
import pyo

# Disable automatic garbage collection sweeps globally
gc.disable()

GLOBAL_AUDIO_FORTRESS = []


def anchor_pyo_objects(func):
    """
    Decorator that runs with automatic GC disabled, sweeps the C++ memory registry
    to capture all audio elements, and manually triggers a safe collection cycle.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 1. Ensure automatic GC is off during execution
        gc.disable()

        # 2. Run the layer function normally
        result = func(*args, **kwargs)

        # 3. Sweep for EVERY live pyo object before running any cleanup
        live_nodes = [obj for obj in gc.get_objects() if isinstance(obj, pyo.PyoObjectBase)]

        # 4. Lock them securely in the fortress
        GLOBAL_AUDIO_FORTRESS.extend(live_nodes)

        # 5. NOW perform manual garbage collection to clear actual dead non-pyo debris
        gc.collect()

        # 6. Keep automatic GC disabled for the next layers
        gc.disable()

        return result

    return wrapper