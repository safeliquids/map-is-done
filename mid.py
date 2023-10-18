import argparse as ap
import json
from os import PathLike
from typing import Any


class Registry:
    """registers actions and verifies, if they are supported"""
    supported_actions = [
        "set_map_name",
        "remove_datapacks",
        "zip",
        "set_gamerules",
        "remove_player_scores",
        "remove_player_data",
        "set_difficulty",
        "set_default_gamemode",
        "explode_last_played"
    ]

    def __init__(self, original_world_folder: PathLike, output_directory: PathLike):
        self.original_world_folder = original_world_folder
        self.output_directory = output_directory

        self.additional_files = []
        self.world_name = None
        self.world_folder_name = None
        self.archive_name = None

        self.should_remove_player_data = False
        self.reset_scores_of_players = []
        self.datapacks_to_remove = []
        self.level_dat_modifications = {}

        self.files_to_remove = []

    @classmethod
    def supports(cls, action_type: str) -> bool:
        return action_type in cls.supported_actions

    def register(self, action: dict):
        """registers an action in json format
        raises ValueError if the action type is unsupported or the action
        definition is invalid.

        In general, additional fields of the action definitioin (and, by
        extention, the validity of a given action definition,) depend on the
        actino type.
        
        Additional relevant data is stored in this object."""
        action_type = action["type"]
        match action_type:
            case "set_map_name":
                world_name = action.get("world_name")
                self._must_be_string(world_name, "world_name")
                folder_name = action.get("folder_name")
                self._must_be_string(folder_name, "folder_name")
                
                self.world_name = world_name
                self.world_folder_name = folder_name

            case "remove_datapacks":
                names = action.get("names")
                self._must_be_list_of_strings(names, "names")
                
                self.datapacks_to_remove += ["file/" + n for n in names]
                self.files_to_remove += ["datapacks/" + n for n in names]

            case "zip":
                archive_name = action.get("archive_name")
                self._must_be_string(archive_name, "archive_name")
                
                self.archive_name = archive_name

            case "set_gamerules":
                gamerules = action.get("gamerules")
                if not isinstance(gamerules, dict):
                    raise ValueError(f"expected a compound of gamerules")
                for rule, value in gamerules.items():
                    if not isinstance(rule, str) or not isinstance(value, str):
                        raise ValueError(
                            f"gamerules and their values must be strings")
                
                self.level_dat_modifications |= {"gamerules":gamerules}

            case "remove_player_scores":
                name = action.get("player")
                self._must_be_string(name, "playername")
                
                self.reset_scores_of_players += name

            case "remove_player_data":
                self.should_remove_player_data = True
                self.files_to_remove += ["playerdata/", "advancements/", "stats/"]

            case "set_difficulty":
                d = {"peaceful":0, "easy":1, "normal":2, "hard":3}
                difficulty = action.get("difficulty")
                if isinstance(difficulty, int):
                    if difficulty < 0 or difficulty > 3:
                        raise ValueError(
                            "difficulty must be a string or between 0 and 3 inclusive.")
                    numerical_difficulty = difficulty
                elif isinstance(difficulty, str):
                    if difficulty not in d:
                        raise ValueError(
                            'difficulty must be a number or one of "peaceful", "easy", "normal", "hard".')
                    numerical_difficulty = d[difficulty]
                else:
                    raise ValueError("difficulty must be a string or number")
                
                self.level_dat_modifications["Difficulty"] = numerical_difficulty

            case "set_default_gamemode":
                g = {"survival":0, "cretive":1, "adventure":2, "spectator":3}
                gamemode = action.get("gamemode")
                if isinstance(gamemode, int):
                    if gamemode < 0 or gamemode > 3:
                        raise ValueError(
                            "gamemode must be a string or between 0 and 3 inclusive.")
                    numerical_gamemode = gamemode
                elif isinstance(gamemode, str):
                    if gamemode not in g:
                        raise ValueError(
                            "gamemode must be a number or one of 'survival', 'creative', 'adventure' and 'spectator'.")
                    numerical_gamemode = g[gamemode]
                else:
                    raise ValueError("gamemode must be a string or number")
                
                self.level_dat_modifications["GameType"] = numerical_gamemode

            case "explode_last_played":
                # long max: 9_223_372_036_854_775_807
                self.level_dat_modifications["LastPlayed"] = 9_223_372_036_854_775_807

            case _:
                raise ValueError(
                    f"action type `{action_type}' is not supported!")

        print(f"registered action of type `{action_type}'")

    @classmethod
    def _must_be_string(cls, something: Any, name: str):
        if not isinstance(something, str):
            raise ValueError(f"{name} must be a string")

    @classmethod
    def _must_be_list_of_strings(cls, something: Any, name: str):
        if not isinstance(something, list):
            raise ValueError(f"{name} must be a list of strings")
        if not all(map(lambda x: isinstance(x, str), something)):
            raise ValueError(f"elements of {name} must be strings")


def extract_config(raw_config: dict) -> dict:
    """Extracts only relevant fields from configuration.
    Also verifies that all required fields are present."""
    config = {}
    for f, t in zip(["world", "output_directory", "actions"], [str, str, list]):
        field = raw_config.get(f)
        if field is None or not isinstance(field, t):
            raise ValueError(f"config field {f} is missing or of invalid type")
        config[f] = field
    return config


if __name__ == "__main__":
    argument_parser = ap.ArgumentParser(
        description="A data-driven tool for getting Minecraft maps ready for release.")
    argument_parser.add_argument(
        "--json", action="store", type=str, required=True,
        metavar="<path/to/config.json>",
        help="use this configuration file in json format")
    args = argument_parser.parse_args()

    with open(args.json, "r", encoding="utf-8") as conf_file:
        raw_config = json.load(conf_file)
    config = extract_config(raw_config)

    print("=" * 40)
    print("resulting config:")
    print(json.dumps(config, indent=4))
    print("=" * 40)

    reg = Registry()
    for action in config["actions"]:
        reg.register(action)
    print("=" * 40)
