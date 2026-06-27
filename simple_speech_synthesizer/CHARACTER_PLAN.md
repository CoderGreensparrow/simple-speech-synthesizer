Because other files are getting more polluted, here's everything that I'll do to have different characters,
plus some other fixes for low/high formant synthesis.

1. Fixing F0 > F1 problem

When singing high, F0 can become greater than F1. This is wrong.
In real singing, this is accounted for by physically taking a different mouth shape,
usually by dropping the jaw, making F1 greater.
A good method is to just have a minimum difference between F0 and F1, linearly in frequency.
This minimum difference is CHARACTER-SPECIFIC.
Therefore:
F1=max(F1_orig,F0+minimum_freq_difference_between_the_two)

Bandwidth also has to be modified in this case.
In my case,
IT WILL JUST FIX THE Q VALUE AS THE F1 IS SHIFTED UPWARDS BY F0.

2. What defines a character?

Unique formant frequencies and bandwidths, yes.
Also, general spectral tilt:
- male voices generally have deeper spectral tilt
- female voices are more flat, with energy being concentrated in F2, F3 and above (especially for kawaii)
[TODO to keep amplitudes of formants consistent, and only be controlled from one place, maybe there shouldn't be an importance for formants...
only spectral tilt, that defines how strong low and high formants and frequencies generally are.
Or I keep the current system and just have a spectral tilt, that is a controllable -x db/octave rolloff.]
The rolloff is basically -6 db/octave by default.
- A ButLP has a rolloff of -12 db/octave (2nd order filter?)
- As I increase the frequency of the rolloff point, the overall volume of the voice source should inversely descrease,
  allowing the F3, F4, F5 extra formants to do the heavy lifting of making the sound bright,
  which also means that their importance should be doubled/tripled as needed.
  (The buzzing happens if I don't decrease the overall amplitude of the voice source,
  because as I make the rolloff point higher and higher,
  more harmonics of the fundamental frequency get included at full volume in the voice soruce,
  making the blit-ness of the blit come through.)

"The relationship between the amplitude of the fundamental frequency (H1) and the second harmonic (H2) heavily dictates perceived voice quality."
Now I misunderstood this as the first harmonic, the octave above F0, but... idk maybe it meant that.
That's another thing I have to control, whichever it is.
- In male or pressed (tense) voices, H2_amp about equals H1_amp.
- In soft, breathy, feminine voices, "the glottis stays open longer during each cycle (a high Open Quotient)" (gemini),
  therefore H1 completely dominates H2.
ALL OF THIS IS JUST GEMINI... I SHOULD DO EMPIRICAL TESTS TO SEE IF ITS ACTUALLY CORRECT.


NATURALNESS IMPROVEMENT?????
"""3. Glottal-Synchronous Noise (Dynamic Breathiness)

Right now, your noise source for breathiness is likely a constant stream mixed with the voice. In a real human throat, breathy air leakage is modulated by the vocal folds. The hiss of air happens primarily during the open phase of the glottal cycle.

    Action: Instead of mixing static white noise, try multiplying your breathiness noise source by the amplitude envelope or the rectified waveform of the voice_source itself. This creates pitch-modulated aspiration noise, which is a major component of a natural-sounding voice.

Now that you are considering character-specific lookup tables, how do you plan to handle the transitions between phonemes when moving between two completely different speaker profiles dynamically?"""

2026. 06. 25. I am here rn, as summerzied by Gemini:
```Gemini
1. The Dynamic Pitch Floor: High F0​ safely pushes F1​ upward to simulate a real jaw-drop.

2. Constant-Q Scaling: Bandwidths automatically expand when formants shift, killing the accidental digital whistles.

3. High-Frequency Excitement: Leaking targeted Blit harmonics above F3​ gives you that vibrant, excited feminine edge.

4. Gain Liberation: pyo.Balance keeps your volumes perfectly leveled, letting you delete all those hardcoded multiplier headaches.

5. Phase Diffusion: A subtle FX chain blurs the rigid digital alignment, giving your engine its signature "style."
```

3. Q factor changes per character
They are a damping_deltafactor for the Q calculation of each formant.
REPLACEMENT: Instead, those magic 50 and 0.05 valules are made into parameters like so (see old calculate_Q):
```python
    # 1. Calculate natural human bandwidth expansion (with a 50Hz floor)
    bandwidth = 50.0 + (0.05 * freq)
```
character_anime_girl = {
    "vowel_f_floor": 25.0,        # Lower floor = ultra-sharp, bright low formants
    "vowel_f_slope": 0.02         # Lower slope = high formants stay crisp and laser-focused
}
character_giant_ogre = {
    "vowel_f_floor": 90.0,        # Higher floor = muddy, massive, warm chest resonance
    "vowel_f_slope": 0.08         # Higher slope = high formants become incredibly wide and breathy
}
POTENTIAL CODE: (tension_mul doesn't exist in this though)
```python
def get_custom_character_q(freq, floor, slope):
    # Calculate bandwidth using the character's specific tissue traits
    bandwidth = floor + (slope * freq)
    
    # Convert straight to Q
    return freq / bandwidth
```
4. Vocal-tract-length (VTL) for GenderDelta
All formants are just scaled by a factor evenly. (multiplication, not addition)
$$F_{\text{character}} = F_{\text{base}} \times \text{VTL\_Scale}$$
5. spectral tilt and hill parameters for characters
The 3, 4 and 5 can be summarized as:
# Character Profile Object (part of it)
character_profile = {
    "vtl_scale": 1.18,          # Shifts the entire vocal size up/down
    "damping": 0.85,            # Controls throat wall texture (sharp vs soft)
    "tilt_type": "6db",         # Selects the glottal source slope
    "hill_freq": 2800,          # Dictates the speaker's main resonance zone
    "hill_boost": 8.0           # Dictates how intensely that zone punches through
}
# A complete, standalone character profile
character_vtuber = {
    # 1. Raw Phonetical Data (Straight from Praat!)
    "vowels": {
        "a": [808, 1210, 3005],
        "i": [450, 3264, 3760],
        "ε": [717, 1858, 2879]
    },
    # 2. Global Biological Lenses (The Macro Modifiers)
    "glottal_damping AKA. vtl_scale": 0.85,    # Tightens the bandwidths globally
    "damping": 0.85,            # Controls throat wall texture (sharp vs soft)
    "hill_freq": 3200,          # The presence zone peak
    "hill_boost": 10.0,         # How hard the presence zone pushes
    "gender_delta": 1.0         # Baseline size (can be warped dynamically later)
}