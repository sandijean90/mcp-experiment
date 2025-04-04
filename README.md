# 🧠 Re-Act Agent with MCP Brave Search Integration

This Jupyter Notebook demonstrates how to use the **BeeAI Re-Act Agent** framework integrated with the **Model Context Protocol (MCP) Brave Server** to perform intelligent internet searches and local lookups via Brave’s Search APIs.

---

## 🚀 What It Does

- Connects to the Brave MCP server using a local subprocess.
- Discovers tools (`brave_web_search`, `brave_local_search`) via MCP.
- Initializes a Re-Act Agent (based on `OpenAI GPT-4o`) that can:
  - Decide when to use each tool.
  - React to responses and iterate intelligently.
- Runs a conversation loop allowing user queries and AI responses.

---

## 🛠️ Setup

1. **Install dependencies**:
   Make sure you have:
   - `beeai-framework`
   - `mcp`
   - `dotenv`
   - Access to `npx` and the Brave MCP server package

2. **Set up `.env` file**:

3. **Adjust paths**:
- Update the `.env` path and any system paths according to your local setup.

---

## 🧪 Run the Notebook

1. Load the environment and dependencies.
2. Start the Brave MCP server and discover available tools.
3. Initialize the Re-Act Agent with LLM, memory, and tools.
4. Run the agent in a conversation loop to handle user queries.

---

## 🐞 Notes

- There's a known bug in the Brave MCP server requiring a `count=5` parameter for certain queries. This is temporarily patched via the system prompt.
- Outputs are color-coded and printed via a helper `ConsoleReader` class for easier readability.

---

## 🌐 Tools Used

- `brave_web_search`: Web searches with filtering/pagination.
- `brave_local_search`: Local business lookups with detailed metadata.

---

## ✅ Example Use Case

> *"What are the opening hours for La Taqueria on Mission St in San Francisco?"*  
→ The agent will automatically select the appropriate tool and return real-time business details.
