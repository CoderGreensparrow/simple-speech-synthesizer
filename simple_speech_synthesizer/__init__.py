"""
IMPORTANT NOTE !!!!
ALL THE DOCUMENTATION IN THIS PROJECT WAS ESSENTIALLY THE RESULT OF ME BRAINSTORMING AND WRITING DOWN STUFF AS THE PROJECT IDEAS EVEN BECAME REAL IDEAS.
SO BASICALLY, THERE CAN BE MANY DIFFERENCES IN WHAT IS DOCUMENTED ABOUT THE ARCHITECTURE AND WHAT HAPPENS.
TODO: Write a good documentation about the architecture.

NEW LAYERS (2026. 07. 01.)
-> targeting
-> pyo_converter
-> reworked acoustic_state
-> realization
-> synthesis



===============

IMPORTANT UPDATE:
at the TARGETING LEVEL:
The voice source is now split in 2:
- oral tract: modified by constriciton_formants, vowel_formants
- nasal tract: modified by nasal murmur, oral tract's vowel_formants
Wherein the constriction and closure of the oral tract (aka. how much frication there is, or if the oral tract is fully closed)
is controlled by "constriction" (0 to 1).
And the constriction and closure of the nasal tract
is constrolled by "nasality" (0 to 1). But this not only controls that:
NASALITY also constrols stuff in the oral tract, like removing higher-freq vowel_formants, because there's such a real-life effect too.
So NASALITY effects BOTH tracts.

These two generate two different audio streams which are mixed together.

There's now also
2 DIFFERENT LEVELS OF COARTICULATION:
- low level: the one at acoustic_state, that is still the same.
- high level: at the TARGETING level, between phonemes:
    - The different vowel_formants are blended together.
      So the prev_phoneme_vowel_form, current_phoneme_vowel_form_template, next_phoneme_vowel_form are all weighted averaged.
      The weight is a single value: vowel_coarticulation_coloring, which shows the ratio of the weights between surrounding and current vowel_formants.
      (Since there are two surrounding vowel_formants, the weight is divided between them equally.)
      Example: Let's take /ana/. /n/ is not colored that much by surrounding phonemes, because it has to retain it's identity (nasals are fragile).
      So vowel_coarticulation_coloring is ~0.2.
      In this case, the /a/s get a collective weight of 0.2, so each /a/ contributes with a weight of 0.1 to the finalized vowel_formants.
      The /n/'s internal vowel_formant preset/template gets a weight of 0.8.
      So it's 0.1, 0.8, 0.1, which helps the /n/ get some coarticulation from the sorrounding phonemes (whether it's a vowel or a consonant),
      but it also retains it's own identity.
    - The contriction_formants are also blended similarly, but because consonants are complicated,
      the constriction_coarticulation_coloring is always a low value.
    - A value of 0 means no coarticulation between phonemes, and a value of 1 means that those spectral peaks/formants are only determined by the surrounding phonemes.
    - ALSO IMPORTANT: every phoneme has it's vowel_formants (templates) present, and only THOSE are used when calculating
      the actual vowel formants. So it's prev_template, current_template, next_template weighted average

===============

Simplified synthesis pipeline, from the smallest component to the largest:

INPUTS (text, inflection, etc. anything the user desires, like SynthV or UTAU)
-> LAYER 0: language_processing (NLP layer, may be very simplistic at first, producing monotone voices, but because it's modular, it should be possible to upgrade it later)
TODO: prosody is not properly defined here. SOLUTION: don't care about prosody, prosody controls are all manually open, like UTAU or Vocaloid. Specific control parameters could be programmatically generated later too. IMPORTANT: create a good prosody input parameter system.
-> LAYER 1: timing (decides the literal length of individual phonemes/phones, based on the NLP info, and controlles the targeting system)
BASICALLY NOTHING IS IMPLEMENTED ABOVE LAYER 2 AS OF NOW.
-> LAYER 2: targeting (decides what the next articulatory target is for the lover subsystems)
-> LAYER 3: acoustic_state (an ever evolving acoustic simulation of the mouth that is controlled by the current state target given by the targeting layer, so essentially it contains and progresses the current state of the nonexistent/acoustic-only mouth)
-> LAYER 4: realization (also called "acoustic_to_synthesis_adaptor", converts complex acoustic synthesis data with "Breathiness", "Vocal tilt" and "Lip Rounding", as well as "Consonant voiced component formant corrections" information to dead-simple parameters for the synthesizer.)
-> LAYER 5: pyo_adapter: converts my own types (Envelope) to pyo's types (whatever is needed for envelopes in pyo)
-> LAYER 6: synthesis (voiced source + formant parameters, voiceless source + formant parameters, MAYBE EVEN breathiness voiceless source + formant parameters, SUMMED UP, it's a very dumb layer)
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
