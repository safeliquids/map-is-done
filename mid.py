import argparse as ap
import json
import logging
from os import PathLike
import pathlib as pl
import shutil
import time
from typing import Any, Dict

import nbtlib


class Registry:
    """registers actions and verifies, if they are supported"""
    WEATHER_TYPES = ["clear", "rain", "thunder"]
    DIFFICULTY_VALUES = {"peaceful":0, "easy":1, "normal":2, "hard":3}
    GAMEMODE_VALUES = {"survival":0, "cretive":1, "adventure":2, "spectator":3}
    LONG_MAX = 9_223_372_036_854_775_807

    def __init__(self):
        self.world_name = None
        self.world_folder_name = None
        self.archive_name = None
        self.should_zip = False
        self.additional_files = []

        self.reset_scores_of_players = []
        self.datapacks_to_remove = []
        self.level_dat_modifications = {}
        self.level_dat_removals = []
        
        self.files_to_remove = []

    def register_action(self, action: dict):
        """registers an action in json format
        raises ValueError if the action type is unsupported or the action
        definition is invalid.

        In general, additional fields of the action definitioin (and, by
        extention, the validity of a given action definition,) depend on the
        actino type.
        
        Additional relevant data is stored in this object."""
        type = action["type"]
        match type:
            case "set_map_name":
                self._register_set_map_name(action)
            case "remove_datapacks":
                self._register_remove_datapacks(action)
            case "zip":
                self._register_zip(action)
            case "set_gamerules":
                self._register_set_gamerules(action)
            case "remove_player_scores":
                self._register_remove_player_scores(action)
            case "remove_player_data":
                self._register_remove_player_data(action)
            case "set_difficulty":
                self._register_set_difficulty(action)
            case "set_default_gamemode":
                self._register_set_default_gamemode(action)
            case "explode_last_played":
                self._register_explode_last_played(action)
            case "remove_paper_garbage":
                self._register_remove_paper_garbage(action)
            case "remove_vanilla_garbage":
                self._register_remove_vanilla_garbage(action)
            case "remove_fabric_garbage":
                self._register_remove_fabric_garbage(action)
            case "set_time":
                self._register_set_time(action)
            case "set_weather":
                self._register_set_weather(action)
            case _:
                msg = f"action type `{type}' is not supported!"
                logging.error(msg)
                raise ValueError(msg)
        logging.info("registered action %s" % str(action))

    def _register_set_map_name(self, action: dict):
        world_name = action.get("world_name")
        self._must_be_string(world_name, "world_name")
        self.world_name = world_name
        
        if "folder_name" not in action:
            self.world_folder_name = None
            return
        folder_name = action.get("folder_name")
        self._must_be_string(folder_name, "folder_name")
        self.world_folder_name = folder_name
        
    def _register_remove_datapacks(self, action: dict):
        names = action.get("names")
        self._must_be_list_of_strings(names, "names")
        self._remove_datapacks_inner(names)
        
    def _register_zip(self, action: dict):
        self.should_zip = True
        if "archive_name" not in action:
            self.archive_name = None
            return
        archive_name = action.get("archive_name")
        self._must_be_string(archive_name, "archive_name")
        self.archive_name = archive_name
        
        if "add_files" in action:
            self._must_be_list_of_strings(action["add_files"], "add_files")
            self.additional_files += action["add_files"]
        
    def _register_set_gamerules(self, action: dict):
        gamerules = action.get("gamerules")
        if not isinstance(gamerules, dict):
            raise ValueError("expected a compound of gamerules")
        for rule, value in gamerules.items():
            if not isinstance(rule, str) or not isinstance(value, str):
                raise ValueError("gamerules and their values must be strings")
        self._set_gamerules_inner(gamerules)
        
    def _register_remove_player_scores(self, action: dict):
        name = action.get("player")
        self._must_be_string(name, "playername")
        self.reset_scores_of_players.append(name)
        
    def _register_remove_player_data(self, action: dict):
        self.files_to_remove += ["playerdata/", "advancements/", "stats/"]
        self.level_dat_removals.append(nbtlib.Path("Player"))
        
    def _register_set_difficulty(self, action: dict):
        difficulty = action.get("difficulty")
        int_difficulty = self._str_or_int_to_int(
            difficulty, self.DIFFICULTY_VALUES, "difficulty")
        self.level_dat_modifications["Difficulty"] = nbtlib.Int(int_difficulty)
        
    def _register_set_default_gamemode(self, action: dict):
        gamemode = action.get("gamemode")
        int_gamemode = self._str_or_int_to_int(
            gamemode, self.GAMEMODE_VALUES, "gamemode")
        self.level_dat_modifications["GameType"] = nbtlib.Int(int_gamemode)
        
    def _register_explode_last_played(self, action: dict):
        if "time" not in action:
            self.level_dat_modifications["LastPlayed"]\
                = nbtlib.Long(self.LONG_MAX)
            return    
        self._must_be_integer(action["time"], "time")
        self.level_dat_modifications["LastPlayed"]\
            = nbtlib.Long(action["time"])
    
    def _register_remove_paper_garbage(self, action: dict):
        self._remove_datapacks_inner(["bukkit"])
        self.level_dat_removals.append(nbtlib.Path('"Bukkit.Version"'))
        self.files_to_remove.append("paper-world.yml")
    
    def _register_remove_vanilla_garbage(self, action: dict):
        self.files_to_remove += ["session.lock", "uid.dat", "level.dat_old"]
        self.level_dat_removals.append(nbtlib.Path("ServerBrands"))
    
    def _register_remove_fabric_garbage(self, action: dict):
        self.files_to_remove += [
            "data/fabricRegistry.dat",
            "data/fabricRegistry.dat.1",
            "data/fabricRegistry.dat.2"]
        self.datapacks_to_remove .append("fabric")
    
    def _register_set_time(self, action: dict):
        t = action.get("time")
        self._must_be_integer(t, "time")
        if t < 0:
            raise ValueError("time must be between 0 and 23999")
        self.level_dat_modifications["DayTime"] = nbtlib.Int(t)
        if "forever" not in action:
            return
        f = action.get("forever")
        self._must_be_boolean(f, "forever")
        v = "true" if f else "false"
        self._set_gamerules_inner({"doDaylightCycle":v})

    def _register_set_weather(self, action: dict):
        forever = False
        duration = action.get("duration", "forever")
        if isinstance(duration, int) and duration > 0:
            forever = False
            self._set_gamerules_inner({"doWeatherCycle":"true"})
        elif duration == "forever":
            forever = True
            self._set_gamerules_inner({"doWeatherCycle":"false"})
        else:
            raise ValueError("duration must be a positive integer or string literal 'forever'")
        # some explanation of the weather times:
        # the combinatin of raining and trhundering flags dictates the
        # actual weather:
        # - raining:0, thundering:0 -> clear
        # - raining:1, thundering:0 -> rain
        # - raining:1, thundering:1 -> thunder
        # - raining:0, thundering:1 -> clear
        # 
        # observations: 
        # - if clearWeatherTime is 0, rainTime and thunderTime always
        # tick down
        # - if clearWeatherTime is set, raining and thundering flags
        # are cleared, rainTime and thunderTime are set to 1
        # - if raining is set and thundering is not set, thunderTime
        # can still be > 0. When it reaches 0, it is set to a random
        # value and the thundering flag is set.
        self.level_dat_modifications["raining"] = nbtlib.Byte(0)
        self.level_dat_modifications["thundering"] = nbtlib.Byte(0)
        self.level_dat_modifications["rainTime"] = nbtlib.Int(1)
        self.level_dat_modifications["thunderTime"] = nbtlib.Int(1)
        self.level_dat_modifications["clearWeatherTime"] = nbtlib.Int(0)
        weather = action.get("weather")
        if weather not in self.WEATHER_TYPES:
            raise ValueError("weather must be one of 'clear', 'rain' or 'thunder'")
        if weather == "clear":
            self.level_dat_modifications["clearWeatherTime"] \
                = nbtlib.Int(1 if forever else duration)
            return
        self.level_dat_modifications["raining"] = nbtlib.Byte(1)
        if weather == "thunder":
            self.level_dat_modifications["thundering"] = nbtlib.Byte(1)
        if not forever:
            self.level_dat_modifications["thunderTime"] = nbtlib.Int(duration)
            self.level_dat_modifications["rainTime"] = nbtlib.Int(duration)
        
    @classmethod
    def _must_be_type(cls, something: Any, type: Any, fail_str: str | None = None):
        if not isinstance(something, type):
            raise ValueError(fail_str) if fail_str is not None else ValueError()
        
    @classmethod
    def _must_be_string(cls, something: Any, name: str):
        cls._must_be_type(something, str, f"{name} must be a string")

    @classmethod
    def _must_be_list_of_strings(cls, something: Any, name: str):
        cls._must_be_type(something, list, f"{name} must be a list of strings")
        for x in something:
            cls._must_be_type(x, str, f"{name} must be a list of strings")
    
    @classmethod
    def _must_be_integer(cls, something: Any, name: str):
        cls._must_be_type(something, int, f"{name} must be an integer")
    
    @classmethod
    def _must_be_boolean(cls, something: Any, name: str):
        cls._must_be_type(something, bool, f"{name} must be a boolean")

    def _remove_datapacks_inner(self, names):
        self.datapacks_to_remove += ["file/" + n for n in names]
        self.files_to_remove += ["datapacks/" + n for n in names]
    
    def _set_gamerules_inner(self, gamerules):
        gamerules_as_nbt_strings = dict(
            map(lambda it: (it[0], nbtlib.String(it[1])),
            gamerules.items()))
        if "GameRules" not in self.level_dat_modifications:
            self.level_dat_modifications["GameRules"] = gamerules_as_nbt_strings
        else:
            self.level_dat_modifications["GameRules"] |= gamerules_as_nbt_strings

    def _str_or_int_to_int(self, value: str | int, choices: Dict[str, int], name: str | None = None) -> int:
        """turns given value to its corresponding numeric value from a given
        list"""
        if isinstance(value, int):
            if value in choices.values():
                return value
            raise ValueError(
                "unexpected numeric value: %d" % value if name is None
                else "unexpected numeric value of '%s': %d" % (name, value))
        elif isinstance(value, str):
            if value in choices.keys():
                return choices[value]
            raise ValueError(
                "unexpected string value: %s" % value if name is None
                else "unexpected string value of '%s': %s" % (name, value))
        raise ValueError(
            "expected a number or string but found %s" % value if name is None
            else "'%s' should be a number or string but found %s" % (name, value))

