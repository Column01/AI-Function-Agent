import os
import random
import time

import numpy as np
import torch
from diffusers import Lumina2Text2ImgPipeline

from ai_function_agent.tool_calling import join_path


# Where to load the model
if torch.cuda.is_available():
    device = "cuda"
    torch_dtype = torch.bfloat16
else:
    device = "cpu"
    torch_dtype = torch.float32


def gen_image(prompt: str, width: int = 512, height: int = 512, open: bool = True) -> str:

    # Clamp H and W to 1024 (subject to change)
    height = min(height, 1024)
    width = min(width, 1024)
    print("Loading image generation model...")
    pipe = Lumina2Text2ImgPipeline.from_pretrained(
        "Alpha-VLLM/Lumina-Image-2.0", torch_dtype=torch_dtype
    )
    pipe.to(device, torch_dtype)

    # Optimizations
    pipe.enable_vae_slicing()
    pipe.enable_vae_tiling()
    pipe.enable_model_cpu_offload()

    # Randomize the seed
    MAX_SEED = np.iinfo(np.int32).max
    seed = random.randint(0, MAX_SEED)

    # Generate the image
    image = pipe(
        prompt,
        height=height,
        width=width,
        guidance_scale=4.0,
        num_inference_steps=50,
        cfg_trunc_ratio=0.25,
        cfg_normalization=True,
        generator=torch.Generator().manual_seed(seed),
    ).images[0]

    os.makedirs(join_path("images"), exist_ok=True)
    f_name = join_path(f"images/image_{int(time.time())}.png")

    image.save(f_name)

    if open:
        image.show()
    return f"Image created at path: {f_name}"


function = gen_image
function_spec = {
    "type": "function",
    "function": {
        "name": "gen_image",
        "description": "Generates an image when requested by the user. If they did not specify a prompt, you MUST ask them for one before using this.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's prompt for the image generation model",
                },
                "width": {
                    "type": "number",
                    "description": "The user defined width of the image (or 512 if not specified)",
                },
                "height": {
                    "type": "number",
                    "description": "The user defined height of the image (or 512 if not specified)",
                }
            },
            "required": ["prompt"],
        },
    },
}


if __name__ == "__main__":
    while True:
        prompt = input("Image Generation Prompt: ")
        gen_image(prompt)
