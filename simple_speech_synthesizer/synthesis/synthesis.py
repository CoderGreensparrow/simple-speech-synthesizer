import pyo
from simple_speech_synthesizer.realization.realization import SynthStates

class Generators:
    def __init__(self):
        pass

    def vocal_source(self, fundamental_frequency, amplitude):
        pass

class Synthesis:
    def __init__(self, pyo_server_kwargs: dict = None):
        pyo_server_kwargs = {
            "sr": 48000,
            "nchnls": 2,
            "buffersize": 256,
            "duplex": 0,
            "audio": "portaudio"
        }
        if pyo_server_kwargs is not None:
            for key, val in pyo_server_kwargs.items():
                pyo_server_kwargs[key] = val
        self.s = pyo.Server(**pyo_server_kwargs)
        self.s.deactivateMidi()
        self.s.boot()
        self.s.start()

    def synthesize(self, synth_frames: SynthStates, deltaTime):
        """
        MAIN LAYER ENTRY FUNCTION
        :param synth_frames: The SynthFrames to synthesize
        :param deltaTime: The equal time spacing between each frame, effectively the resolution of how many times the synthesis can change.
        :return:
        """


if __name__ == "__main__":
    synthesis = Synthesis()