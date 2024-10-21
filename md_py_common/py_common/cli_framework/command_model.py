from typing import List, Callable

import pydantic


class CommandModel(pydantic.BaseModel):
	commands: List[str]
	description: str
	action: Callable
