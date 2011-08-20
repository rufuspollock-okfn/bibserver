import json
def load_config(path):
    fileobj = open(path)
    c = ""
    for line in fileobj:
        if line.strip().startswith("#"):
            continue
        else:
            c += line
    out = json.loads(c)
    return out

# TODO: make this less hacky and more configurable
config = load_config('config.json')

__all__ = ['config']

