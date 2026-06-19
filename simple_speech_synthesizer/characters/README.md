This directory contains all the data for different characters.
A "character" is a directory with all the phoneme and other information databases necessary for speech synthesis.

REQUIRED DATA:
- acoustic_parameter_data.json (lookup table for specific acoustic configurations of the "mouth")
- phoneme_data.json (takes a configuration from parameter_data and associates a manner template with it)
- manner_data.json (stores how to produce the subtargets for different manners of articulation, but only the parameters for each type of articulation-generation-function, more details in template file)
- synthesis_parameters.json (controls global parameters, like other lower-level coarticulation strength, throat jitteriness etc.)

Just know that you don't have to make (in fact, it's not recommended) individual IPA phonemes without attaching them to a language.
You should make **language-specific phonemes with individual IDs**.
This will also allow for mixing and matching phonemes from different language later, which may make it much easier for the synth to speak *any* language.

A template for the data formats of the JSON files can be found in TemplateCharacter.