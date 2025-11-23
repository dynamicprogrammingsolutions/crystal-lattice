```
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, write a short poem."}
    ],
    "stream": false
  }"
```

curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    "model": "deepseek-r1:1.5b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a short poem and count how many R letters are in it?"}
    ],
    "think": true,
    "stream": false
  }"


curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    "model": "deepseek-r1:1.5b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a short poem and count how many R letters are in it?"}
    ],
    "think": true,
    "stream": true
  }"

curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    "model": "qwen3:0.6b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a short poem and count how many R letters are in it?"}
    ],
    "think": true,
    "stream": true
  }"

curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    "model": "qwen3:0.6b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Calculate a color code from the given words.\n\nWORDS: Mountain Sky River Forest Cloud\n\nSteps:\n1. Count total number of vowels (a,e,i,o,u) in all words = vowel_count\n2. Count total number of words = word_count\n3. Calculate: code = (vowel_count + word_count * 2) mod 8\n\nColor codes:\n0: \"red\"\n1: \"blue\"\n2: \"green\"\n3: \"yellow\"\n4: \"purple\"\n5: \"orange\"\n6: \"pink\"\n7: \"brown\"\n\nOutput only the color name for your calculated code."}
    ],
    "think": true,
    "stream": true
  }"

{"id":"chatcmpl-345","object":"chat.completion","created":1763756595,"model":"qwen3:0.6b","system_fingerprint":"fp_ollama","choices":[{"index":0,"message":{"role":"assistant","content":"purple","reasoning":"Okay, let"s do this step by step. First, I need to count the vowels in all the given words. The words are Mountain, Sky, River, Forest, Cloud.\n\nLooking at each word:\n- Mountain: M, A, U, N. So vowels here are A and U, which are two vowels.\n- Sky: S, K, I, Y. Vowels are I. One vowel here.\n- River: R, I, V, E, R. Vowels are I and E. Two vowels here.\n- Forest: F, O, R, E, S. Vowels are O and E. Two vowels here.\n- Cloud: C, L, O, U, D. Vowels are O and U. Two vowels here.\n\nSo, adding all vowels together: Mountain has 2, Sky has 1, River 2, Forest 2, Cloud 2. Total vowels count is 2+1+2+2+2 = 9. \n\nNext, count the number of words. That"s 5 words, so word_count is 5. \n\nNow, calculate the code. The formula is (vowel_count + word_count * 2) mod 8. Let"s plug in the numbers. \n\nVowel_count is 9, word_count is 5. So 9 + 5*2 = 9 + 10 = 19. Then 19 mod 8. Let"s do 19 divided by 8 is 2 with a remainder of 3. So the remainder is 3. \n\nNow, look at the color code. The third position is 3, which corresponds to \"purple\". So the final answer should be purple.\n"},"finish_reason":"stop"}],"usage":{"prompt_tokens":146,"completion_tokens":368,"total_tokens":514}}


curl -s http://localhost:11434/api/chat -H "Content-Type: application/json" -d "{
  "model": "qwen3:0.6b",
  "messages": [{"role": "user", "content": "What are the current weather conditions and temperature in New York and London?"}],
  "stream": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_temperature",
        "description": "Get the current temperature for a city",
        "parameters": {
          "type": "object",
          "required": ["city"],
          "properties": {
            "city": {"type": "string", "description": "The name of the city"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_conditions",
        "description": "Get the current weather conditions for a city",
        "parameters": {
          "type": "object",
          "required": ["city"],
          "properties": {
            "city": {"type": "string", "description": "The name of the city"}
          }
        }
      }
    }
  ]
}"


curl -s http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{"model": "qwen3:0.6b", "tools": [{"type": "function", "function": {"name": "read_file", "description": "Read contents of a text file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Path to the file to read"}}, "required": ["file_path"]}}}], "tool_choice": "auto", "messages": [{"role": "system", "content": "You are a helpful assistant. You MUST use the read_file tool to answer questions about file contents. Never guess."}, {"role": "user", "content": "Read and return the content of this file using the tool: /Users/ferenci84/Dev/Mine/ai-agent-platform/tmpbi46qbxt"}], "stream": false}'