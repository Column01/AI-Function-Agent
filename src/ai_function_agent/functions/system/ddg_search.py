import json

searcher = None

try:
    from duckduckgo_search import DDGS
    searcher = DDGS()
except ImportError:
    print("No module named 'duckduckgo_search' found")


def ddg_search(query: str, results: int = 3) -> list[dict]:
    if searcher is not None:
        text = searcher.text(query, max_results=results)
        return text
    else:
        return "Cannot load the duckduckgo search module!"


function = ddg_search
function_spec = {
    "type": "function",
    "function": {
        "name": "ddg_search",
        "description": "Searches the internet using duck duck go.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to look for"},
                "results": {"type": "number", "description": "The number of (max) results to get, defaults to 3 results"}
            },
            "required": ["query"],
        },
    },
}


if __name__ == "__main__":
    res = ddg_search("cat food")
    print(res)
