# AI Function Agent (WIP!)

A simple script using OpenAI's Python library to connect to an LLM inference backend for AI-Controlled python function calling

- Chat with your own locally or remotely hosted AI assistant that can run python code implicitly
- Build AI mediated automation ecosystems tailored to your workload
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
    - If you want to run the main LLM locally, we recommend using [llama.cpp](https://github.com/ggerganov/llama.cpp/releases)'s OpenAI API [compatable server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md). **Be sure to enable `--jinja` if you use this backend to enable the tool calling**


### Installation

Installing modules in the correct order helps make sure everything installs with proper support for acceleration when applicable.

1. Clone the repository:
    - `git clone https://github.com/Column01/AI-Function-Agent.git`
2. Create a python virtual environment (on linux, use `python3`):
    - `python -m venv aiAgentVenv`
3. Activate that virtual environment\
    - `./aiAgentVenv/Scripts/activate`
4. [Install torch, torchvision, and torchaudio](https://pytorch.org/get-started/locally/) with CUDA/ROCM if possible
5. Install the AI Function Agent package (this repo)
    - `pip install -e .`
6. Install diffusers from source (for lumina2 support) 
    - `pip install git+https://github.com/huggingface/diffusers`

## Usage

### Running the Script

In order to configure the script, you will need to run it the first time to generate a `config.json` file for you.

You can run the script with the following command (assuming you activated the venv first!)

`ai-function-agent`

After it has been run the new location of the config file shoudl have been printed to your console. After you have that copied, you can type `exit` close the prompt so we can edit the newly created config file (see [Backend Configuration](#backend-configuration) for instructions on how to do that). If you are using `llama.cpp` server we recommend for local use as the backend, it is already configured to connect to a model running on the local machine and it will ask for a prompt. Be descriptive for what you want the model to do so it knows which tools to select, and what to do with any data it gets from the tools.

You can also use this for normal LLM chatting if you'd like.

There are a few commands you can use in the prompt, type `help` to list them all.

### Backend Configuration

You'll need to open and edit the newly created `config.json` file. To locate this file, the program should have printed out the location to your console on the first run. If you closed the terminal without saving that path (and followed the install guide properly) the config should be located here: `src/ai_function_agent/config.json` (assuming you are at the project root).

Once located, you need to open it and edit the fields to have the correct URL and API key for your tool calling model. This can be a locally hosted model, or a remote model so long as the backend uses an OpenAI API compatable server.

As stated above, for locally hosting a model use we recommend using [llama.cpp](https://github.com/ggerganov/llama.cpp/releases)'s OpenAI API [compatable server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md). Be sure to enable the `--jinja` flag for tool calling support!

### Available tools

Pre-made tools can be found in the [functions](/functions) folder of the repo.

### Making your own tooling

Custom tools can be created by placing a new function script in the `functions/user/` folder of the project which can then be used by running the `tool_calling.py` script again. Once it starts, you can type `load` in the prompt to load your user functions (alternatively, the config can be changed to load them at startup)

Below is a template you can use, the `function` variable must point to the function the LLM should use. The `function_spec` variable MUST follow the [OpenAI tool/function format](https://platform.openai.com/docs/guides/function-calling) and is required for your function to be loaded and registered as usable with the model.

```py
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
```

## Other Notes

### Good Model hosts

A good model host to get your foot in the door is [Groq.com](https://groq.com/). I've been testing out their free tier for development purposes and their rate limits/daily limits are really generous, and the model selection they have is great! You could also make functions for this tool to use their other models for tasks. They offer pay per token pricing, that information is available [on their website](https://groq.com/pricing/).
For example, the `qwen2.5-32b` model has no daily limit on tokens per day. Instead they opted to limit the number of requests per minute, tokens per minute, and another limit on requests per day (which does effectively limit you to a certain number of tokens max, but it is still generous enough to allow normal use).
You can get an API key by signing in with a Google account so no need for making a new account, and as mentioned before they have a free tier that is relatively generous

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
