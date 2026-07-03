from pprint import pprint

from simple_speech_synthesizer.garbage_collection_prevention import GLOBAL_AUDIO_FORTRESS, SEND_TO_THE_SCOPE
from simple_speech_synthesizer.targeting.types import Input as InputTargeting
from simple_speech_synthesizer.targeting.transform import transform as transform_targeting
from simple_speech_synthesizer.pyo_converter.types import Input as InputPyoConverter
from simple_speech_synthesizer.pyo_converter.transform import transform as transform_pyo_converter
from simple_speech_synthesizer.acoustic_state.types import Input as InputAcousticState
from simple_speech_synthesizer.acoustic_state.transform import transform as transform_acoustic_state
from simple_speech_synthesizer.realization.types import Input as InputRealization
from simple_speech_synthesizer.realization.transform import transform as transform_realization
from simple_speech_synthesizer.synthesis.synthesis_types import Input as InputSynthesis
from simple_speech_synthesizer.synthesis.transform import transform as transform_synthesis

import pyo

import time, math

from simple_speech_synthesizer.global_debug_vars import _DEBUG_SYNTHESIS

#### GLOBAL AUDIO OUTPUTS
global_left_channel = None
global_right_channel = None

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

def process_targeting(input: InputTargeting, full_stack: bool = True):
    """
    Process the TARGETING layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return:
    """
    output = transform_targeting(input)
    pprint(output)
    if full_stack:
        output = run_pyo_converter_fixed(output)
    return output

def process_pyo_converter(orchestrator_server: pyo.Server, input: InputPyoConverter) -> tuple[pyo.PyoObject, pyo.PyoObject]:
    """
    Process the TARGETING layer. ALWAYS runs full stack.
    :param input: Input of the layer with the layer's own Input class.
    :return: Two audio outputs, for the two channels, that have to be .out()ed and saved in orchestrator's global reference.
    """
    output = transform_pyo_converter(orchestrator_server, input)
    output = process_acoustic_state(output)
    return output

def process_acoustic_state(input: InputAcousticState):
    """
    Process the ACOUSTIC STATE (parametric simulation) layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return:
    """
    output = transform_acoustic_state(input)
    output = process_realization(output)
    return output

def process_realization(input: InputRealization):
    """
    Process the REALIZATION (middle-level parameter to synthesizer-level parameter converter) layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return:
    """
    output = transform_realization(input)
    output = process_synthesis(output)
    return output

def process_synthesis(input: InputSynthesis):
    """
    Process the SYNTHESIS (last) layer.
    :param input: Input of the layer with the layer's own Input class.
    :param full_stack: Whether (TRUE case:) to run through the input the full stack of layers, and output TTS audio, or (FALSE case:) to only process this layer.
    :return: The filepath of the outputted audio file
    """
    output = transform_synthesis(input)
    return output

