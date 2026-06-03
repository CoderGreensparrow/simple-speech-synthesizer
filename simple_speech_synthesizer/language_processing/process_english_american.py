"""
Internal module for processing English input text. DIALECT: North American Standard English.
"""

from process_base import BasePhonemeProcessor
from constants import LANGUAGE_CODES
from nltk.corpus import cmudict

ARPABET_TO_IPA = {

}

class EnglishAmericanPhonemeProcessor(BasePhonemeProcessor):
    """
    English american phoneme processor (text to phoneme).
    """
    def __init__(self, text: str, lang_code: str):
        super().__init__(text, lang_code)
        # https://stackoverflow.com/questions/33666557/get-phonemes-from-any-word-in-python-nltk-or-other-modules
        self.cmudict_words = cmudict.dict()


    def to_cmudict_phonemes(self, word: str):
        """
        Converts the input text to phonemes with nltk.corpus.cmudict.
        :return: ARPABET phoneme mapping
        """
        return self.cmudict_words[word]

    def arpabet_to_ipa(self, arpabet_phone: str):
        """
        Mapping from arpabet to IPA.
        :return: IPA mapping
        """
        return ARPABET_TO_IPA[arpabet_phone]


    def 