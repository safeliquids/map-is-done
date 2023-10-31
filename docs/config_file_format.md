
# Configuration File Format

A config file is written in JSON for relative ease of use. An example can
be seen in the file [`example.json`](../examples/example.json). The format has
several required and optional fields, all other fields are ignored. See example

```json
{
    "world":"path/to/world/folder",
    "output_directory":"path/to/output/directory/",
    "actions":{
        "set_map_name":{
            "world_name":"A Pretty World Name",
            "folder_name":"a_technical_world_folder_name"
        }
    }
    "extra_stuff":"This and all not-recognized fields are ignored.",
    "extra_extra_stuff":"This and all not-recognized fields are ignored."
}
```

Required fields are `"world"` which is a path to the world to be modified,
`"output_directory"` which is a path to a directory where the result of the
modifications is placed, and `"actions"`, an object of action definitions.
Actions describe modifiactions to the supplied world. All referenced filesystem
paths should be absolute or relative to the current working directory (where
the script is run from.)

## Actions
It depends on the action what the value should be. In the example above,
there is one action of type `set_world_name` where the value is an object
containing two strings `"world_name"` and `"folder_name"`.

A list of implemented action types follows:
1. `"set_map_name"`

    Changes the world name in `level.dat` and the name of the world folder.
    The value must be an object containing these keys:
    - `"world_name"` - the new world name
    - `"folder_name"` - the new world folder name

2. `"remove_datapacks"`

    Removes specified data packs from the `"datapacks"` subdirectory and from
    `"level.dat"`. The value must be a list of datapack names.

3. `"set_gamerules"`

    Changes values of game rules. The value must be an object containing
    key-value pairs where each key is the name of a gamerule and it's
    corresponding value is the new value of that gameruld. 
    Both names and values must be strings, however, it is not
    verified, that each name is an existing gamerule, nor is it checked if
    supplied values are appropriate for the gamerule.

4. `"zip"`

    After all changes are done, compress the world in a zip archive and place it
    in the configured output directory. The value must be an object containing
    these keys:
    - `"archive_name"` - name of the resulting archive (*without* the .zip extension)

5. `"remove_player_scores"`

    Resets all scoreboard scores of given players. The value must be a list of
    player names (or, more generally, scoreholder names.)

6. `"remove_player_data"`

    Removes all data from the `playerdata`, `advancements` and `stats`
    subdirectories, and the `Player` element of `level.dat`. The mentioned
    subdirectories are also removed, since they would contain no data.
    The value must be a boolean value. Player data is only removed if the value
    is `true`.

7. `"set_difficulty"`

    Sets the world difficulty. The value is either a string or a numeric
    representation of the difficulty, see table below.
      | Numeric | String   |
      |     --: | :--      |
      |       0 | peaceful |
      |       1 | easy     |
      |       2 | normal   |
      |       3 | hard     |

8. `"set_default_gamemode"`

    Sets the default gamemode in `level.dat`. Newly joining players will spawn
    in this gamemode. The value is either a string or a numeric representation
    of the gamemode, see table below.
      | Numeric | String    |
      |     --: | :--       |
      |       0 | survival  |
      |       1 | creative  |
      |       2 | adventure |
      |       3 | spectator |

9. `"explode_last_played"`

    Sets the `LastPlayed` property in `level.dat` to a very high number, so that
    the map, when installed in singleplayer, appears at the top of the world list
    before it is loaded for the first time. The value must be boolean. The change
    is only done if the value is `true`.

10. `"remove_garbage"`
    Deletes various "garbage" files and other objects from the map. The value
    must be an object, where keys are `"vanilla"` or `"paper"` and values are
    booleans. Corresponding cleanups are:
    - if `"vanilla"` is `true`, removes
        - `level.dat_old`, `session.lock`, `uid.dat` files
        - `ServerBrands` field in `level.dat`
    - if `"paper"` is `true`, removes
        - `paper-world.yml`
        - datapack `file/bukkit`
        - remove `BukkitVersion` field in `level.dat`
