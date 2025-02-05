
def print_message(message: str = None) -> str:
    if message:
        print(message)
        return message


function = print_message
function_spec = {
    "type": "function",
    "function": {
        "name": "print_message",
        "description": "Print's a message into the dev console. Only use when requested to use.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "A message to print"}
            },
            "required": ["message"],
        },
    },
}
