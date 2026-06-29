# simple-speech-synthesizer
A simple speech synthesizer without rigorous internal structure.

Name: PESK (from a typo by one of my friends)
It's an acronym not yet decided... maybe parametrically engineered speech K____

The project description is better in __init__.py.
Everything below is a remnant of the brainstorming.

===

RELATED RESEARCH (without access if access was needed):
- (Basic description of source-filter model: https://cir.nii.ac.jp/crid/1360013168855541376
- (https://journals.sagepub.com/doi/10.1177/002383096000300105 <- would be useful if I had access)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC5132428/ <- how are English vs Japanese /s/ and /ʃ or ç/ are pronounced over time (centroid differences!)
- https://www.researchgate.net/publication/3333705_Noise_source_models_for_fricative_consonants)
- ! Different ways to measure fricatives: https://scholarworks.iu.edu/journals/index.php/iulcwp/article/view/40694

===

IMPORTANT IDEA:
the targeting layer actually splits up consonants like plsives into sub-targets that the AcousticState follows dumbly.
Therefore, plosive envelopes happen at the targeting level, removing the need for phoneme-specific envelopes at the synthesis level.
Example:
timing layer: /t/ from 01:23.03 --> 01:23.54
targeting layer: closure target at this time, next up is release burst target (NOTE: these are just AcousticStates, or MouthStates), next up is a bit of aspiration target, and finally here's the next vowel, now  here's the next etc. etc...
AcousticState: OK, I got a new target, let's start moving there... hey, here's a new one, let's start moving there... hey, here's a new one... ...
Synthesis (filters + generators): Let's read the current AcousticState... OK, so this means I have to put a formant here and here on this sawtooth source etc.

**So there are no "modes", only "targeting profiles" for different types of phones that only the targeting layer knows about.**


SIMPLIFIED REQUIREMENTS:
I'll compress it with a few more ideas that shouldn't make it too-too complex:
Sources: vocal source (F0 sine + F0 sawtooth with RelativeAmplitude, which means the sawtooth's amplitude relative to the sine's amplitude, as a fraction: SawtoothAmplitude/SineAmplitude) and noise source (white noise with Amplitude)
Core system (voiced and voiceless generators, using the vocal and the noise sources accordingly):
1. The vowel space is coarticulated
2. The consonant lookup table is not coarticulated
3. Voiced components are from the vowel space
4. Voiceless components are from a lookup table
5. Nasality, Breathiness, Tension, VocalTilt and LipRounding are separate lazy paramters
Processing blocks (its not a single layer, its spread around, I also took inspiration of KlattGrid's generation pipeline, like where "Aspiration" is seemingly placed, if I understand it's diagram right):
Nasality is applied after the vowel space and consonant lookup table (just "diagrams" for short).
Breathiness is applied before the diagrams, and its a completely separate system, which mixes an /h/ sound into whatever is playing with the desired Amplitude.
Tension sets the sawtooth component's RelativeAmplitude and can also control the noise source's Amplitude, as well as the Amplitude envelopes applied to stops and the like for e.g. a stronger /t/ sound, so its an overarching setting (which may require sub-paramters).
VocalTilt is applied before any diagrams, as a simple EQ line that tips at one end a certain amount depending on setting (can be made more complex).
LipRounding's effect: The vowel space is crafted in a way that **includes lip rounding information by default** (that's what happens in Praat's VowelEditor, from how I hear it). This means that the LipRounding paramter has **no effect on voiced components**, but does on **voiceless components**. But each vowel **also has a LipRounding paramter associated with it**, set in such a way that a consonant next to it has its formants modified just right, like in the case of /ʃi/ and /ʃu/ for /ʃ/. I hope this is a good compromise, but if it is not, I should build it in a way where it is removable. (It should just stop affecting stuff.) (The other option is to remve the rounding information form the vowel space, and add it in through the LipRounding paramter, thereby introducing coarticulated lip rounding to vowel-consonant clusters fully.) LipRounding is applied as deltaFormant1, deltaFormant2, etc., as needed, and potentially as EQ too.

Modes still exist, and they all reference the same underlying mechanisms described above. Also, they still have their own lazy Amplitude sliders, which mean we can mix perceptually smoothly from one mode to the other. All modes use all paramters as desired. Processing blocks are used by all the modes (even if their effects are not immediately present, it can still matter, like for LipRounding by vowels).
- Vowel mode: Voiced component only.
- Fricitive mode: Voiceless + voiced, with arbitrarily long amplitude envelope. (Amplitude being any and all amplitudes required for achieving the sound here, I won't list all of the amplitude paramters.)
- Plosive (or stop) mode: Same as fricitive with a very short, burst-like amplitude envelope.
- Trill mode: Similar to stop mode, but a series of softer bursts in amplitude and nasality.
- Tap mode: Trill mode, only one trill.
- Liquid mode: Essentially vowel mode with extra formant characteristics.
- Nasal mode: Nasality set all the way up, and pretty much like vowel mode with extra characteristics.
- Approximant mode: Essentially vowel mode with extra formant characteristics, like liquid mode.
The extra characteristics are stored in the consonant lookup table.
Every phone (vowels and consonants) have a LipRounding associated with them, of course, and only consonants are affected by it.

TARGETING SYSTEM 1: Coarticulation logic: When a pronouncing the next phone in a sequence, the transition to the required mode begins. The parameters have inertia ("lazy mouth", coarticulation etc.) and they will try to reach the next target, which is the parameter configuration for the next phone. The mode transition happens by mixing the previous mode down, and mixing the new one up.
Because vowels are a space, with a single state, this state is shared between modes, but it is **only controlled by the current mode being transitioned into** (or just... current mode). The preivous mode, during the mixing of modes, can still get affected by the changing state though, to make coarticulation happen.)))
=== OR ===
TARGETING SYSTEM 2: Coarticulation logic: I mean I can get more complex: take the current point in time t, look around it, see what kind of phones are around that window, evaluate what their state wants to be (targets), average those tartgets in a weighted manner (the one closer to the current time t gets a lot more weight, kinda like a bell curve around time t), and that's the current *global target*, which the system attempts to move to. Yeah, this would make anticipatory effects work much more smoothly. Essentially a rolling window of phones with center-weighted target averaging, resulting in a GLOBAL TARGET that the system attempts to reach at the current time t. (That requires a lot of little stuff on the parameter level, but may be more natural.) Yes, this may *seem* more complex, but it doesn't actually require a lot more parameters, only a lot more synthesis logic and math, but once that's figured out, it just works. (About modes: (See: I mean... maybe... but now I see modes as not really "modes", rather "generation styles". "For this consonant, use the vowel space at this point, get this formant data from the lookup table, use these amplitude envleopes, and use all these nasality etc. settings, to get the exact, pure consonant without context." That's a "mode"... it's really just a lookup table for lookup tables lol So I guess I could just smooth it out like there were no modes at all. Modes are just... ways of generating stuff. ESSENTIALLY "RECIPES" FOR PHONES.) BUT CONSONANTS NEED LESS SMOOTHING AND VOWELS NEED WIDER SMOOTHING (different kernels for Gaussian smoothing:
```
From ChatGPT:
vowels: wide Gaussian (strong smoothing)
fricatives: medium width
stops: very narrow or even impulse-like weighting
```
Summary of ChatGPT about this: Your system has converged to a kernel-smoothed target trajectory speech synthesizer driven by phoneme annotations, with dynamical parameter tracking and layered excitation, which is a much more principled and scalable formulation than the earlier mode-based design.
See last three messages with ChatGPT for more info on this Gaussian thing.

