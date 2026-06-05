from typing import Literal, overload
import json

@overload
def load_from_file(path: str, file_encoding: Literal["json"]) -> list | dict: ...
@overload
def load_from_file(path: str, file_encoding: None = None) -> str: ...

def load_from_file(path: str, file_encoding: str | None = None) -> list | dict | str:
    with open(path, "r", encoding="utf-8") as f:
        if file_encoding and file_encoding == "json":
            return json.load(f)
        return f.read()