
def say_hello(name: str, message: str = None) -> str:
    if message:
        print(message)
        return message
    else:
        print(f"Hello, {name}!")
        return f"Hello, {name}!"


function = say_hello
function_spec = {
    "type": "function",
    "function": {
        "name": "say_hello",
        "description": "Says hello to someone, the returned value is the message that was sent. Alternatively sends a custom message to someone when one is specified",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The person's name"},
                "message": {"type": "string", "description": "A custom message to send to the person"}
            },
            "required": ["name"],
        },
    },
}
