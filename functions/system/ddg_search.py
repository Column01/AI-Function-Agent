import json

searcher = None

try:
    from duckduckgo_search import DDGS
    searcher = DDGS()
except ImportError:
    print("No module named 'duckduckgo_search' found")


def ddg_search(query: str, max_results: int = 5) -> str:
    if searcher is not None:
        return json.dumps(searcher.text(query, max_results=max_results))
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
                "max_results": {"type": "int", "description": "The number of results to get, defaults to 5 results"}
            },
            "required": ["query"],
        },
    },
}


if __name__ == "__main__":
    res = ddg_search("cat food")
    print(res)
