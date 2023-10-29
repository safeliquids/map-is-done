# map-is-done
*Data-driven tool for publishing Minecraft: Java Edition maps.*

This tool is inteneded for people who make custom maps (worlds) for
Minecraft: Java Edition. When the map is done, there is still 
unpleasant work left to do, that is having to manually remove various files
from the world directory, modify NBT files (such as `level.dat`), and more.
The purpose of this tool is to automate as much as possible of that process,
notably
- removing the unnecessary `level.dat_old` file,
- removing player data,
- changing several properties in `level.dat`, such as gamerules and
- compressing the resulting world in a zip archive.

Worlds in version 1.16 or newer *should* be compatible, older ones might run into
issues. Always keep backups of your maps!

## Setup
`map-is-done` requires python 3.10 or higher. It also depends on `nbtlib` and
`numpy`. You can install these dependencies using pip
```console
> pip install -r requirements.txt
```

## Running the Script
Run the script from the command line like so
```console
> python mid.py --json path/to/config/file.json
```

When given a world, the script first copies it to a temporary directory and
does all modifications in that copy. The temporary directory is named
`.mid/<timestamp>` and is created inside the current working directory,
resulting in a structure such as
```
./
|- .mid
|  |- 1698233982531529800/
|     |- my_world/
|        |- level.dat
|        |- region/
|        |- icon.png
|        |  ...
|  ...
```
When given the `--clean` or `-c` flag, the working world is deleted after the
result is produced.

## Config file format
Information on what modifications the script should do are passed to it in
a human-readable configuration file in JSON format. That makes it easy for
users to define actions (ie. stuff that should happen to the map) or quickly
review them, and it allows for seamless addition of new functionality.
A detailed description of the format can be found [here](docs/config_file_format.md).
