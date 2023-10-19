# map-is-done
*Data-driven tool for publishing Minecraft: Java Edition maps.*

This tool is inteneded for people who make custom maps (worlds) for
Minecraft, the popular video game. When the map is done, there is still 
unpleasant work left to do, that is having to manually remove various files
from the world directory, modify NBT files (such as `level.dat`), and more.
The purpose of this tool is to automate as much as possible of that process,
notably
- removing the unnecessary `level.dat_old` file,
- removing player data,
- changing several properties in `level.dat`, such as gamerules and
- compressing the resulting world in a zip archive.

Information on what modifications the script should do are passed to it in
a human-readable configuration file in JSON format. That makes it easy for
users to define actions (ie. stuff that should happen to the map) or quickly
review them, and it allows for seamless addition of new functionality.

## Configuration File Format

*Note: map-is-done is in early development so this format may (and will)
change going forward.*

A config file is written in JSON for relative ease of use. An example can
be seen in the file [`example.json`](examples/example.json). The format has
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

Currently, the required fields are `"world"` which is a path to the world
that is to be modified, `"output_directory"` which is a path to a directory
where the result of the modifications is placed, and `"actions"`, a list
of compounds, each describing a modification to the supplied world.

### Actions
Theoretically, the list may contain any number of actions, and may even be
empty. Each action must contain it's type, and possibly more arguments
depending on the type. In the above example, there is one action of type
`"set_map_name"` and additional arguments `"world_name"` and `"folder_name"`.
A list of implemented action types follows:

1. `"set_map_name"`

    Changes the world name in `level.dat` and the name of the world folder.
    Parameters are
    - `"world_name"` - the new world name
    - `"folder_name"` - the new world folder name

2. `"remove_datapacks"`

    Removes specified data packs from the `"datapacks"` subdirectory and from
    `"level.dat"`.
    - `"names"` - list of data pack names to be removed; must be strings

3. `"set_gamerules"`

    Changes values of game rules. Parameters are
    - `"gamerules"` - a compound holding a pair of rule:value for each gamerule
      to change. Both names and values must be strings, however, it is not
      verified, that each name is an existing gamerule, nor is it checked if
      supplied values are appropriate for the gamerule.

4. `"zip"`

    After all changes are done, compress the world in a zip archive and place it
    in the configured output directory. Parameters:
    - `"archive_name"` - name of the resulting archive (withou the .zip extension)

5. `"remove_player_scores"`

    Resets all scoreboard scores of a given player. Parameters:
    - `"player"` - name of the player whose scores should be reset

6. `"remove_player_data"`

    Removes all data from the `playerdata`, `advancements` and `stats`
    subdirectories, and the `Player` element of `level.dat`. The mentioned
    subdirectories are also removed, since they would contain no data.

7. `"set_difficulty"`

    Sets the world difficulty. Parameters:
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
