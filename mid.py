import json

class Registry:
    """registers actions and verifies, if they are supported"""
    supported_actions = [
        "set_map_name",
        "remove_datapacks",
        "zip",
        "set_gamerules"
    ]


    def supports(self, action_type: str) -> bool:
        return action_type in self.supported_actions


    def register(self, action: dict):
        """registers an action in json format
        raises ValueError if the action type is unsupported or the action
        definition is invalid.
        
        In general, additional fields of the action definitioin (and, by
        extention, the validity of a given action definition,) depend on the
        actino type."""
        action_type = action["type"]
        match action_type:
            case "set_map_name":
                world_name = action.get("world_name")
                folder_name = action.get("folder_name")
                if not isinstance(world_name, str)\
                        or not isinstance (folder_name, str):
                    raise ValueError(f"malformed action definition")
            
            case "remove_datapacks":
                names = action.get("names")
                if not isinstance(names, list):
                    raise ValueError(f"malformed action definition")
                if not all(map(lambda n: isinstance(n, str), names)):
                    raise ValueError(f"malformed action definition")

            case "zip":
                archive_name = action.get("archive_name")
                if not isinstance(archive_name, str):
                    raise ValueError(f"malformed action definition")
            
            case "set_gamerules":
                gamerules = action.get("gamerules")
                if not isinstance(gamerules, dict):
                    raise ValueError(f"malformed action definition")
                for rule, value in gamerules.items():
                    if not isinstance(rule, str) or not isinstance(value, str):
                        raise ValueError(f"malformed action definition")
                    
            case _:
                raise ValueError(f"action type `{action_type}' is not supported!")
            
        print(f"registered action of type `{action_type}'")


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
    with open("example.json", "r", encoding="utf-8") as conf_file:
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
    
