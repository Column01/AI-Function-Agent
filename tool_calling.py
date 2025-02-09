import glob
import inspect
import json
import os
from datetime import datetime
from importlib import util
from typing import Callable, Tuple, List, Dict

from qwen_agent.llm import get_chat_model


def confirm_input(prompt: str = "Confirm? (y/n): ") -> bool:
    test = input(prompt)
    return test.lower() == "y"


def glob_import(glob_str: str) -> Tuple[List[dict], Dict]:
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
            if isinstance(fn, list):
                for fnc in fn:
                    fn_name = fnc.__name__
                    functions[fn_name] = fnc
            else:
                fn_name = fn.__name__
                functions[fn_name] = fn
        if getattr(module, "function_spec"):
            func_spec = getattr(module, "function_spec")
            if isinstance(func_spec, list):
                function_spec.extend(func_spec)
            else:
                function_spec.append(func_spec)

    return functions, function_spec


def load_user_funcs():
    global system_function_library, function_library, functions
    print("Loading user functions...")
    user_function_library, USER_TOOLS = glob_import("functions/user/*.py")
    # For Qwen-Agent library, extracts actual functions from the tools dicts
    user_functions = [tool["function"] for tool in USER_TOOLS]
    function_library = system_function_library | user_function_library
    functions.extend(user_functions)
    print("User functions loaded!")


# Load the user's config file
with open("config.json", "r") as fp:
    config = json.load(fp)

# Import all system functions
system_function_library, TOOLS = glob_import("functions/system/*.py")
function_library = system_function_library

# For Qwen-Agent library, extracts actual functions from the tools dicts
functions = [tool["function"] for tool in TOOLS]

if config.get("load_user_funcs"):
    load_user_funcs()


def print_assistant_messages(responses: list):
    printable = [
        resp["content"]
        for resp in responses
        if resp["role"] == "assistant" and resp["content"] != ""
    ]
    print("\n".join(printable))


def is_valid_func_call(fn_name: str, fn_args: dict) -> bool:
    # Checks if the function exists
    fnc = get_actual_function(fn_name)
    if not fnc:
        return False
    params = inspect.signature(fnc).parameters
    fnc_args = params.keys()
    model_args = fn_args.keys()

    # Check for extra arguments we aren't expecting
    extra = [arg for arg in model_args if arg not in fnc_args]
    if len(extra) != 0:
        return False

    # See if any arguments are missing
    missing = fnc_args - model_args
    # No args are missing
    if len(missing) == 0:
        # Check that the keys match
        return list(params.keys()) == list(fn_args.keys())
    # Check if the "missing" parameters have no default value
    for key in missing:
        param = params.get(key)
        if param.default == inspect.Parameter.empty:
            return False
    return True


def print_func_calls(responses: list):
    print("\nFunctions to call (invalid functions will be ignored!): ")

    for response in responses:
        fn_call = response.get("function_call", None)
        if fn_call:
            name = fn_call["name"]
            args = json.loads(fn_call["arguments"])
            print(f"\n{name}")
            print(f"    Args: {args}")
            print(f"    Valid: {("Y" if is_valid_func_call(name, args) else "N")}")
    print("\n")


def has_func_calls(responses: list) -> bool:
    calls = [response for response in responses if response.get("function_call")]
    return len(calls) > 0


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
                if is_valid_func_call(fn_name, fn_args):
                    fn_res = fnc(**fn_args)
                    if fn_res:
                        messages.append(
                            {"role": "function", "name": fn_name, "content": fn_res}
                        )
                else:
                    messages.append(
                        {
                            "role": "function",
                            "name": fn_name,
                            "content": "This function either does not exist, or the parameters provided were invalid.",
                        }
                    )
    return messages


def print_help():
    print("help")
    print("    Shows this text")
    print("exit (or quit)")
    print("    Exits the program")
    print("clear")
    print("    Clears the console and the chat history for a new convo")
    print("load")
    print(
        "    Load's the functions in the user folder. (can be enabled by default in the config)"
    )


def main():
    llm = get_chat_model(
        {
            "model": config["model_name"],
            "model_server": config["api_url"],
            "api_key": config["api_key"],
        }
    )

    system_prompt = inspect.cleandoc(f"""
                    You are JARVIS, a helpful and witty assistant. 
                    You help a user with their tasks by using any of the functions available to you and your replies should always aim to be short but informative.
                    When a user refers to themselves in a prompt to create or recall a memory in the first person, change it to refer to 'The User'.
                    If you cannot answer a prompt based on information you have available, use your tools to find more information.
                    The current date is {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}
                    """)

    system_message = {
        "role": "system",
        "content": system_prompt,
    }

    print("Type 'help' for chat commands")

    messages = []
    messages.append(system_message)
    running = True
    while running:
        try:
            # Ask for the prompt
            prompt = input("Prompt: ")
            # If no prompt is provided, skip this loop and ask for a new one
            if not prompt:
                print("You have to say something for this to work...")
                continue

            if prompt == "help":
                print_help()
                continue
            if prompt == "clear":
                # clears the chat history and terminal
                messages.clear()
                messages.append(system_message)
                os.system("cls" if os.name == "nt" else "clear")
                continue
            if prompt == "load":
                load_user_funcs()
                continue
            if prompt in ("exit", "quit"):
                exit("Exiting...")

            # Add the prompt to the context
            messages.append({"role": "user", "content": prompt})

            print("Prompting the backend for function calls...")

            finished = False
            while not finished:
                # Do initial inference to let the AI select function calls
                for responses in llm.chat(
                    messages=messages,
                    functions=functions,
                    extra_generate_cfg=dict(parallel_function_calls=True),
                ):
                    pass

                # Add AI response/function call requests to context
                messages.extend(responses)
                print_assistant_messages(responses)
                # If there are no function calls, this will break the loop after this conversation turn
                if not has_func_calls(responses):
                    finished = True
                else:
                    # Print all function calls the model is requesting
                    print_func_calls(responses)
                    # Execute functions and add their responses to the context
                    func_responses = execute_functions(responses)
                    messages.extend(func_responses)

        except KeyboardInterrupt:
            # print(json.dumps(messages, indent=2))
            exit("Exiting...")


if __name__ == "__main__":
    main()
