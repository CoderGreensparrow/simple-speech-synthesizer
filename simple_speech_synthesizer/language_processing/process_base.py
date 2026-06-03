"""
Base classes for processing text in different languages (to phoneme conversion).
Also contains the Utterance class which acts as an output.

SPECIFICATION OF OUTPUT TREE STRUCTURE:

Utterance contains multiple Clauses contains multiple
Words contains Phones.
Each layer can provide extra information for synthesis:
- Utterance (no extras, just a container).
- Clause: provides emotional mood (happy, down, angry, cynical, encouraging) and TODO provides a "grammatical mood" (is there a comma after, is it declerative, is it interrogative etc.)
- Word: TODO provides focus of clause/emphasized words in the form of an integer where a higher integer means more emphasis relative to smaller integers
- Phone: provides stress placement.
"""

import typing

class Phone:
    def __init__(self, IPA_phone: str, metadata: dict = None):
        """
        A language-specific phoneme with an ID.
        :param phoneme_ID: The phoneme to pronounce, references an internal ID, language-independent
        :param metadata: A dictionary containing extra metadata. (Like primary/secondary stress on the phone, downstep in Japanese etc.)
        """
        self.IPA_phone = IPA_phone
        self.metadata = metadata

class Word:
    def __init__(self, phones: list[Phone], emphasis_level: int = None):
        self.phones = phones
        self.emphasis_level = emphasis_level

class Clause:
    def __init__(self, words: list[Word], emotional_mood: str = None, grammatical_mood: str = None):
        self.words = words
        self.emotional_mood = emotional_mood
        self.grammatical_mood = grammatical_mood

class Utterance:
    def __init__(self, clauses: list[Clause], lang_code: str):
        self.clauses = clauses


class BasePhonemeProcessor:
    """
    The base class for all text to phoneme (and other data) converter classes for all languages.
    """
    def __init__(self, text: str, lang_code: str):
        """
        :param text: Input text in human-readable orthography.
        :param lang_code: The internal language code. Use one of the values from the LANGUAGE_CODES tuple in this module.
        """
        self.text = text
        self.lang_code = lang_code

    def process(self):
        pass