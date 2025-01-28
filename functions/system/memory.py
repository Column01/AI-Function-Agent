import glob
import json
import os
import time

import torch
import torch.nn.functional as F
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer
from usearch.index import Index


def mean_norm_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = (
        attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    )
    return F.normalize(
        torch.sum(token_embeddings * input_mask_expanded, 1)
        / torch.clamp(input_mask_expanded.sum(1), min=1e-9),
        p=2,
        dim=1,
    )


# Text Embedding Model
tokenizer = AutoTokenizer.from_pretrained("nomic-ai/modernbert-embed-base")
text_embed_model = AutoModel.from_pretrained("nomic-ai/modernbert-embed-base")
onloaded = False


def onload():
    """Onloads the Text Embedding model for GPU acceleration if available"""
    global text_embed_model, onloaded
    if torch.cuda.is_available() and not onloaded:
        print("Onloading text embedding model to GPU...")
        text_embed_model.cuda()
        onloaded = True


def offload():
    """Offloads the Text Embedding model to save VRAM"""
    global text_embed_model, onloaded
    if onloaded:
        print("Offloading text embedding model to CPU...")
        text_embed_model.cpu()
        onloaded = False


if not os.path.exists("memory"):
    os.mkdir("memory")
    os.mkdir("memory/index")

metadata = {}
index = Index(ndim=768)
i = 0
if os.path.isfile("memory/index.usearch"):
    index.load("memory/index.usearch")
    i = len(index)

if os.path.isfile("memory/metadata.json"):
    with open("memory/metadata.json", "r") as fp:
        metadata = json.load(fp)


def index_file(path, auto_save=True, onload_model=True) -> str:
    global i

    if onload_model:
        onload()

    document = ""
    new_path = os.path.join(os.path.dirname(path), "index", os.path.basename(path))
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    os.rename(path, new_path)

    with open(new_path, "r") as fp:
        document = fp.read()

    with torch.no_grad():
        # Format the document for what the nomic-ai/modernbert-embed-base model expects
        document = "search_document: " + document
        encoded_document = tokenizer(
            document, padding=True, truncation=True, return_tensors="pt"
        )

        if onloaded and torch.cuda.is_available():
            encoded_document = {k: v.cuda() for k, v in encoded_document.items()}
        documents_output = text_embed_model(**encoded_document)

        vector = mean_norm_pooling(documents_output, encoded_document["attention_mask"])
        index.add(i, vector.squeeze(0).cpu().numpy())
        metadata[str(i)] = new_path
        i += 1

    if auto_save:
        index.save("memory/index.usearch")
        with open("memory/metadata.json", "w") as fp:
            json.dump(metadata, fp, indent=4)

    # if onload_model:
    #     offload()

    return new_path


def index_memory():
    """
    Indexes all text files in the 'memory' directory by embedding their contents into vectors and adding them to an index.

    This function processes each text file in the 'memory' directory, uses the `index_file` function to create embeddings,
    and adds the embeddings to the index. After processing all files, it saves the index to a file named 'memory/index.usearch'.
    """
    onload()
    for file_path in glob.glob("memory/*.txt"):
        print(f"Processing file: {file_path}")
        index_file(file_path, auto_save=False, onload_model=False)

    index.save("memory/index.usearch")
    with open("memory/metadata.json", "w") as fp:
        json.dump(metadata, fp, indent=4)
    offload()


def find_document(queries, n_docs=1, onload_model=True):
    if onload_model:
        onload()
    with torch.no_grad():
        formatted_queries = ["search_query: " + document for document in queries]
        encoded_documents = tokenizer(
            formatted_queries, padding=True, truncation=True, return_tensors="pt"
        )

        if onloaded and torch.cuda.is_available():
            encoded_documents = {k: v.cuda() for k, v in encoded_documents.items()}

        documents_outputs = text_embed_model(**encoded_documents)

        doc_embeddings = mean_norm_pooling(
            documents_outputs, encoded_documents["attention_mask"]
        )

        matches = []

        for doc_embedding in doc_embeddings:
            documents = index.search(doc_embedding.cpu().numpy(), n_docs)
            matches.append(documents)

        return matches


def recall_memory(query: str, n_docs: int = 1) -> str:
    print(f"Retrieving documents from memory with query: {query}")
    matches = find_document([query], n_docs=n_docs)
    if matches:
        documents = []
        for _matches in matches:
            for match in _matches:
                path = metadata.get(str(match.key))
                if path:
                    with open(path, "r") as fp:
                        file_data = fp.read()
                        documents.append(file_data)
        return json.dumps(documents, indent=2)


def create_memory(memory_text: str) -> str:
    # Create a new text file in the '/memory' subdirectory with the memory_text
    file_path = os.path.join("memory", f"memory_{int(time.time())}.txt")
    print(f"Creating new memory...")
    with open(file_path, "w") as fp:
        fp.write(memory_text)

    # Index the newly created file
    new_path = index_file(file_path, auto_save=True, onload_model=True)
    print(f"Created new memory and indexed to: {new_path}")
    return f"New memory file created and indexed at: {new_path}"


function = [create_memory, recall_memory]
function_spec = [
    {
        "type": "function",
        "function": {
            "name": "create_memory",
            "description": "Called when the user requests you to create a memory. Memories are simple text and storerd as text files in your 'brain' for lack of a better word.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_text": {
                        "type": "string",
                        "description": "The text the user requested you to remember.",
                    }
                },
                "required": ["memory_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Called when you want to recall a memory based on a query. Can be used to find information stored locally about the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A query to search the memory for",
                    },
                    "n_docs": {
                        "type": "int",
                        "description": "An optional amount for the number of memories to retrieve",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
