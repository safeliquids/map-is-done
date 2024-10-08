
# Configuration File Format

A config file is written in JSON for relative ease of use. An example can
be seen in the file [`example.json`](../examples/example.json). The format has
several required and optional fields, all other fields are ignored. See example

```json
{
    "world":"path/to/world/folder",
    "output_directory":"path/to/output/directory/",
    "actions":[
        {
            "type":"set_map_name",
            "world_name":"A Pretty World Name",
            "folder_name":"a_technical_world_folder_name"
        }
    ],
    "extra_stuff":"This and all not-recognized fields are ignored.",
    "extra_extra_stuff":"This and all not-recognized fields are ignored."
}
```

Required fields are ***"world"*** which is a path to the world to be modified,
***"output_directory"*** which is a path to a directory where the result of the
modifications is placed, and ***"actions"***, a list of item named actions.
Each action describes a modification to the supplied world. Actions are 
described in [the following section.](#actions) Also note that, all 
filesystem paths referenced in the config file (eg. ***"world"*** must be
absolute or relative to the directory where the script is run from.)

## Actions
The list may contain any number of actions and may even be empty.
Generally, an action is given as an object containing a mandatory ***"type"***
field and possibly more fields (ie. arguments), which depend on the action
type. In the above example, there is one action of type ***"set_map_name"***
that has additional arguments ***"world_name"*** and ***"folder_name"***.

Some actions can be given without some of their arguments which usually means
a default value is used. Some actions (e.g. ***"explode_last_played"***) have no
parameters at all. This can be written as an object  with only the ***"type"***
field
```json
    "actons":[
        {
            "type":"explode_last_played"
        }
    ]
```
or, equivalently, only the action type
```json
    "actons":[
        "explode_last_played"
    ]
```

## Implemented Action Types

### Naming and packaging

1. ***"set_map_name"***

    Changes the world name in `level.dat` and the name of the world folder.
    
    Parameters:
    - ***"world_name": string*** - the new world name
    - ***"folder_name": string (optional)*** - the new world folder name.
    If omitted, the original world directory name is used.

2. ***"zip"***

    After all changes are done, compress the world in a zip archive and place it
    in the configured output directory.
    
    Parameters:
    - ***"archive_name": string (optional)*** - name of the resulting archive.
    If omitted, the archive is named the same as the world folder. It can be
    given with or without the `.zip` extension.
    - ***"add_files": list of strings (optional)*** - names of files or
    directories that should be added to the archive. All files or directories
    are added to the root of the archive, on the same level as the world
    folder.

3. ***"explode_last_played"***

    Sets the `LastPlayed` property in `level.dat` to a very high number, so that
    the map, when installed in singleplayer, appears at the top of the world list
    before it is loaded for the first time.
    
    Parameters:
    - ***"time": integer (optional)*** - exact value to set the
    `LastPlayed` property to. If omitted, the value 
    `LONG_MAX = 9_223_372_036_854_775_807` is used.

### Cleanup
    
4. ***"remove_datapacks"***

    Removes specified data packs from the `datapacks` subdirectory and from
    `level.dat`.

    Parameters:
    - ***"names": list of strings*** - names of data packs to be removed

5. ***"remove_player_scores"***

    Resets all scoreboard scores of given players.
    
    Parameters:
    - ***"players": list of strings*** - names of the players whose scores
    should be reset

6. ***"remove_player_data"***

    Removes all data from the `playerdata`, `advancements` and `stats`
    subdirectories, and the `Player` element of `level.dat`. The mentioned
    subdirectories are also removed, since they would contain no data.

    Known Issue: In Minecraft versions 1.20.3 and 1.20.4, if the `Player` property in `level.dat` in a singleplayer world is missing, it gets initialized to some default values. This means that, when opening the world the first time, the player will spawn at 0 0 0 (i.e. not at the world spawn.) This no longer happens in versions 1.20.5 and newer.

7. ***"remove_paper_garbage"***

    Performs various cleanup of information that Paper uses but is irrelevant
    to the finished map. That includes
    - `paper-world.yml`
    - datapack `file/bukkit`
    - remove `BukkitVersion` field in `level.dat`

8. ***"remove_vanilla_garbage"***

    Performs various cleanup of information normally present in the world, but
    that are irrelevant to the finished map. That includes
    - `level.dat_old`, `session.lock`, `uid.dat` files
    - `ServerBrands` field in `level.dat`

9. ***"remove_fabric_garbage"***

    Performs various cleanup of information that Fabric uses but is irrelevant
    to the finished map. That includes
    - `data/fabricRegistry.dat`, `data/fabricRegistry.dat.1`,
    `data/fabricRegistry.dat.2` files
    - remove the `fabric` datapack

### Technical changes

10. ***"set_default_gamemode"***

    Sets the default gamemode in `level.dat`. Newly joining players will spawn
    in this gamemode.

    Parameters:
    - ***"gamemode": string or integer*** - string or numeric representation 
    of the intended gamemode. Allowed values are
        | Numeric | String    |
        |     --: | :--       |
        |       0 | survival  |
        |       1 | creative  |
        |       2 | adventure |
        |       3 | spectator |

11. ***"set_difficulty"***

    Sets the world difficulty.
    
    Parameters:
    - ***"difficulty": string or integer*** - the string or numeric
    representation of the desired difficulty. Allowed values are
        | Numeric | String   |
        |     --: | :--      |
        |       0 | peaceful |
        |       1 | easy     |
        |       2 | normal   |
        |       3 | hard     |

12. ***"set_gamerules"***

    Changes values of game rules. 
    
    Parameters:
    - ***"gamerules": object with string:string pairs*** - a compound holding
    a rule:value pair for each gamerule to change. Both names and values must
    be strings, however, it is not verified, that each name is an existing
    gamerule, nor is it checked if supplied values are appropriate for the
    gamerule.

13. ***"set_time"***

    Sets the in-game time of the world, possibly enabling or disabling
    advancing the in-game time (the so-called daylight cycle.) Do note, this
    is done by setting the `doDaylightCycle`
    gamerule. If you also set this gamerule directly using the
    ***"set_gamerules"*** action it is undefined what happens. It is
    recommended to enable or disable the daylight cycle using ***"set_time"***
    aciton.

    Parameters:
    - ***"time": integer*** - in-game time of day in ticks. Must be between
    0 and 23999, where 6000 is noon, 18000 is midnight.
    - ***"forever: boolean (optional)"*** - If true, disables the daylight
    cycle. If false, forcefully enables it. If omitted, the daylight cycle is
    left unchanged.

14. ***"set_weather"***

    Sets the world's weather, optionally forever or with a timer.
    Naturally changing the weather (so-called weather cycle) is governed by
    the `doWeatherCycle` gamerule. Setting the duration in this action changes
    that gamerule. If you also set this gamerule directly using
    the ***"set_gamerules"*** action it is undefined what happens, therefore
    it is once again recommended to enable or disable the weather cycle using
    ***"set_weater"*** aciton.

    Parameters:
    - ***"weather": string*** - weather type. must be one of `"clear"`,
    `"rain"` or `"thunder"`
    - ***"duration": integer or string literal (optional)*** - number
    of ticks this weather should remain for, or `"forever"`, which stops the
    weather cycle. Default is ***"forever"***. If a number is given, it must
    be positive.