About Breathiness: Yes, it's just /h/, but it's affected by the vowel space as well as LipRounding, actually. It's essentially a separate third system (block), but it's still part of the system. However, as a separate block, it only takes inputs, and outputs breathiness at a specified amplitude, which can be directly mixed into the output. That's the plan.

EACH PHONE IS IN A LOOKUP TABLE. EACH PHONE HAS A MODE ATTACHED, WHICH JUST MEANS WHICH TABLES IT GETS DATA FROM (VOWEL SPACE, CONSONANT LOOKUP) AND WHAT ENVELOPES IT SHOULD HAVE. THAT'S IT. IN FACT, THERE COULD BE ENVELOPE CALCULATOR FUNCTIONS ATTACHED TO EACH "MODE".
Not every parameter gets an envelope, that would be far too much. Envelopes can also be broken up to categories:
```
From ChatGPT:
1. Fast dynamics (enveloped)
amplitude
noise level
burst energy
2. Medium dynamics (lazy)
F1/F2 trajectory
lip rounding
tension
3. Static per phone
template selection
consonant identity
base formant anchor

This keeps:

expressiveness
but preserves control
```


===


Ignore this below, ideas for later and non-finished requirements:
```
All parameter names of the mouth are written in PascalCase. (Even though I'm using Python.)
All continuous parameters are "lazy", according to the simplification of coarticulation etc. I'm calling the "lazy mouth" concept. Which essentially means that the mouth cannot teleport from one state to another, and must glide there. This applies to all named parameters and state spaces in their own way.

Very simple source-filter model based approach, and state targets:
- Sources: a sine wave with an extra sawtooth component (the amplitude of which is adjusted by the Tension parameter) as a source (called vocal source) and a noise source.
- Filter(s): There are multiple modes for the filters, which essentially means that there are different little "sub-synthesizers" in the synthesizer.
- The program goes through each phone sequentially, in a timed manner. When the next syllable is up, the mouth state associated with the phone is set as a "target state", and the mouth will try reaching that state. The process of the mouth moving can be interrupted by a "target state change", which means the mouth starts accelerating towards another phone before reaching the first one. This can introduce natural coarticulation effects into the synthesizer with minimal coding effort. This idea comes strictly from the "lazy mouth" concept and therefore coarticulation. (Yes, here, the mouth is not anticipating sounds, but rather trails behind what should be spoken already, but that has a similar effect anyway. IDEA FOR LATER: The mouth should get the next two targets and calculate a trajectory for just those two, to follow until the targets are updated. This could introduce more anticipatory coarticulation.)

Generation pipeline:
Sources -> Sub-synthesizer I (filtering devices) -> Sub-synthesizer II (modes) -> output

## Sources (stage I)
Each source corresponds to one of the simplified components of speech: a sound that the vocal chords prodouce (vocal source) and a sound used for synthesizing hissing stuff (noise source, which is just white noise).
Each of the two sources has an Amplitude paramter. There is only one of this paramter in the entire synthesizer, which means different modes don't get to have their own little versions of the generators: the same generators, with the same lazyness, same current state, are used for all filtering modes.
PARAMETERS: both has Amplitude, vocal source has Tension (sawtooth Amplitude), and noise source has Tension (extra Amplitude)

## Filters
### filtering devices (stage II)
The next step in the synthesis hierarchy is the vocal and noise filting devices. These are sub-synthesizers used on a higher-level by the modes (discussed next) to generate phones. Each of these shares the source parameters (discussed more cleanly in the modes section.) These filtering devices are the little sub-devices used by the modes to generate an actual phone. IMPORTANTLY, each source has exactly one filtering device associated with it, which means there are two filtering devices in total: vocal filtering device (or "voiced component synthesizer device") and noise filtering device (or "voiceless component filtering device"). In generation, every phone is built from a voiced + a voiceless component, and so these two devices are enough to build a phone. PARAMETERS: both has multiple ResonantFilterParameters (for as many formant and anti-formant generating filters as needed), with each resonant filter having its own ID (like "F0", "F1" etc.), and also an EQFilterParameter each. The EQ is applied first, then the resonant filters.

### modes (stage III)
Above these are entire filter-subsystems, called "modes". These modes act like their own little sub-synthesizer, therefore each has its own Amplitude. The sub-synthesizers share the vocal filtering device, (therefore if there would be two competing sub-synthesizers, wanting to generate two different phones at once, the two competing parameter accelerations would be applied to the same vocal filtering device and in the end neither would perfectly pronounce what it wanted, but we would get an average. But this never happens, really, at least for now, because the synthesizer can only be in one state at a time.) This ensures that the nonextent tongue's psition is shared between modes for coarticulation purposes. The noise filtering device *can* be shared between modes, but only between CONSONANT CLUSTERS, and nothing else. Also, interpolation is just done by interpolating the foramnts of each consonant logarithmically (or some other way, TODO, this could also be parametrized for creating different characters). Essentially, CV (consonant, vowel) and VC (vowel consonant) clusters are EXCEPTIONS TO THE COARTICULATION RULES, THEY ARE NOT "LAZY", BUT ONLY IN THE NOISE FILTERING DEVICES.

The synthesizer can only be in one mode at a time.

So, as I said, each mode has its own Amplitude. When switching from, for example, synthesizing a /t/ to an /a/, the "t-generator's Amplitude" gets lowered quickly, and the "a-generator's Amplitude" gets turned up. This helps coarticulation.

The whole concept of modes was created to simplify acoustic synthesis into only a few discrete modes of generation, like vowel synthesis, fricitive synthesis, stop synthesis etc.

THE MODES CAN HAVE THE SAME PARAMETERS AS THE SOURCES, SINCE THE FILTERS/MODES ARE ONE LEVEL HIGHER IN THE SYNTHESIS PIPELINE AND CONTROL THE SOURCES DIRECTLY. THEREFORE THEY NEED MAY NEED THEIR OWN VERSION OF "AMPLITUDE" AND "TENSION" FOR EXAMPLE.

### Modes
There are different modes which correspond to different types of phones with their own little requirements for sounding right.
- Vowel mode: This mode generates vowels. It uses the vowel space diagram by Dr. Geoff Lindsey (or the diagram used in Praat) to generate vowels with tongue velocity. PARAMETERS: VoicedDiagramX, VoicedDiagramY, Rhoticity, Nasality, Breathyness, Tension. All of these parameters are used to compute the resulting F1, F2, F3 etc. formants. Note that the "vowel" diagram also contains dots corresponding to *voiced consonants* too, since those use the "vowel" (called "voiced" here) diagram for their voiced component in the same space as vowels. MORE ABOUT THE VOICED DIAGRAM LATER.
- Fricitive mode: This mode generates fricitives, both voiced and voiceless. The voiced part is generated by the vocal filtering device (shared amongst all modes), and the voiceless part is generated by the noise filtering device (shared only amongst consonant modes). Because the noise filtering device is only shared amongst consonant modes, CV and VC (consonant, vowel, vowel, consonant) clusers don't experience coarticulation. PARAMETERS: VoicelessDiagram (as many dimensions as needed for the formants), Nasality, Breathyness, Tension
etc. I'm lazy, I'll do it later, I may have to rewamp a few things

## Targets

For more concrete data, I can record my own voice.
For input, I can use some simple descriptive rules that may not adhere strictly to correct writing in the language in use, but are still useful, kinda how SynthV represents different phonemes.
This "intermediate input" can be converted to IPA symbols which are actually fed into the synthesizer.

The length of consonants and vowels can also just be simple parameters.

There is no prosody yet, only "singing", so to speak.
```
