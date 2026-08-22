"""
NOT IMPLEMENTED
SYNTHESIZER LAYER 1A: timing (SPECIFICALLY FOR SINGING)
Using exposed, higher-level (phoneme and prosody level, like pitch curves and breathiness envelopes) control parameters,
it generates the timing of all phonemes, with their specific parameters tuned to liking.
"""

from simple_speech_synthesizer.sing_timing import types as this_layer_types
#  from simple_speech_synthesizer.sing_timing import input_validation
from simple_speech_synthesizer.targeting import types as next_layer_types

from simple_speech_synthesizer.base.load_character import load_character
from simple_speech_synthesizer.base.types import Envelope, Point, Segment
from simple_speech_synthesizer.base import utils

from dataclasses import dataclass

@dataclass(frozen=True)
class __return_value_GloballyAlignedLocalEnvelopes:
    """
    Local Envelopes from a note with their timings properly put to their global time.
    """
    new_Volume: Envelope
    new_F0: Envelope
    new_NasalityDelta: Envelope
    new_BreathinessDelta: Envelope
    new_Tension: Envelope
    new_MachineGrowl: Envelope
    new_LipRoundingDelta: Envelope
    new_VocalGenderDelta: Envelope
    new_ThroatJitter: Envelope

def process_Note_phonemes_to_TimedPhonemes(input_, note: this_layer_types.Note) -> tuple[tuple[next_layer_types.TimedPhoneme, ...], __return_value_GloballyAlignedLocalEnvelopes]:
    # TimedPhoneme
    phonemes = []
    for i, id, start in enumerate(zip(note.phoneme_ids, note.phoneme_times)):
        # TODO do input validation
        if i + 1 == len(note.phoneme_times):
            end_time = note.note_end
        else:
            end_time = note.phoneme_times[i+1]
        phonemes.append(
            next_layer_types.TimedPhoneme(id, start, end_time)
        )

    # Create F0 local envelope
    if note.pitch_delta is not None:
        new_F0_points = [Point(point.t + note.note_start, point.v + note.base_pitch) for point in note.pitch_delta.points]
        new_F0_segments = note.pitch_delta.segments
        new_F0 = Envelope(tuple(new_F0_points), new_F0_segments)
    else:
        new_F0 = utils.new_flat_Envelope(note.note_start, note.note_end, note.base_pitch)

    # Handle other local envelopes to be able to be inserted to global
    new_Volume  = utils.shift_Envelope_by_time(note.Volume, note.note_start)
    new_NasalityDelta = utils.shift_Envelope_by_time(note.Volume, note.note_start)
    new_BreathinessDelta = utils.shift_Envelope_by_time(note.NasalityDelta, note.note_start)
    new_Tension = utils.shift_Envelope_by_time(note.BreathinessDelta, note.note_start)
    new_MachineGrowl = utils.shift_Envelope_by_time(note.Tension, note.note_start)
    new_LipRoundingDelta = utils.shift_Envelope_by_time(note.MachineGrowl, note.note_start)
    new_VocalGenderDelta = utils.shift_Envelope_by_time(note.LipRoundingDelta, note.note_start)
    new_ThroatJitter = utils.shift_Envelope_by_time(note.VocalGenderDelta, note.note_start)

    return tuple(phonemes), __return_value_GloballyAlignedLocalEnvelopes(
        new_Volume,
        new_F0,
        new_NasalityDelta,
        new_BreathinessDelta,
        new_Tension,
        new_MachineGrowl,
        new_LipRoundingDelta,
        new_VocalGenderDelta,
        new_ThroatJitter
    )


def sort_notes(notes: list | tuple[this_layer_types.Note, ...]) -> tuple[this_layer_types.Note, ...]:
    return tuple(sorted(notes, key=lambda note: note.note_start))


