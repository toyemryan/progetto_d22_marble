import json

def load_from_file(path: str, file_encoding: str | None = None):
    with open(path, "r", encoding="utf-8") as f:
        if file_encoding and file_encoding=="json":
            return json.load(f)
        return f.read()