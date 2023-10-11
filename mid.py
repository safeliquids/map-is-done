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


if __name__ == "__main__":
    config = {}
    properties = {
        "actions":{"required":True, "found":False},
        "description":{"required":False, "found":False}
    }
    with open("example.json", "r", encoding="utf-8") as conf_file:
        raw_config = json.load(conf_file)
    
    for k, v in raw_config.items():
        if k not in properties:
            print(f"found unknown property `{k}', ignoring.")
            continue
        
        property_info = properties[k]
        if property_info["found"]:
            print(f"property `{k}' was given multiple times. stopping.")
            exit(-1)

        if property_info["required"]:
            print(f"found required property `{k}' in file")
        else:
            print(f"found optional property `{k}' in file")
        
        config[k] = v
        property_info["found"] = True
    
    for name, info in properties.items():
        if info["required"] and name not in config:
            print(f"missing required property `{name}'. stopping")
            exit(-1)
    
    print("resulting config:")
    print(json.dumps(config))
    print("=" * 40)

    reg = Registry()
    for action in config["actions"]:
        reg.register(action)
    
