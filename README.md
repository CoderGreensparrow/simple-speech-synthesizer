# simple-speech-synthesizer
A simple speech synthesizer without rigorous internal structure.

Very simple source-filter model based approach:
- Sources: a sawtooth source and a noise source
- Vowels: The vowel space is pretty much just a setting of different formant frequencies. Potentially with gliding. Using EQ.
- Consonants: Using EQ and amplitude envelopes, I can generate artificial vowels.

For more concrete data, I can record my own voice.
For input, I can use some simple descriptive rules that may not adhere strictly to correct writing in the language in use, but are still useful, kinda how SynthV represents different phonemes.
This "intermediate input" can be converted to IPA symbols which are actually fed into the synthesizer.

The length of consonants and vowels can also just be simple parameters.

There is no prosody yet, only "singing", so to speak.
