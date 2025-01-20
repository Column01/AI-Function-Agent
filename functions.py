import glob
import json
import os
from importlib import util
from typing import Callable


def confirm_input(prompt: str = "Confirm? (y/n): ") -> bool:
    test = input(prompt)
    return test.lower() == "y"


def glob_import(glob_str: str):
    function_spec: list = []
    functions: dict = {}
    gui_file_paths = glob.glob(glob_str)

    for file_path in gui_file_paths:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = util.spec_from_file_location(module_name, file_path)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if getattr(module, "function"):
            fn = getattr(module, "function")
            fn_name = fn.__name__
            functions[fn_name] = fn
        if getattr(module, "function_spec"):
            function_spec.append(getattr(module, "function_spec"))

    return functions, function_spec


func_specs = []

# Import all functions and obtain their defined specs
function_library, TOOLS = glob_import("functions/*.py")

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
            fn_name = fn_call["name"]
            fn_args = json.loads(fn_call["arguments"])
            fnc = get_actual_function(fn_name)
            if fnc:
                fn_res = fnc(**fn_args)

                if fn_res:
                    messages.append(
                        {"role": "function", "name": fn_name, "content": fn_res}
                    )
    print("\n")
    return messages
