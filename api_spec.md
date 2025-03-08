# API Backend Specification

The backend is a custom one using 2 main endpoints for interacting with the model. Currently, there is no authentication for the backend so be cautious when opening ports to access! (this **will** change later and an API key system will be added)

## Conversation IDs

Conversation IDs are created by the backend and returned when making a conversation, so be sure to keep track of it. An example of one is shown in the API examples below

## API Usage Examples

Below are examples of using the endpoints from the API. All request examples are using curl commands to represent how to execute the requests. All respones from the API are in json

### `/prompt`

The main program route is `/prompt`. This route when used will return something that is similar to traditional LLM conversation, except it will only return new messages from the model.

**Request:**
```
curl -X 'POST' \
  'http://127.0.0.1:8000/prompt?prompt=What%20is%20my%20favorite%20flavor%20of%20apple%3F' \
  -H 'accept: application/json' \
  -d ''
```

**Response:**
```json
{
  "conversation_id": "242fee1b-fe1f-4fa3-ba77-6287b0fe4a13",
  "new_messages": [
    {
      "role": "assistant",
      "tool_calls": [
        {
          "id": "call_regx",
          "function": {
            "arguments": "{\"query\": \"The User favorite flavor of apple\"}",
            "name": "recall_memory"
          },
          "type": "function"
        }
      ],
      "content": ""
    },
    {
      "role": "tool",
      "name": "recall_memory",
      "content": "[\n  \"The user prefers gala apples\"\n]",
      "tool_call_id": "call_regx"
    },
    {
      "content": "The User's favorite flavor of apple is gala.",
      "role": "assistant"
    }
  ]
}
```

Now to demonstrate how it only sends new messages, this is an example of continuing that same conversation and how the API would respond to me.

**Request:**
```
curl -X 'POST' \
  'http://127.0.0.1:8000/prompt?prompt=Thank%20you%21&conversation_id=242fee1b-fe1f-4fa3-ba77-6287b0fe4a13' \
  -H 'accept: application/json' \
  -d ''
```

**Response:**
```json
{
  "conversation_id": "242fee1b-fe1f-4fa3-ba77-6287b0fe4a13",
  "new_messages": [
    {
      "content": "You're welcome. Is there anything else I can help you with?",
      "role": "assistant"
    }
  ]
}
```

### `/conversation/{conversation_id}`

This endpoint retrieves an entire conversation history (including the system prompt!) using a `conversation_id` that you would have recieved when creating the thread.

**Request:**
```
curl -X 'GET' \
  'http://127.0.0.1:8000/conversation/242fee1b-fe1f-4fa3-ba77-6287b0fe4a13' \
  -H 'accept: application/json'
```

**Response:**
```json
{
  "conversation_id": "242fee1b-fe1f-4fa3-ba77-6287b0fe4a13",
  "messages": [
    {
      "role": "system",
      "content": "You are JARVIS, a helpful and witty assistant. \nYou help a user with their tasks by using any of the functions available to you and your replies should always aim to be short but informative.\nWhen a user refers to themselves in a prompt to create or recall a memory in the first person, change it to refer to 'The User'.\nIf you cannot answer a prompt based on information you have available, use your tools to find more information.\nThe current date is 2025-03-01 09:05:07"
    },
    {
      "role": "user",
      "content": "What is my favorite flavor of apple?"
    },
    {
      "role": "assistant",
      "tool_calls": [
        {
          "id": "call_regx",
          "function": {
            "arguments": "{\"query\": \"The User favorite flavor of apple\"}",
            "name": "recall_memory"
          },
          "type": "function"
        }
      ],
      "content": ""
    },
    {
      "role": "tool",
      "name": "recall_memory",
      "content": "[\n  \"The user prefers gala apples\"\n]",
      "tool_call_id": "call_regx"
    },
    {
      "content": "The User's favorite flavor of apple is gala.",
      "role": "assistant"
    },
    {
      "role": "user",
      "content": "Thank you!"
    },
    {
      "content": "You're welcome. Is there anything else I can help you with?",
      "role": "assistant"
    }
  ]
}
```

## OpenAPI Specification

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "FastAPI",
    "version": "0.1.0"
  },
  "paths": {
    "/prompt": {
      "post": {
        "summary": "Send Prompt",
        "description": "Creates or continues a conversation thread. To create a thread, do not include a conversation_id, to continue one, include the conversation_id returned after your first message",
        "operationId": "send_prompt_prompt_post",
        "parameters": [
          {
            "name": "prompt",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Prompt"
            }
          },
          {
            "name": "conversation_id",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Conversation Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {

                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/conversation/{conversation_id}": {
      "get": {
        "summary": "Get Conversation",
        "description": "Retrieves a conversation in its entirety from the local conversation history",
        "operationId": "get_conversation_conversation__conversation_id__get",
        "parameters": [
          {
            "name": "conversation_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Conversation Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {

                }
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "type": "array",
            "title": "Detail"
          }
        },
        "type": "object",
        "title": "HTTPValidationError"
      },
      "ValidationError": {
        "properties": {
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "type": "array",
            "title": "Location"
          },
          "msg": {
            "type": "string",
            "title": "Message"
          },
          "type": {
            "type": "string",
            "title": "Error Type"
          }
        },
        "type": "object",
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError"
      }
    }
  }
}
```
