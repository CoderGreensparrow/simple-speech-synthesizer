"""
A piano roll frontend for the speech and singing synthesizer.

Will have general support for multiple speech synth backends.
This is achieved by the following:
- There is a connector layer (middle end) that has exposed inputs of basic types (Note, Envelope, StepFunction etc.).
- These are then processed for each backend separately and given to them in their respective input data types.

PLANS:
- Support my own engine (PEKSS).
- Add support for SAM (Software Automatic Mouth https://simulationcorner.net/index.php?page=sam) to be able to sing and speak
  directly from the editor (just like another voice).
- Maybe even add support for anything else.
"""