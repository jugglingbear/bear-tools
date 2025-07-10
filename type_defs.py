from typing import TypeAlias

from jsonalias import Json

JsonDict: TypeAlias = dict[str, Json]
JsonList: TypeAlias = list[JsonDict]
