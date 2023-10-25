import argparse as ap
import json
from os import PathLike
import pathlib as pl
import shutil
import time
from typing import Any
import zipfile as zf

import nbtlib


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
        "explode_last_played",
        "remove_paper_garbage",
        "remove_vanilla_garbage"
    ]

    def __init__(self):
        self.additional_files = []
        self.world_name = None
        self.world_folder_name = None
        self.archive_name = None

        self.reset_scores_of_players = []
        self.datapacks_to_remove = []
        self.level_dat_modifications = {}
        self.level_dat_removals = []
        
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
                self._remove_datapacks_inner(names)

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
                gamerules_as_nbt_strings = dict(
                    map(lambda it:(it[0],nbtlib.String(it[1])), gamerules.items()))
                if "GameRules" not in self.level_dat_modifications:
                    self.level_dat_modifications["GameRules"] = gamerules_as_nbt_strings
                else:
                    self.level_dat_modifications["GameRules"] |= gamerules_as_nbt_strings

            case "remove_player_scores":
                name = action.get("player")
                self._must_be_string(name, "playername")
                
                self.reset_scores_of_players.append(name)

            case "remove_player_data":
                self.files_to_remove += ["playerdata/", "advancements/", "stats/"]
                self.level_dat_removals.append(nbtlib.Path("Player"))

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
                self.level_dat_modifications["Difficulty"] = nbtlib.Int(numerical_difficulty)

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
                self.level_dat_modifications["GameType"] = nbtlib.Int(numerical_gamemode)

            case "explode_last_played":
                # long max: 9_223_372_036_854_775_807
                self.level_dat_modifications["LastPlayed"]\
                    = nbtlib.Long(9_223_372_036_854_775_807)

            case "remove_paper_garbage":
                self._remove_datapacks_inner(["bukkit"])
                self.level_dat_removals.append(nbtlib.Path('"Bukkit.Version"'))
                self.files_to_remove.append("paper-world.yml")

            case "remove_vanilla_garbage":
                self.files_to_remove += ["session.lock", "uid.dat", "level.dat_old"]
                self.level_dat_removals.append(nbtlib.Path("ServerBrands"))

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
    
    def _remove_datapacks_inner(self, names):
        self.datapacks_to_remove += ["file/" + n for n in names]
        self.files_to_remove += ["datapacks/" + n for n in names]


def _general_remove(path: PathLike):
    """delete the file pointed to by paty.
    IF path is a directory, first recursively delete all it's children and then
    remove it."""
    if not path.is_dir():
        path.unlink(missing_ok=True)
        return
    for child in path.iterdir():
        _general_remove(child)
    path.rmdir()


def _add_something_to_archive(source: pl.Path, archive: zf.ZipFile, path: str):
    if source.is_file():
        archive.write(source, path)
    elif source.is_dir():
        archive.mkdir(path)
        for child in source.iterdir():
            _add_something_to_archive(child, archive, path + "/" + child.name)
    else:
        raise ValueError("cannot add %s to archive (unsupported type)" % str(source))


def _zip_directory(dir_path: pl.Path, target: pl.Path, replacement_name: str | None = None):
    """compress given directory into a zip archive
    
    deprecated"""
    with zf.ZipFile(target, mode="w", compression=zf.ZIP_DEFLATED, compresslevel=-1) as z:
        _add_something_to_archive(dir_path, z, dir_path.name if replacement_name is None else replacement_name)


def _first_not_none(*stuff):
    for s in stuff:
        if s is not None:
            return s


