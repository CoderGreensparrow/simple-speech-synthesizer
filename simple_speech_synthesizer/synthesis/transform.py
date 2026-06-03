import pyo
from simple_speech_synthesizer.realization.transform import SynthStates

class Generator:
    def __init__(self, F0, amp = 1.0,
                 F0_sway_amp = 3, vocal_jitter_amp = 0.15,
                 vocal_amp_jitter_amp = 0.03,
                 blit_harmonics = 80,
                 delta_vocal_tilt = 0.0):
        """
        Instantiates vocal and noise generators.
        :param F0: The starting fundamental frequency
        :param amp: The amplitude of the generator. Leave at default.
        :param F0_sway_amp: The amplitude of the slow instability of F0 in Hz. Default 3.
        :param vocal_jitter_amp: The amplitude of the vocal jitter in Hz. Default 0.15.
        :param vocal_amp_jitter_amp: How much the amplitude of the vocal jitters. Ratio difference. default 0.03.
        :param blit_harmonics: How many harmonics the base tone has, essentially how dense the basic vocal is.
        :param delta_vocal_tilt: The amount in Hz to adjust the "vocal tilt effect" by (how muddy or how bright the original signal is). Too high values cause sawtooth-like engine noise.
        """
        fundamental_sway = pyo.ButLP(pyo.BrownNoise(), freq=3, mul=F0_sway_amp)
        FM_jitter = pyo.ButLP(pyo.BrownNoise(), freq=15, mul=vocal_jitter_amp)
        vocal_amp_sway = pyo.ButLP(pyo.BrownNoise(), freq=25, mul=vocal_amp_jitter_amp)
        vocal_raw = pyo.Blit(freq=F0 + fundamental_sway + FM_jitter, harms=blit_harmonics, mul=amp + vocal_amp_sway)
        body = pyo.ButLP(vocal_raw, 400 + delta_vocal_tilt, mul=1)  # spectral "tilt" (spectral shaping of Blit)
        body_high = pyo.ButHP(vocal_raw, 3000 + delta_vocal_tilt, mul=0.01)
        self.vocal = body + body_high

        self.noise = pyo.Noise()


    def instantiate_vocal_source(self, F0, amp):
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

    def synthesize_grain(self):
        pass

    def synthesize(self, synth_frames: SynthStates, deltaTime):
        """
        MAIN LAYER ENTRY FUNCTION
        :param synth_frames: The SynthFrames to synthesize
        :param deltaTime: The equal time spacing between each frame, effectively the resolution of how many times the synthesis can change.
        :return:
        """
        pass


if __name__ == "__main__":
    synthesis = Synthesis()