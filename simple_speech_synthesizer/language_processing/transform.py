"""
LAYER 1: language processing
NOT IMPLEMENTED
"""

from constants import LANGUAGE_CODES
from process_english_american import EnglishPhonemeProcessor
import _nltk_setup

def process(text: str, lang_code: str):
    """
    Process the input text with the correct class for the lang_code (all language codes are in the constants.LANGUAGE_CODES tuple).
    :param text: Input text in human-readable orthography.
    :param lang_code: Internal language code. Can be obtained from constants.LANGUAGE_CODES.
    :return: Returns a list with all info for phonemic synthesis in an internally specified format.
    """
    if lang_code in ("english_american", "english_british"):
        phoneme_processor = EnglishPhonemeProcessor(text, lang_code)