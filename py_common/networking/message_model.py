from typing import Optional

import pydantic

from .message_payload import MessagePayload

class MessageModel(pydantic.BaseModel):
	payload: MessagePayload
	target_uuid: Optional[str]
