
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

Required fields are `"world"` which is a path to the world to be modified,
`"output_directory"` which is a path to a directory where the result of the
modifications is placed, and `"actions"`, a list of item named actions.
Each action describes a modification to the supplied world. Actions are 
described in [the following section.](#actions) Also note that, all 
filesystem paths referenced in the config file (eg. `"world"` must be
absolute or relative to the directory where the script is run from.)


Generally, an action is given as an object containing a mandatory `"type"` field and possibly more fields, which depend on the action type.

## Actions
The list may contain any number of actions, and may even be empty.
Generally, an action is given as an object containing a mandatory `"type"`
field and possibly more fields (ie. arguments), which depend on the action
type. In the above example, there is one action of type `"set_map_name"`
and additional arguments `"world_name"` and `"folder_name"`.

Some actions can be given without some of their arguments, which usually means
a default value is used. Some actions (eg. `"explode_last_played"`) have no
parameters at all. This can be written as an object  with only the `"type"`
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

### List of Action Types
1. `"set_map_name"`

    Changes the world name in `level.dat` and the name of the world folder.
    
    Parameters:
    - `"world_name"` - the new world name
    - `"folder_name"` (optionnal) - the new world folder name; if omitted,
    the original world directory name is used.
    
2. `"remove_datapacks"`

    Removes specified data packs from the `"datapacks"` subdirectory and from
    `"level.dat"`.

    Parameters:
    - `"names"` - list of data pack names to be removed; must be strings

3. `"set_gamerules"`

    Changes values of game rules. 
    
    Parameters:
    - `"gamerules"` - a compound holding a pair of rule:value for each gamerule
      to change. Both names and values must be strings, however, it is not
      verified, that each name is an existing gamerule, nor is it checked if
      supplied values are appropriate for the gamerule.

4. `"zip"`

    After all changes are done, compress the world in a zip archive and place it
    in the configured output directory.
    
    Parameters:
    - `"archive_name"` (optional) - name of the resulting archive (*without*
    the .zip extension); if omitted, the archive is named the same as the world
    folder.
    - `"add_files"` (optional) - list of names of files or directories, that
    should be added to the archive. All files or directories are added to the
    root of the archive, on the same level as the world folder.

5. `"remove_player_scores"`

    Resets all scoreboard scores of given players.
    
    Parameters:
    - `"players"` - list of names of the players whose scores should be reset

6. `"remove_player_data"`

    Removes all data from the `playerdata`, `advancements` and `stats`
    subdirectories, and the `Player` element of `level.dat`. The mentioned
    subdirectories are also removed, since they would contain no data.

7. `"set_difficulty"`

    Sets the world difficulty.
    
    Parameters:
    - `"difficulty"` - the numeric or string representation of the desired
      difficulty. Allowed values are in a table below
      | Numeric | String   |
      |     --: | :--      |
      |       0 | peaceful |
      |       1 | easy     |
      |       2 | normal   |
      |       3 | hard     |

8. `"set_default_gamemode"`

    Sets the default gamemode in `level.dat`. Newly joining players will spawn
    in this gamemode.

    Parameters:
    - `"gamemode"` - the intended gamemode. Similar to difficulty, it can be a numeric
      or string representation. Allowed values are
      | Numeric | String    |
      |     --: | :--       |
      |       0 | survival  |
      |       1 | creative  |
      |       2 | adventure |
      |       3 | spectator |

9. `"explode_last_played"`

    Sets the `LastPlayed` property in `level.dat` to a very high number, so that
    the map, when installed in singleplayer, appears at the top of the world list
    before it is loaded for the first time.
    
    Parameters:
    - `"time"` (optional) - exact value to set the `"LastPlayed"` property to.
    Must be an integer. If omitted, `LONG_MAX` is used.

10. `"remove_paper_garbage"`

    Performs various cleanup of information that Paper uses but is irrelevant
    to the finished map. That includes
    - `paper-world.yml`
    - datapack `file/bukkit`
    - remove `BukkitVersion` field in `level.dat`

11. `"remove_vanilla_garbage"`

    Performs various cleanup of information normally present in the world, but
    that are irrelevant to the finished map. That includes
    - `level.dat_old`, `session.lock`, `uid.dat` files
    - `ServerBrands` field in `level.dat`

12. `"remove_fabric_garbage"`

    Performs various cleanup of information that Fabric uses but is irrelevant
    to the finished map. That includes
    - `data/fabricRegistry.dat`, `data/fabricRegistry.dat.1`, `data/fabricRegistry.dat.2` files
    - remove the `fabric` datapack
