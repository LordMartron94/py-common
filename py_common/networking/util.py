import json


def encode_message_to_bytes(message_json: dict, end_of_message_token: str = "<eom>") -> bytes:
    message = message_json.copy()
    message = json.dumps(message)
    message += end_of_message_token
    byte_buffer = bytes(message, encoding='utf-8')
    return byte_buffer
