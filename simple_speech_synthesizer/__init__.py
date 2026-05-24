"""
Simplified synthesis pipeline, from the smallest component to the largest:

INPUTS (text, inflection, etc. anything the user desires, like SynthV or UTAU)
-> language_processing (NLP layer, may be very simplistic at first, producing monotone voices, but because it's modular, it should be possible to upgrade it later)
-> timing (decides the literal length of individual phonemes/phones, based on the NLP info, and controlles the targeting system)
-> targeting (decides what the next articulatory target is for the lover subsystems)
-> acoustic_state (an ever evolving acoustic simulation of the mouth that is controlled by the current state target given by the targeting layer, so essentially it contains and progresses the current state of the nonexistent/acoustic-only mouth)
-> realization (also called "acoustic_to_synthesis_adaptor", converts complex acoustic synthesis data with "Breathiness", "Vocal tilt" and "Lip Rounding", as well as "Consonant voiced component formant corrections" information to dead-simple parameters for the synthesizer.)
    Outputs: SynthStates
-> synthesis (voiced source + formant parameters, voiceless source + formant parameters, MAYBE EVEN breathiness voiceless source + formant parameters, SUMMED UP, it's a very dumb layer)
OUT: audio

IMPORTANT NOTE: formant deltas, formant delta coarticulation with percentage changing as transition between CV and VC happens

ChatGPT summary:
INPUTS
(text, phonemes, pitch, expression, timing hints)
↓
language_processing
Converts text/input into linguistic structure:
phonemes, syllables, stress, intonation, etc.
↓
timing
Assigns durations and timing to phonemes/events.
Produces a fully timed phoneme sequence.
↓
targeting
Expands phonemes into time-based acoustic targets.
Example: /t/ → closure → burst → aspiration.
Outputs timed AcousticStateTargets.
↓
acoustic_state
Continuously evolves the current acoustic state toward targets.
This is where coarticulation emerges naturally through inertia/smoothing.
No phoneme knowledge exists here anymore.
↓
realization
Converts high-level acoustic descriptors into concrete DSP parameters.
Combines:
- vowel-space formants
- consonant formant deltas
- nasality deltas
- lip-rounding deltas
- etc.
Outputs fully resolved synthesis parameters.
↓
synthesis
Dumb DSP renderer.
Generates audio using:
- voiced source
- noise source
- filters
- gains
- EQ
No linguistic or phonetic knowledge exists here.
↓
AUDIO

The pipeline's main and subcomponents are modular.

Additional components:

video_visualization (synthesizing pipeline state visualization rendering with matplotlib)
"""