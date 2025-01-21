
def ask_age(name: str) -> str:
    return input(f"How old are you, {name}?: ")


function = ask_age
function_spec = {
    "type": "function",
    "function": {
        "name": "ask_age",
        "description": "Ask someone their age",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The person's name."}
            },
            "required": ["name"],
        },
    }
}
