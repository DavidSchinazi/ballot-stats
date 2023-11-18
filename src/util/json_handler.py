import json


def save_json(obj, file_path):
    with open(file_path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True, default=str)