def run_pyo_converter_fixed(input_: InputPyoConverter):
    global global_left_channel, global_right_channel

    print("[ORCHESTRATOR] Booting pyo server...")
    s = start_pyo()

    print("[ORCHESTRATOR] Starting layer processing pipe...")
    raw_synthesis_output = process_pyo_converter(s, input_)
    print(f"[ORCHESTRATOR] Synthesis layer finished! Output type: {type(raw_synthesis_output)}")
    print(f"[ORCHESTRATOR] Content of output: {raw_synthesis_output}")


    # Hard-stop diagnostic check: Let's see what we actually got back
    # before trying to unpack it into two variables
    print("[ORCHESTRATOR] Attempting to extract audio channels...")
    audio_out = raw_synthesis_output[0]
    audio_out_2 = raw_synthesis_output[1]

    global_left_channel = audio_out
    global_right_channel = audio_out_2

    print("[ORCHESTRATOR] Routing channels to hardware buffers...")
    global_left_channel.out(0)
    global_right_channel.out(1)

    print("[ORCHESTRATOR] Starting pyo master clock...")
    s.start()

    print(len(GLOBAL_AUDIO_FORTRESS))

    _DEBUG_SCOPE_ON = True

    print("=== Vocal engine running successfully... ===")
    if not(_DEBUG_SYNTHESIS and _DEBUG_SCOPE_ON):
        print("=== NaN Tracker Active. Watching the DSP graph... ===")
        start_time = time.time()
        try:
            while True:
                """time.sleep(1)
    
                # 1. Documented Server Checks: Track elapsed runtime via Python
                elapsed = time.time() - start_time
                sr = s.getSamplingRate()
                buf = s.getBufferSize()
    
                print(f"[SERVER STATE] Running for: {elapsed:.2f}s | SR: {sr} Hz | Buffer: {buf} samples")
    
                # 2. Documented Node Inspection: Use .get() to sample the active stream buffer
                if audio_out is not None:
                    try:
                        # .get() returns the first sample of the current audio buffer block as a float
                        current_sample = audio_out.get()
                        print(f"[AUDIO OUT] Live Sample Value: {current_sample}")
    
                        # Optional: Verify the underlying stream structures safely
                        # streams = final_output_node.getBaseObjects()
                        # print(f"[HARDWARE STREAMS] Managed Audio Pipes: {len(streams)}")
    
                    except Exception as node_err:
                        print(f"[NODE CHECK FAILED] Error reading output node: {node_err}")"""
                time.sleep(0.1)  # Sample frequently to catch it early

                """# Inside your while True loop:
                for obj in GLOBAL_AUDIO_FORTRESS:
                    # Replace 'Step' with the actual class name of your step function objects
                    if "Port" in type(obj).__name__ or "Linseg" in type(obj).__name__:
                        print(f"[{type(obj).__name__} Check] Current Value: {obj.get()}")"""

                found_bad_obj = False
                for obj in GLOBAL_AUDIO_FORTRESS:
                    try:
                        # Read the current buffer value of the node
                        val = obj.get()

                        # Check if this specific node has collapsed into NaN or Infinity
                        if math.isnan(val) or math.isinf(val):
                            found_bad_obj = True
                            print(f"\n🚨 MATH EXPLOSION DETECTED! 🚨")
                            print(f"Node Type: {type(obj).__name__}")
                            print(f"Memory Address: {hex(id(obj))}")

                            # If the object has parameters you can read, print them:
                            if hasattr(obj, 'freq'):
                                print(f" -> Current Freq Parameter: {obj.freq}")
                            if hasattr(obj, 'mul'):
                                print(f" -> Current Mul Parameter: {obj.mul}")

                    except Exception:
                        # Some internal structural base objects might not support .get(), skip them safely
                        continue
                if found_bad_obj:
                    print("\nHalting synthesis.")
                    return  # Exit the program immediately

        except KeyboardInterrupt:
            print("\nStopping audio server gracefully...")
            s.stop()
    else:
        to_scope = [audio_out]
        to_scope.extend(SEND_TO_THE_SCOPE)
        scope = pyo.Scope(to_scope, length=0.75)
        analyzer = pyo.Spectrum([audio_out], size=2 ** 14)
        analyzer.setFscaling(True)  # log
        analyzer.setLowFreq(0)
        analyzer.setHighFreq(10000)
        analyzer.setGain(0)
        s.gui(locals())


if __name__ == "__main__":
    from simple_speech_synthesizer.targeting.types import Input, TimedPhoneme, EnvelopeTargets
    from simple_speech_synthesizer.base.types import Envelope, Point, Segment

    from simple_speech_synthesizer.base.types import Envelope, Point, Segment

    i = Input(
        character_dir_path=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\characters\Greensparrow",
        output_filepath=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\testaudio.wav",
        duration=3,
        phonemes=(
            TimedPhoneme("hun_s", 0, 1),
            TimedPhoneme("hun_a", 1, 2),
            TimedPhoneme("hun_s", 2, 3),
        ),
        envelope_targets=EnvelopeTargets(
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
    o = process_targeting(i, full_stack=True)
