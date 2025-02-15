# AI Function Agent (WIP!)

- Chat with your own local or remote AI assistant that can run custom python functions implicitly
- Build an AI mediated automation ecosystem tailored to your workload
- Generate images using the included image generation tool and the [Lumina-Image-2.0](https://huggingface.co/Alpha-VLLM/Lumina-Image-2.0) model!

## Important Note

Although the main function calling LLM can be remotely hosted, some of the included functions such as the Memory or the Image Generation require a reasonably powerful local system to use.

Development is done with an Ryzen 5600X w/ 32GB of RAM and an RTX 3060 12GB. When generating images the Lumina 2 image model eats most of my resources (all my VRAM and a lot of RAM) generating 512x512 images

If your system can't handle that, you should disable that function (change the [image generation script](functions/system/image_gen.py) file extensions to `.py.dis` or delete the file)

## Setup

### Model Selection

You're going to need find a model that has function calling capabilities. A good resource for selecting a model is the [Berkeley Function-Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)

Development is done using a quant of `Qwen2.5-14B-Instruct` from [bartowski](https://huggingface.co/bartowski). This model has good function-calling capabilities while also being great at general-purpose chatting.

A larger model with better overall capabilities is preferred as you will get a better general chatting experience.

### Pre-Requisites

- Download this repo
- Install Python 3.11+
- The code expects a model run by a OpenAI API compatable server
- **Other Recommendations:**
    - Create a python virtual environment (on linux, use `python3`):
        - `python -m venv aiAgentVenv`
    - Once created, it can be activated with:
        - `./aiAgentVenv/Scripts/activate`
    - If you want to run the main LLM locally, we recommend using [llama.cpp](https://github.com/ggerganov/llama.cpp/releases)'s OpenAI API [compatable server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md).


### Modules

Installing modules in the correct order helps make sure everything installs with proper support for acceleration when applicable.

1. [Install torch, torchvision, and torchaudio](https://pytorch.org/get-started/locally/) with CUDA/ROCM if possible
2. `pip install duckduckgo-search qwen-agent transformers usearch`
3. `pip install git+https://github.com/zhuole1025/diffusers.git@lumina2` (fork of diffusers with new lumina2 image pipeline)

## Usage

### Backend Configuration

You'll need to open and edit the [config.json](/config.json) file locally to have the correct URL and API key for your tool calling model. This can be a locally hosted model, or a remote model so long as the backend uses an OpenAI API compatable server.

As stated above, for local use we recommend using [llama.cpp](https://github.com/ggerganov/llama.cpp/releases)'s OpenAI API [compatable server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md).

### Running the Script

Run the script to prompt the model for function calling (assuming you activated the venv!)

`python tool_calling.py`

After it has been run, it will ask for a prompt. Be descriptive for what you want the model to do so it knows which tools to select, and what to do with any data it gets from the tools.

You can also use this for normal LLM chatting if you'd like.

There are a few commands you can use in the prompt, type `help` to list them all.

### Available tools

Pre-made tools exist and can be found in the [functions](/functions) folder of the repo.

### Making your own tooling

Custom tools can be created by placing a new function script in the `functions/user/` folder of the project which can then be used by running the `tool_calling.py` script again. Once it starts, you can type `load` in the prompt to load your user functions (alternatively, the config can be changed to load them at startup)

Below is a template you can use, the `function` variable must point to the function the LLM should use. The `function_spec` variable MUST follow the [OpenAI tool/function format](https://platform.openai.com/docs/guides/function-calling) and is required for your function to be loaded and registered as usable with the model.

```py
def say_hello(name: str) -> str:
    print(f"Hello, {name}!")
    return f"Hello, {name}!"


function = say_hello
function_spec = {
    "type": "function",
    "function": {
        "name": "say_hello",
        "description": "Says hello to someone, the returned value is the message that was sent.",
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

### Memory

The model is equipped with tooling to remember text for you, and recall it based on a query. Due to the simplistic nature of the models, anything you ask it to remember or recall should be relatively explicit. If you said "remember I like apples" it could choose to remember, literally, "I like apples".

Here is an example asking it to remember my apple preference. **Notice how I was explicit with what I wanted it to remember**

```md
Prompt: Can you remember something for me? Remember: "The user prefers gala apples"        
Prompting the backend for function calls...


Functions to call (invalid functions will be ignored!):  

create_memory
    Args: {'memory_text': 'The user prefers gala apples'}
    Valid: Y


Executing functions...

Creating new memory...
Onloading text embedding model to GPU...
Created new memory and indexed to: memory\index\memory_1738100862.txt
I've remembered that the user prefers gala apples. Is there something else you'd like me to remember?
```

Here is another example, except this time is an entirely fresh run, and I'm now asking it to remember what apples I prefer


```md
Prompt: Can you remember what type of apples I prefer?
Prompting the backend for function calls...


Functions to call (invalid functions will be ignored!): 

recall_memory
    Args: {'query': 'apple preference'}
    Valid: Y


Executing functions...

Retrieving documents from memory with query: apple preference
Onloading text embedding model to GPU...
You prefer gala apples.
```
