from dataclasses import dataclass

from simple_speech_synthesizer.base.types import Envelope, Point, Segment

@dataclass(frozen=True)
class Note:
    """
    Represents one sung note (preferably with one syllable).
    :param note_start: Shows note's start time measured from the start of the audio file in seconds.
    :param note_end: Shows note's end time measured from the start of the audio file in seconds.
    :param phoneme_ids: The IDs of all the phonemes (as included in the chosen character's phoneme_data.json) in order of appearance.
    :param phoneme_times: Shows the switching time from the previous phoneme to the current one. Aka. it shows the start time of the current phoneme, and the next phoneme's phoneme_time determines this current phoneme's end time. Ths is measured from the beginning of the current note (note_start) in seconds, and *not* the beginning of the audio file.
    :param base_pitch: The base pitch of the note.
    :param pitch_delta: Denotes manual deviations from the base pitch.
    """
    note_start: float
    note_end: float
    phoneme_ids: tuple[str, ...]
    phoneme_times: tuple[float, ...]
    """Describes the start time of each phoneme measured from the start of the note.
    The phonemes ends are the start of the next phoneme, or the end of the note respectively.
    Every phoneme_id has exactly 1 time associated with it at the same index in phoneme_times."""
    # These Envelopes also only take control during the duration of the note. Their t=0 timepoint means note_start. t=duration means note_end.
    # Going through each Note and summing them up to one big Envelope will be the final control Envelope.
    pitch_delta: Envelope | None  # fundamental pitch
    base_pitch: float

    Volume: Envelope
    NasalityDelta: Envelope  # modifies the original nasality (since each phoneme has different levels of it by default)
    BreathinessDelta: Envelope  # modifies the original breathiness
    Tension: Envelope  # softness - hardness modifier
    MachineGrowl: Envelope  # lets the Blit run rampant
    LipRoundingDelta: Envelope  # WIP, may not be implemented; modifies the formants for liprounding
    VocalGenderDelta: Envelope  # modifies the perceived gender of the sound (similar to how other vocal synths use a gender property)
    ThroatJitter: Envelope

    def __post_init__(self):
        if len(self.phoneme_ids) != len(self.phoneme_times):
            raise ValueError("Each phoneme_id should have one phoneme_time associated with it, so self.phoneme_ids == self.phoneme_times. (Error a Note class.)")


@dataclass(frozen=True)
class Input:
    character_dir_path: str
    output_filepath: str
    # DURATION CALCULATION IS HANDLED BY THIS LAYER
    notes: tuple[Note, ...]

    def __post_init__(self):
        # CHECK FOR OVERLAPPING NOTES
        sorted_notes = sorted(self.notes, key=lambda note: note.note_start)
        for i, note in enumerate(sorted_notes):
            if note.note_end > sorted_notes[i + 1].note_start:
                raise ValueError(f"Notes in sing_timing Input mustn't overlap in time. "
                                 f"Note #{i+1} ({' '.join(note.phoneme_ids)}) overlaps with next note between {sorted_notes[i+1].note_start} and {note.note_end} seconds.")
