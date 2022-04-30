import json


def load_json_object(path):
    with open(path, 'r') as fp:
        json_object = json.load(fp)
    return json_object


def save_json_object(json_object, path):
    with open(path, 'w') as fp:
        json.dump(json_object, fp, indent=2)