"""
Simplified synthesis pipeline, from the smallest component to the largest:

INPUTS (text, inflection, etc. anything the user desires, like SynthV or UTAU)
-> LAYER 0: language_processing (NLP layer, may be very simplistic at first, producing monotone voices, but because it's modular, it should be possible to upgrade it later)
TODO: prosody is not properly defined here. SOLUTION: don't care about prosody, prosody controls are all manually open, like UTAU or Vocaloid. Specific control parameters could be programmatically generated later too. IMPORTANT: create a good prosody input parameter system.
-> LAYER 1: timing (decides the literal length of individual phonemes/phones, based on the NLP info, and controlles the targeting system)
-> LAYER 2: targeting (decides what the next articulatory target is for the lover subsystems)
-> LAYER 3: acoustic_state (an ever evolving acoustic simulation of the mouth that is controlled by the current state target given by the targeting layer, so essentially it contains and progresses the current state of the nonexistent/acoustic-only mouth)
-> LAYER 4: realization (also called "acoustic_to_synthesis_adaptor", converts complex acoustic synthesis data with "Breathiness", "Vocal tilt" and "Lip Rounding", as well as "Consonant voiced component formant corrections" information to dead-simple parameters for the synthesizer.)
    Outputs: SynthStates
-> LAYER 5: synthesis (voiced source + formant parameters, voiceless source + formant parameters, MAYBE EVEN breathiness voiceless source + formant parameters, SUMMED UP, it's a very dumb layer)
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

IMPLEMENTATION DETAILS:

- there are no separate language-specific pronunciations of phonemes, each phoneme is attached to a language.
    So there is an English /ε/, a Japanese /ε/, and they have separate phoneme IDs (e.g. one uses ARPABET with prefix "En" and one uses XSAMPA with "Jp")
- the entire project is based around the idea of a vocal synthesizer, so each little parameter and inflection can be edited.
    This means that the default "speech" and "singing" inflections/auto-parametrizers are just defaults applied to the parameters, which can be edited later.
    This means that the user could select a part of the snythsis (e.g. some notes), hit an "apply speech inflection" or "apply singing inflection" button,
    and the corresponding systems would overwrite all or part of the tuning present in that part to make it sound like singing or speech.
"""