def _general_remove(path: PathLike):
    """delete the file or directory pointed to by path"""
    if not path.is_dir():
        path.unlink(missing_ok=True)
    else:
        shutil.rmtree(path)


def _first_not_none(*stuff):
    for s in stuff:
        if s is not None:
            return s


def convert(registry: Registry, world: PathLike,
            output_directory: PathLike, temp_directory: PathLike,
            clean: bool):
    original_world = pl.Path(world)
    output_directory = pl.Path(output_directory)
    tempdir = pl.Path(temp_directory, str(time.time_ns()))

    NEW_WORLD_DIRECTORY_NAME = _first_not_none(
        registry.world_folder_name, original_world.name)

    logging.debug("original world: '%s'" % original_world)
    logging.debug("output dir: '%s'" % output_directory)
    logging.debug("temp dir: '%s'" % tempdir)

    # step 1: copy to temp directory
    WORKING_WORLD = tempdir / NEW_WORLD_DIRECTORY_NAME
    logging.debug("working world: '%s'" % str(WORKING_WORLD))
    WORKING_WORLD.parent.mkdir(parents=True, exist_ok=True)
    if WORKING_WORLD.exists():
        _general_remove(WORKING_WORLD)
    shutil.copytree(original_world, WORKING_WORLD, symlinks=True)
    logging.info("copied world '%s' to directory '%s', working world is '%s'" % (original_world, tempdir, WORKING_WORLD))

    # step 2: removing player scores
    scoreboard_path = WORKING_WORLD / "data" / "scoreboard.dat"
    if scoreboard_path.is_file() and registry.reset_scores_of_players != []:
        with nbtlib.load(WORKING_WORLD / "data" / "scoreboard.dat") as scoreboard:
            for player in registry.reset_scores_of_players:
                logging.info("removing scores of player '%s'" % player)
                del scoreboard[nbtlib.Path('"".data.PlayerScores[{Name:"%s"}]' % player)]

    # step 3 and 4: remove things from level.dat, then apply modifications
    with nbtlib.load(WORKING_WORLD / "level.dat") as level_dat:
        data = nbtlib.Path('"".Data')
        
        # step 3: deletions
        for item in registry.level_dat_removals:
            del level_dat[data + item]
            logging.info("deleted '%s' from level.dat" % str(item))

        # step 4: modifications
        level_dat[data].merge(registry.level_dat_modifications)
        logging.info("applied modifications to level.dat")
        level_dat[data + nbtlib.Path("LevelName")] = nbtlib.String(registry.world_name)
        logging.info("changed world name in level.dat")

        yeeting_packs = registry.datapacks_to_remove
        yeeting_pack_indices = {
            "Enabled":[],
            "Disabled":[]
        }
        for state in ["Enabled", "Disabled"]:
            for i, pack_name in enumerate(level_dat[data + nbtlib.Path('DataPacks.%s' % state)]):
                if pack_name in yeeting_packs:
                    logging.info("datapack '%s' will be removed from level.dat, it was %s"
                              % (pack_name, state))
                    yeeting_pack_indices[state].append(i)
            for index in reversed(yeeting_pack_indices[state]):
                del level_dat[data + nbtlib.Path('DataPacks.%s[%d]' % (state, index))]

    # step 5: remove unwanted files and directories
    for d in registry.files_to_remove:
        _general_remove(WORKING_WORLD / d)
        logging.info("deleted %s" % d)

    # step 6: move result to output directory
    output_directory.mkdir(parents=True, exist_ok=True)
    if registry.should_zip:
        for path in map(lambda x: pl.Path(x), registry.additional_files):
            if path.is_dir():
                shutil.copytree(path, tempdir / path.name, dirs_exist_ok=True)
            elif path.is_file():
                shutil.copy2(path, tempdir)
            elif path.exists():
                logging.warn("only files or directories can be added to archive, skipping `%s`" % path)
            else:
                logging.error("cannot add `%s` to archive, not found" % path)

        archive_name = _first_not_none(registry.archive_name, NEW_WORLD_DIRECTORY_NAME)
        archive_path = output_directory / (archive_name + ".zip")
        _general_remove(pl.Path(archive_path))
        shutil.make_archive(
            (output_directory/archive_name).as_posix(), "zip",
            tempdir, ".")
        logging.info("zipped working world at '%s', archive is '%s'"
                    % (WORKING_WORLD, archive_path))
    else:
        # move working world to output dir
        shutil.copytree(WORKING_WORLD, output_directory / NEW_WORLD_DIRECTORY_NAME, symlinks=True)
        logging.info("copied working world '%s' to output dir, result is '%s'"
                    % (WORKING_WORLD, output_directory/NEW_WORLD_DIRECTORY_NAME))
    
    if clean:
        _general_remove(tempdir)
        logging.info("deleted temporary directory at '%s'" % tempdir)
        

