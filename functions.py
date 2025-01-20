import json

from typing import Callable


# Define a simple function
def say_hello(name: str, message: str = None) -> str:
    if message:
        print(message)
        return message
    else:
        print(f"Hello, {name}!")
        return f"Hello, {name}!"


# Define a simple function
def ask_age(name: str) -> str:
    return input(f"How old are you, {name}?: ")


# Library of the usable functions
function_library = {
    "say_hello": say_hello,
    "ask_age": ask_age
}


def confirm_input(prompt: str = "Confirm? (y/n): ") -> bool:
    test = input(prompt)
    return test.lower() == "y"


TOOLS = [
    {
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
    },

    {
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
        },
    }
]

# For Qwen-Agent library, extracts actual functions from the tools
functions = [tool["function"] for tool in TOOLS]


def print_func_calls(func_calls: list):
    print("\nFunctions to call (invalid functions will be ignored!): ")
    functions = function_library.keys()
    for func_call in func_calls:
        fn_call = func_call.get("function_call", None)
        if fn_call:
            name = fn_call["name"]
            print(f"\n{name}")
            print(f"    Args: {fn_call["arguments"]}")
            print(f"    Valid: {("Y" if name in functions else "N")}")
    print("\n")


def get_actual_function(func_name: str) -> Callable | None:
    return function_library.get(func_name)


def execute_functions(responses: list) -> list:
    messages = []
    print("Executing functions...\n")
    for response in responses:
        fn_call = response.get("function_call", None)
        if fn_call:
            fn_name = fn_call['name']
            fn_args = json.loads(fn_call["arguments"])
            fnc = get_actual_function(fn_name)
            if fnc:
                fn_res = fnc(**fn_args)

                if fn_res:
                    messages.append({
                        "role": "function",
                        "name": fn_name,
                        "content": fn_res
                    })
    print("\n")
    return messages
