"""
Contains generators for certain things.
"""

from simple_speech_synthesizer.base.types import Envelope, Point, Segment

def new_flat_Envelope(start: float, end: float, value: float) -> Envelope:
    return Envelope(
        (Point(start, value), Point(end, value)),
        (Segment("linear"),)
    )

def shift_Envelope_by_time(envelope: Envelope, t: float) -> Envelope:
    """
    Shifts the Envelope left or right on the time axis (in seconds).
    """
    new_points = [Point(point.t + t, point.v) for point in envelope.points]
    return Envelope(tuple(new_points), envelope.segments)

def list_extend_Envelope_with_Envelope(envelope: Envelope, other: Envelope) -> Envelope:
    """
    Appends an envelope at the end of another envelope directly on list-level.
    (If the two envelopes are not in order in a timely manner, then there will be a conflict, as points won't be in the order they should come.)
    """
    return Envelope(
        points=envelope.points + other.points,
        segments=envelope.segments + other.segments
    )

def partially_override_Envelope(base: Envelope, other: Envelope) -> Envelope:
    """
    Takes one Envelope, and overrides only the part of it that is defined by another Envelope.
    [other[, so base is overridden at the starting time of other, but it is not overridden at the ending time of other.
    """
    points = list(base.points)[::-1][::-1]
    segments = list(base.segments)[::-1][::-1]
    other_points_rev = list(other.points)[::-1]
    other_segments_rev = list(other.segments)[::-1]
    i = 0
    handle_segmentless_last_point = False
    while points[i].t < other.min_t:
        i += 1
    while points[i].t < other.max_t:
        if other.min_t <= points[i].t < other.max_t:
            points.pop(i)
            if i < len(segments):
                segments.pop(i)
            else:
                handle_segmentless_last_point = True
    for point in zip(other_points_rev, other_segments_rev):
        if not handle_segmentless_last_point:
            pass
            # TODO
        else:
            # TODO
            handle_segmentless_last_point = False
    # TODO