"""
internal
loads the character information required for the targeting layer
ONLY LOADS PHONEME_DATA.JSON AND ATTACHED JSON FILES
"""

import json
import os
from dataclasses import dataclass


@dataclass
class Character:
    phoneme_data: dict
    acoustic_data: dict
    manner_data: dict


def load_character(path: str) -> Character:
    """
    INTERNAL FUNCTION
    Loads a character's databases from a specific directory.
    :param path: The directory of the character's databases.
    :return: A Character(phoneme_data, acoustic_data, manner_data) dataclass instance.
    """
    phoneme_data = json.loads(open(os.path.join(path, "phoneme_data.json"), "r", encoding="utf-8").read())
    acoustic_parameter_data = json.loads(open(os.path.join(path, "acoustic_parameter_data.json"), "r", encoding="utf-8").read())
    manner_data = json.loads(open(os.path.join(path, "manner_data.json"), "r", encoding="utf-8").read())

    return Character(phoneme_data, acoustic_parameter_data, manner_data)