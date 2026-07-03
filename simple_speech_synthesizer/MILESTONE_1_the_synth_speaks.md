# Summary of the project up until this point

Phew this was a lot to work on...

BASIC PIPELINE:
- targeting layer
  - *TARGET*: Because real mouths don't just teleport from one phoneme to another, the system implement rudimentary coarticulation.
    This happens at a low level (glides between different mouth states, or rather acoustic states),
    and at a higher level, which is really what "coarticulation" means in linguistic terms, where certain phonemes give each other's timbre coloration.
    To implement such a system effectively, the system needs TARGETS. These are the states which the system has to reach at any given point in time.
    As the current target changes, the system will try to reach that new desired state.
    (Btw, "the system" means the parametric formant synthesizer hidden at the bottom of the pipeline, essentially it means the machine mouth.)
    The targets can either be tied to specific points in time (like phoneme switches), and can change over time (like volume, the pitch of the voice, aspiration levels etc.)
  - This layer takes in TimedPhonemes, which function as the higher-level targets that need to be converted, along with certain EnvelopeTargets (targets which are defined by envelopes)
  - After it has done processing, it outputs lower-level *targets* which are used for the semi-physical simulation of the mouth (like the vowel formants) in the next two layers.
- pyo_converter layer
  - This layer takes in the targets and converts them to pyo friendly pyo.Linseg objects (control signal functions which consist of points connected by lines).
  - This layer is also responsible for handling something deeper:
    - In the system, every phoneme has a variable number of formants. But the synthesizer cannot handle a variable number of control signals.
    - This is solved by introducing an amplitude multiplier/factor (called internally *importance*) to every formant synthesized. When it is 0, the formant is muted.
    - Because we need to already create the amount of formants we will have at maximum right at the point we transition to using pyo.Linsegs,
      we have to calculate these amplitude multipliers (*importances*) now.
    - So this layer also handles appearing and disappearing formants (aka. formants which are defined in one phoneme but not defined in another).
- acoustic_state layer (better called acoustic *simulation*)
  - This is responsible for the low-level coarticulation, the gliding between different target states.
  - This is done with simple pyo.Port objects (exponential portamento).
  - Now it's important to make a distinction between the different types of parameters used:
    - *HIGH-LEVEL PARAMETERS*: These parameters of the synthesized voice have semantic meaning, and may require multiple separate parts of
      the low level synthesizer to be correctly synthesized.
    - *LOW-LEVEL PARAMETERS*: These can directly drive the low-level (or "dumb", doesn't know why the parameters the way they are) synthesizer.
    - At this layer, the two coexist.
- realization layer
  - But these parameters will all be collapsed into *LOW-LEVEL PARAMETERS* in this layer.
  - So this layer's job is to apply the changes of the *HIGH-LEVEL PARAMETERS* to the *LOW-LEVEL* ones.
    This leaves behind *only the parameters that can directly drive the synthesizer.*
- synthesis layer
  - You may ask: Why did I not have the high-level parameters drive the synth too? The synth could have the logic to do so.
    Answer: **I wanted to keep the synthesizer layer as simple and dumb as possible. Which means it shouldn't be aware of why it does what it does.
    It should just blindly accept any parameter input it receives and act it out.**
  - Therefore, it ONLY ACCEPTS *LOW-LEVEL PARAMETERS*.
  - It then synthesizes the actual voice and BAM we have an audio file.

I brushed over a lot of details here. But that's the gist of it.

To summarize:
This is a bodged together implementation of a parametric formant synthesizer where the parameters are all semantically meaningful and the parameter space of the synthesizer is as simple as possible.

Of course, the actual implementation is kind of far from this description. **But it talks! And that's what matters to me right now.**

PLAN TO ADD:
- stops and affricates
- trills and taps
- vibrato and squillo
- silence marker (there should be a 'sil' phoneme like in a certain commercial vocal synth), and maybe also breathing