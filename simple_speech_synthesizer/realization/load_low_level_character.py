"""
internal
loads the character information required for the targeting layer
ONLY LOADS THE SYNTHESIS_PARAMETERS.JSON FILE'S CONTENTS
"""

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LowLevelCharacter:
    synthesis_parameters: dict


def load_low_level_character(path: str) -> LowLevelCharacter:
    """
    INTERNAL FUNCTION
    Loads a character's databases from a specific directory.
    :param path: The directory of the character's databases.
    :return: A LowLevelCharacter(synthesis_parameters) dataclass instance.
    """
    synthesis_parameters = json.loads(open(os.path.join(path, "synthesis_parameters.json"), "r", encoding="utf-8").read())

    return LowLevelCharacter(synthesis_parameters)