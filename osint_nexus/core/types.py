from __future__ import annotations

# JSON types that allow recursive structures
type JSONValue = str | int | float | bool | None | dict[str, JSONValue] | list[JSONValue]
type JSONObject = dict[str, JSONValue]
type JSONList = list[JSONValue]

# Metadata dictionary for general usage
type MetadataDict = dict[str, JSONValue]
