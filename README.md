# AI Function Agent

A simple script using Qwen-Agent to access a locally running model for function/tool calling.

## Setup

### Pre-Requisites

- Download this repo
- Install Python 3.11+
- **Recommended:**
    - Create a python virtual environment (on linux, use `python3`):
    - `python -m venv aiAgentVenv`
    - Once created, it can be activated with:
    - `./venv/Scripts/activate`
    - All future installed modules will no longer overwrite your system packages!

### Modules

Installing modules in the correct order helps make sure everything installs with proper support for acceleration when applicable.

1. [Install torch, torchvision, and torchaudio](https://pytorch.org/get-started/locally/) with CUDA/ROCM if possible
2. `pip install duckduckgo-search qwen-agent transformers usearch`

## Usage

Run the script to prompt the model for function calling (assuming you activated the venv!)

`python tool_calling.py`

After it has been run, it will ask for a prompt. Be descriptive for what you want the model to do so it knows which tools to select, and what to do with any data it gets from the tools.

### Available tools

Pre-made tools exist and can be found in the [functions](/functions) folder of the repo

### Making your own tooling

Custom tools can be created by placing a new function script in the `functions` folder of the project which can then be used by running the `tool_calling.py` script again

Below is a template you can use, the `function` and the `function_spec` variables MUST follow the [OpenAI tool/function format](https://platform.openai.com/docs/guides/function-calling) and are required for your function to be loaded and registered as usable with the model

```py
def say_hello(name: str) -> str:
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
                "name": {"type": "string", "description": "The person's name"}
            },
            "required": ["name"],
        },
    },
}

```

## Examples

### Asking for weather

Here is an example of asking the model to find the weather in a location (the lat/long is generated by the model based on your specified location, so it could be incorrect! This might change at a later date)

```md
Prompt: What's the weather like in Ottawa?
Prompting the backend for function calls...
What's the weather like in Ottawa?

Functions to call (invalid functions will be ignored!): 

get_weather
    Args: {"latitude": "45.4215", "longitude": "-75.6919"}
    Valid: Y


Confirm? (y/n): y
Executing functions...

The current temperature in Ottawa is -16.6°C and the wind speed is 12.5 meters per second. It's quite chilly, make sure to wear warm clothes if you plan on going outside!
```

### Searching the internet

Here is an example of asking the model to search the internet for information about the new Nvidia DLSS 4 frame generation:

```md
Prompt: Can you search for info about the DLSS 4 and the new frame generation from nvidia? Do two separate searches for both  
Prompting the backend for function calls...
Can you search for info about the DLSS 4 and the new frame generation from nvidia? Do two separate searches for both

Functions to call (invalid functions will be ignored!): 

ddg_search
    Args: {"query": "DLSS 4", "max_results": 5}
    Valid: Y

ddg_search
    Args: {"query": "Nvidia new frame generation", "max_results": 5}
    Valid: Y


Confirm? (y/n): y
Executing functions...

Here's the information I found:

For DLSS 4:
- DLSS 4 is a suite of neural rendering technologies that boosts frame rates and image quality for over 700 RTX games and apps.
- It features Multi Frame Generation for GeForce RTX 50 Series GPUs, and a new transformer model for Ray Reconstruction, Super Resolution, and DLAA.

Regarding Nvidia's new frame generation:
- It is part of the DLSS 4 technology suite, specifically Multi Frame Generation, which generates up to three additional frames for each rendered frame, boosting frame rates.
- It will be supported by 75 games and apps from the start of the GeForce RTX 50 Series GPUs' availability.

For more detailed information, you can check out these sources:
- [NVIDIA DLSS 4 Introduces Multi Frame Generation & Enhancements For All](https://www.nvidia.com/en-us/geforce/news/dlss4-multi-frame-generation-ai-innovations/)
- [NVIDIA DLSS 4 Introduces Multi Frame Generation & Enhancements For All...](https://www.nvidia.com/en-us/geforce/news/dlss4-multi-frame-generation-ray-tracing-rtx-games/)
```