def extract_config(raw_config: dict) -> dict:
    """Extracts only relevant fields from configuration.
    Also verifies that all required fields are present."""
    config = {}
    for f, t in zip(["world", "output_directory", "actions"], [str, str, list]):
        field = raw_config.get(f)
        if field is None or not isinstance(field, t):
            raise ValueError(f"config field {f} is missing or of invalid type")
        config[f] = field
    for i, thing in enumerate(config["actions"]):
        if isinstance(thing, dict):
            if not "type" in thing:
                raise ValueError("found action without a type")
        if isinstance(thing, str):
            config["actions"][i] = {"type": thing}
    return config


if __name__ == "__main__":
    argument_parser = ap.ArgumentParser(
        description="A data-driven tool for getting Minecraft maps ready for release.")
    argument_parser.add_argument(
        "--json", action="store", type=str, required=True,
        metavar="<path/to/config.json>",
        help="use this configuration file in json format")
    argument_parser.add_argument(
        "-c", "--clean", action="store_true",
        help="delete working copy after result is produced")
    argument_parser.add_argument(
        "-q", "--quiet", action="count", default=0,
        help="do not print information other than errors to console."
        +" If given twice, do not print anything.")
    args = argument_parser.parse_args()
    
    match args.quiet:
        case 0: loglevel = logging.INFO
        case 1: loglevel = logging.ERROR
        case _: loglevel = 1000
    logging.basicConfig(format="%(levelname)s:%(message)s", level=loglevel)

    logging.info("reading configuration from file '%s'" % str(args.json))
    with open(args.json, "r", encoding="utf-8") as conf_file:
        raw_config = json.load(conf_file)
    config = extract_config(raw_config)

    reg = Registry()
    for action in config["actions"]:
        reg.register_action(action)

    convert(reg, config["world"], config["output_directory"], ".mid",
            args.clean)
