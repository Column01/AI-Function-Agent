from datetime import datetime

from qwen_agent.llm import get_chat_model

import functions as funcs


def main():
    llm = get_chat_model({
        "model": "Qwen",
        "model_server": "http://localhost:8080/v1",
        "api_key": "EMPTY"
    })

    # Ask for the prompt
    prompt = input("Prompt: ")
    # If no prompt is provided, use this default prompt (mostly for testing purposes)
    if not prompt:
        prompt = "Can you say hello to Bob the Builder? Ask bob how old he is and let me know."

    messages = [
        {"role": "system", "content": f"You are JARVIS, a helpful and witty assistant. You help users with their tasks by using any of the functions available to you and your replies should always aim to be short but informative. The current date is {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"},
        {"role": "user", "content": prompt}
    ]

    print("Prompting the backend for function calls...")
    print(messages[1]["content"])

    # Do initial inference to le the AI select function calls
    for responses in llm.chat(
        messages=messages,
        functions=funcs.functions,
        extra_generate_cfg=dict(parallel_function_calls=True)
    ):
        pass

    # Print all function calls the model is requesting
    funcs.print_func_calls(responses)
    # Ask for confirmation before running any functions
    if funcs.confirm_input():
        # Add function calls to context
        messages.extend(responses)
        # Execute functions and add their responses to the context
        func_responses = funcs.execute_functions(responses)
        messages.extend(func_responses)
        # Get the AI's final response after tool calls and print it
        for responses in llm.chat(messages=messages, functions=funcs.functions):
            pass
        messages.extend(responses)
        print(messages[-1]["content"])


if __name__ == "__main__":
    main()
