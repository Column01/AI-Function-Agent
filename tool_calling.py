import glob
import inspect
import json
import os
from datetime import datetime
from importlib import util
from typing import Callable

from openai import OpenAI
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)

# Load the user's config file
with open("config.json", "r") as fp:
    config = json.load(fp)

# Set up OpenAI API client
client = OpenAI(base_url=config.get("api_url"), api_key=config.get("api_key"))


def glob_import(glob_str: str) -> tuple[list[dict], dict]:
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
    function_library = system_function_library | user_function_library
    functions.extend(USER_TOOLS)
    print("User functions loaded!")


# Import all system functions
system_function_library, TOOLS = glob_import("functions/system/*.py")
function_library = system_function_library

functions = []
functions.extend(TOOLS)

if config.get("load_user_funcs"):
    load_user_funcs()


def is_valid_tool_call(tool_call: ChatCompletionMessageToolCall) -> bool:
    fn_name = tool_call.function.name
    fn_args = json.loads(tool_call.function.arguments)
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


def print_func_calls(choice: Choice):
    print("\nFunctions to call (invalid functions will be ignored!): ")
    tool_calls = choice.message.tool_calls
    for tool_call in tool_calls:
        print(f"\n{tool_call.function.name}")
        print(f"    Args: {tool_call.function.arguments}")
        print(f"    Valid: {('Y' if is_valid_tool_call(tool_call) else 'N')}")
        print("\n")


def format_tool_message(tool_call: ChatCompletionMessageToolCall, fn_res: str) -> dict:
    resp = {"role": "tool", "name": tool_call.function.name, "content": fn_res}
    # Handle OpenAI tool calls
    if tool_call.id:
        resp["tool_call_id"] = tool_call.id
    return resp


def format_assistant_message(choice: Choice) -> dict:
    resp = choice.message.to_dict(exclude_none=True)
    if resp.get("content") is None:
        resp["content"] = ""
    return resp


def has_func_calls(choice: Choice) -> bool:
    return choice.finish_reason == "tool_calls"


def get_actual_function(func_name: str) -> Callable | None:
    return function_library.get(func_name)


def execute_functions(choice: Choice) -> list:
    tool_call_messages = []
    tool_calls = choice.message.tool_calls
    print("Executing functions...\n")
    for tool_call in tool_calls:
        fnc = get_actual_function(tool_call.function.name)
        if fnc:
            if is_valid_tool_call(tool_call):
                fn_args = json.loads(tool_call.function.arguments)
                fn_res = fnc(**fn_args)
                tool_call_messages.append(format_tool_message(tool_call, fn_res))
            else:
                tool_call_messages.append(
                    format_tool_message(
                        tool_call,
                        "This function either does not exist, or the parameters provided were invalid.",
                    )
                )
    return tool_call_messages


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
    system_prompt = inspect.cleandoc(
        f"""
                    You are JARVIS, a helpful and witty assistant. 
                    You help a user with their tasks by using any of the functions available to you and your replies should always aim to be short but informative.
                    When a user refers to themselves in a prompt to create or recall a memory in the first person, change it to refer to 'The User'.
                    If you cannot answer a prompt based on information you have available, use your tools to find more information.
                    The current date is {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}
                    """
    )

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
                choice = client.chat.completions.create(
                    model=config["model_name"],
                    messages=messages,
                    tools=functions,
                    tool_choice="auto",
                ).choices[0]
                # Add AI response/function call requests to context
                messages.append(format_assistant_message(choice))
                # If there are no function calls, this will break the loop after this conversation turn
                if choice.finish_reason != "tool_calls":
                    print(choice.message.content)
                    finished = True
                    continue
                # Print all function calls the model is requesting
                print_func_calls(choice)
                # Execute functions and add their responses to the context
                func_responses = execute_functions(choice)
                messages.extend(func_responses)

        except KeyboardInterrupt:
            print(json.dumps(messages, indent=2))
            exit("Exiting...")


if __name__ == "__main__":
    main()
