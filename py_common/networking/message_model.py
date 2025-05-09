from datetime import datetime
from typing import Optional
from uuid import uuid4

import pydantic
from pydantic import Field

from .message_payload import MessagePayload

class MessageModel(pydantic.BaseModel):
	payload: MessagePayload
	sender_id: Optional[str] = Field("")
	target_uuid: Optional[str] = Field("")
	unique_id: Optional[str] = Field(str(uuid4()))
	time_sent: Optional[str] = Field(str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z" ))
