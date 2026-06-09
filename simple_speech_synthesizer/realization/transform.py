"""
LAYER 4: realization
Evaluates higher-level acoustic parameters into the lower-level ones.
So Nasality, Breathiness etc. gets all encoded in F0, F1, F2, noise_amp, voiced_amp etc.
It makes the higher-level data synthesizer-friendly.

The actual conversion from custom types (Envelope) to pyo's types happens in the layer below.
"""