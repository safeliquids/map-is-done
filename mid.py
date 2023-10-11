import json


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

