import glob
import inspect
import json
import os
from datetime import datetime
from importlib import util
from typing import Optional
import uuid

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
import uvicorn

# Initialize FastAPI app
app = FastAPI()

# Determine script location and define join_path lambda
__location__ = os.path.dirname(os.path.realpath(__file__))
join_path = lambda x: os.path.join(__location__, x)

# Set conversations directory using join_path
CONVERSATIONS_DIR = join_path("conversations")
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

# Load or create configuration
config_path = join_path("config.json")
if not os.path.exists(config_path):
    with open(config_path, "w") as fp:
        config = {
            "model_name": "Qwen",
            "api_url": "http://localhost:8080/v1",
            "api_key": "EMPTY",
            "load_user_funcs": False,
            "web_server": {"host": "127.0.0.1", "port": 8000, "reload": False},
        }
        json.dump(config, fp, indent=4)
        print(f"\nNEW CONFIG FILE CREATED FOR EDITING: {config_path}")
else:
    with open(config_path, "r") as fp:
        config = json.load(fp)

# Set up OpenAI client
client = OpenAI(base_url=config.get("api_url"), api_key=config.get("api_key"))


# Function to import modules from glob pattern
def glob_import(glob_str: str) -> tuple[dict, list]:
    function_library = {}
    functions = []
    file_paths = glob.glob(glob_str)
    for file_path in file_paths:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = util.spec_from_file_location(module_name, file_path)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "function"):
            fn = module.function
            if isinstance(fn, list):
                for fnc in fn:
                    function_library[fnc.__name__] = fnc
            else:
                function_library[fn.__name__] = fn
        if hasattr(module, "function_spec"):
            func_spec = module.function_spec
            if isinstance(func_spec, list):
                functions.extend(func_spec)
            else:
                functions.append(func_spec)
    return function_library, functions


# Import system and user functions
system_function_library, TOOLS = glob_import(join_path("functions/system/*.py"))
function_library = system_function_library
functions = TOOLS

if config.get("load_user_funcs"):
    user_function_library, USER_TOOLS = glob_import(join_path("functions/user/*.py"))
    function_library.update(user_function_library)
    functions.extend(USER_TOOLS)

# Define system message
system_prompt = inspect.cleandoc(
    f"""
    You are JARVIS, a helpful and witty assistant. 
    You help a user with their tasks by using any of the functions available to you and your replies should always aim to be short but informative.
    When a user refers to themselves in a prompt to create or recall a memory in the first person, change it to refer to 'The User'.
    If you cannot answer a prompt based on information you have available, use your tools to find more information.
    The current date is {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}
    """
)
system_message = {"role": "system", "content": system_prompt}


# Helper functions
def is_valid_tool_call(tool_call: ChatCompletionMessageToolCall) -> bool:
    fn_name = tool_call.function.name
    fn_args = json.loads(tool_call.function.arguments)
    fnc = function_library.get(fn_name)
    if not fnc:
        return False
    params = inspect.signature(fnc).parameters
    fnc_args = params.keys()
    model_args = fn_args.keys()
    extra = [arg for arg in model_args if arg not in fnc_args]
    if len(extra) != 0:
        return False
    missing = fnc_args - model_args
    if len(missing) == 0:
        return list(params.keys()) == list(fn_args.keys())
    for key in missing:
        param = params.get(key)
        if param.default == inspect.Parameter.empty:
            return False
    return True


def format_tool_message(tool_call: ChatCompletionMessageToolCall, fn_res: str) -> dict:
    resp = {"role": "tool", "name": tool_call.function.name, "content": fn_res}
    if tool_call.id:
        resp["tool_call_id"] = tool_call.id
    return resp


def format_assistant_message(choice: Choice) -> dict:
    resp = choice.message.to_dict(exclude_none=True)
    if resp.get("content") is None:
        resp["content"] = ""
    resp.pop("reasoning", None)
    return resp


def execute_functions(choice: Choice) -> list:
    tool_call_messages = []
    tool_calls = choice.message.tool_calls
    for tool_call in tool_calls:
        fnc = function_library.get(tool_call.function.name)
        if fnc and is_valid_tool_call(tool_call):
            fn_args = json.loads(tool_call.function.arguments)
            fn_res = fnc(**fn_args)
            if not isinstance(fn_res, str):
                fn_res = str(fn_res)
            tool_call_messages.append(format_tool_message(tool_call, fn_res))
        else:
            tool_call_messages.append(
                format_tool_message(
                    tool_call,
                    "This function either does not exist, or the parameters provided were invalid.",
                )
            )
    return tool_call_messages


# Conversation management functions
def generate_conversation_id() -> str:
    return str(uuid.uuid4())


def load_conversation(conversation_id: str) -> list:
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Conversation not found")
    with open(file_path, "r") as f:
        return json.load(f)


def save_conversation(conversation_id: str, messages: list):
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    with open(file_path, "w") as f:
        json.dump(messages, f, indent=2)


# FastAPI endpoints
@app.post("/prompt")
async def send_prompt(prompt: str, conversation_id: Optional[str] = None):
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # Start new conversation or load existing one
    if conversation_id is None:
        conversation_id = generate_conversation_id()
        messages = [system_message]
    else:
        messages = load_conversation(conversation_id)

    # Append user's prompt
    messages.append({"role": "user", "content": prompt})
    initial_length = len(messages)

    # Process AI response and tool calls
    finished = False
    while not finished:
        choices = client.chat.completions.create(
            model=config["model_name"],
            messages=messages,
            tools=functions,
            tool_choice="auto",
        ).choices
        choice = choices[0]
        assistant_messages = format_assistant_message(choice)
        messages.append(assistant_messages)
        if choice.finish_reason != "tool_calls":
            finished = True
            continue
        func_responses = execute_functions(choice)
        messages.extend(func_responses)

    # Save updated conversation
    save_conversation(conversation_id, messages)

    # Return only new messages
    new_messages = messages[initial_length:]
    return {"conversation_id": conversation_id, "new_messages": new_messages}


@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    messages = load_conversation(conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}


# New function to start Uvicorn server
def start():
    web_server_config = config.get("web_server", {})
    host = web_server_config.get("host", "127.0.0.1")
    port = int(web_server_config.get("port", 8000))  # Ensure port is an integer
    reload = web_server_config.get("reload", False)
    uvicorn.run(app, host=host, port=port, reload=reload)


# Start server when script is run directly
if __name__ == "__main__":
    start()