def convert(registry: Registry, world: PathLike,
            output_directory: PathLike, temp_directory: PathLike):
    original_world = pl.Path(world)
    output_directory = pl.Path(output_directory)
    tempdir = pl.Path(temp_directory, str(time.time_ns()))

    ARCHIVE_NAME = _first_not_none(registry.archive_name, original_world.name)
    ARCHIVE_FILENAME = ARCHIVE_NAME + ".zip"

    NEW_WORLD_DIRECTORY_NAME = _first_not_none(registry.world_folder_name, original_world.name)

    # step 1: copy to temp directory
    WORKING_WORLD = tempdir / NEW_WORLD_DIRECTORY_NAME
    WORKING_WORLD.parent.mkdir(parents=True, exist_ok=True)
    if WORKING_WORLD.exists():
        _general_remove(WORKING_WORLD)
    shutil.copytree(original_world, WORKING_WORLD, symlinks=True)
    print("copied world '%s' to directory '%s', working world is '%s'" % (original_world, tempdir, WORKING_WORLD))
    # working_world_zip_path = tempdir / ARCHIVE_FILENAME
    # _zip_directory(original_world, working_world_zip_path, ARCHIVE_NAME)
    # zf.ZipFile(working_world_zip_path, "r").extractall(WORKING_WORLD.parent)
    # working_world_zip_path.unlink()

    """
    stuff that needs doing:
    - remove player scores
    - modify level.dat (changes and deletions)
      - also set the world name, which is separate for some reason
    - remove datapacks from level.dat, too

    - remove playerdata, stats and advancements
    - remove some datapacks (directories)
    - delete garbage files

    - zip the result or only move it to the output
    """

    # step 2: removing player scores
    scoreboard_path = WORKING_WORLD / "data" / "scoreboard.dat"
    if scoreboard_path.is_file() and registry.reset_scores_of_players != []:
        with nbtlib.load(WORKING_WORLD / "data" / "scoreboard.dat") as scoreboard:
            for player in registry.reset_scores_of_players:
                print("removing scores of player '%s'" % player)
                del scoreboard[nbtlib.Path('"".data.PlayerScores[{Name:"%s"}]' % player)]
    print("deleted player data")

    # step 3 and 4: remove things from level.dat, then apply modifications
    with nbtlib.load(WORKING_WORLD / "level.dat") as level_dat:
        data = nbtlib.Path('"".Data')
        
        # step 3: deletions
        for item in registry.level_dat_removals:
            del level_dat[data + item]
            print("deleted '%s' from level.dat" % str(item))
        # well. that was easy!

        # step 4: modifications
        level_dat[data].merge(registry.level_dat_modifications)
        print("applied modifications to level.dat")
        level_dat[data + nbtlib.Path("LevelName")] = nbtlib.String(registry.world_name)
        print("changed world name in level.dat")

        yeeting_packs = registry.datapacks_to_remove
        yeeting_pack_indices = {
            "Enabled":[],
            "Disabled":[]
        }
        for state in ["Enabled", "Disabled"]:
            for i, pack_name in enumerate(level_dat[data + nbtlib.Path('DataPacks.%s' % state)]):
                if pack_name in yeeting_packs:
                    print("datapack '%s' will be removed from level.dat, it was %"
                          % (pack_name, state))
                    yeeting_pack_indices[state].append(i)
            for index in reversed(yeeting_pack_indices[state]):
                del level_dat[data + nbtlib.Path('DataPacks.%s[%d]' % (state, index))]

    # step 5: remove unwanted files and directories
    for d in registry.files_to_remove:
        _general_remove(WORKING_WORLD / d)
        print("deleted %s" % d)

    # step 6: move result to output directory
    output_directory.mkdir(parents=True, exist_ok=True)
    if registry.archive_name is not None:
        archive_path = output_directory / ARCHIVE_FILENAME
        _general_remove(pl.Path(archive_path))
        shutil.make_archive(
            (output_directory/ARCHIVE_NAME).as_posix(), "zip",
            tempdir, NEW_WORLD_DIRECTORY_NAME)
        # _zip_directory(WORKING_WORLD, archive_path)
        
        # TODO: additional files that should go in the archive,
        # such as a README.
        print("zipped working world at '%s', archive is '%s'"
              % (WORKING_WORLD, archive_path))
    else:
        # move working world to output dir
        shutil.copytree(WORKING_WORLD, output_directory / NEW_WORLD_DIRECTORY_NAME, symlinks=True)
        print("copied working world '%s' to output dir, result is '%s'"
              % (WORKING_WORLD, output_directory/NEW_WORLD_DIRECTORY_NAME))
    
    # _general_remove(WORKING_WORLD)
        

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

    convert(reg, config["world"], config["output_directory"], ".mid")