def process_input(input_: this_layer_types.Input) -> tuple[float, tuple[next_layer_types.TimedPhoneme, ...], next_layer_types.EnvelopeTargets]:
    character = load_character(input_.character_dir_path)

    # PROCESS NOTES
    notes = sort_notes(input_.notes)

    global_envelopes_initialized = False
    duration = 0
    phonemes = []
    for note in notes:
        # global duration measure
        if note.note_end > duration:
            duration = note.note_end
        # phonemes to global timed_phonemes
        local_phonemes, __GALE = process_Note_phonemes_to_TimedPhonemes(input_, note)
        phonemes.extend(local_phonemes)
        # insert local envelopes to global
        if not global_envelopes_initialized:
            Volume           = __GALE.new_Volume
            F0               = __GALE.new_F0
            NasalityDelta    = __GALE.new_NasalityDelta
            BreathinessDelta = __GALE.new_BreathinessDelta
            Tension          = __GALE.new_Tension
            MachineGrowl     = __GALE.new_MachineGrowl
            LipRoundingDelta = __GALE.new_LipRoundingDelta
            VocalGenderDelta = __GALE.new_VocalGenderDelta
            ThroatJitter     = __GALE.new_ThroatJitter
            global_envelopes_initialized = True
        else:
            Volume           = utils.list_extend_Envelope_with_Envelope(Volume          , __GALE.new_Volume)
            F0               = utils.list_extend_Envelope_with_Envelope(F0              , __GALE.new_F0)
            NasalityDelta    = utils.list_extend_Envelope_with_Envelope(NasalityDelta   , __GALE.new_NasalityDelta)
            BreathinessDelta = utils.list_extend_Envelope_with_Envelope(BreathinessDelta, __GALE.new_BreathinessDelta)
            Tension          = utils.list_extend_Envelope_with_Envelope(Tension         , __GALE.new_Tension)
            MachineGrowl     = utils.list_extend_Envelope_with_Envelope(MachineGrowl    , __GALE.new_MachineGrowl)
            LipRoundingDelta = utils.list_extend_Envelope_with_Envelope(LipRoundingDelta, __GALE.new_LipRoundingDelta)
            VocalGenderDelta = utils.list_extend_Envelope_with_Envelope(VocalGenderDelta, __GALE.new_VocalGenderDelta)
            ThroatJitter     = utils.list_extend_Envelope_with_Envelope(ThroatJitter    , __GALE.new_ThroatJitter)

    # MAKE GLOBAL ENVELOPES

    envelope_targets = next_layer_types.EnvelopeTargets(
        Volume,
        F0,
        NasalityDelta,
        BreathinessDelta,
        Tension,
        MachineGrowl,
        LipRoundingDelta,
        VocalGenderDelta,
        ThroatJitter
    )

    return duration, phonemes, envelope_targets

def transform(input_: this_layer_types.Input):
    # TODO for later: breathing?
    duration, phonemes, envelope_targets = process_input(input_)
    output = next_layer_types.Input(
        character_dir_path=input_.character_dir_path,
        output_filepath=input_.output_filepath,
        duration=duration,
        phonemes=phonemes,
        envelope_targets=envelope_targets
    )
    return output

r"""
EXAMPLE OF OUTPUTTED Input CLASS INSTANCE (taken from old orchestrator.py):
if __name__ == "__main__":
    from simple_speech_synthesizer.targeting.types import Input, TimedPhoneme, EnvelopeTargets
    from simple_speech_synthesizer.base.types import Envelope, Point, Segment

    from simple_speech_synthesizer.base.types import Envelope, Point, Segment

    i = Input(
        character_dir_path=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\characters\Greensparrow_JP",
        output_filepath=r"D:\PycharmProjects\simple-speech-synthesizer\simple_speech_synthesizer\testaudio.wav",
        duration=4,
        phonemes=(
            TimedPhoneme("<sil>", 0, 0.5),
            TimedPhoneme("hun_a", 0.5, 1),
            TimedPhoneme("hun_n", 1, 1.5),
            TimedPhoneme("hun_cs", 1.5, 2),
            TimedPhoneme("hun_a", 2, 2.5),
            TimedPhoneme("<sil>", 2.5, 3),
            TimedPhoneme("hun_a", 3, 3.11),
            TimedPhoneme("hun_n", 3.11, 3.25),
            TimedPhoneme("hun_cs", 3.25, 3.352),
            TimedPhoneme("hun_a", 3.352, 3.44),
            TimedPhoneme("<sil>", 3.44, 4),
        ),
        envelope_targets=EnvelopeTargets(
            Volume=Envelope((Point(0, -3), Point(3, -3)), (Segment("linear"),)),
            F0=Envelope((Point(0, 140), Point(3, 140), Point(3.25, 120)), (Segment("linear"), Segment("linear"),)),
            NasalityDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            BreathinessDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            Tension=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            MachineGrowl=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            LipRoundingDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            VocalGenderDelta=Envelope((Point(0, 0), Point(3, 0)), (Segment("linear"),)),
            ThroatJitter=Envelope((Point(0, 1), Point(3, 1)), (Segment("linear"),))
        )
    )
    o = process_targeting(i, full_stack=True)
    print(o)
"""