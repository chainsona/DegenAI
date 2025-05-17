![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

[Chat with DegenAi 🤖](https://agentverse.ai/agents/details/agent1qwxczd9zm38ku74f3nxev66ltu7vcyseegwcjmx6h47lh0g7at8qj5z7e95/profile)

## 🏡 Project Overview

This repository implements a modular, AI‑driven Solana memecoin analysis and trading agent using the FetchAi uAgents framework. It consists of three main components:

1. **`chat.py`** – Handles natural‑language parsing via ASI‑1 LLM, extracting user intents (analyze, buy, sell) and token addresses into structured JSON.  
2. **`query.py`** – Defines data schemas and fetches on‑chain memecoin metrics (prices, trade volumes, buyer/seller counts, liquidity) from Bitquery’s GraphQL API.  
3. **`agent.py`** – Orchestrates the full agent runtime: enforces rate limits, routes chat messages, invokes analysis, and executes trades via PumpPortal.

Together, these pieces form an autonomous agent capable of understanding user prompts, gathering data, generating expert analysis, scoring tokens, and executing on‑chain buy/sell orders.

---

## 🧵 Features

- **Natural‑Language Processing**  
  Parses user prompts and extracts, **“/analyze”**, **“/buy”**, and **“/sell”** commands with highly structured accuracy.

- **On‑Chain Data Retrieval**  
  Pulls real‑time 15‑minute DEX metrics (volumes, unique traders, highs) for any Solana token.

- **AI‑Driven Analysis**  
  Uses ASI‑1 to craft detailed memecoin briefings (price action, sentiment, strategy) complete with emoji‑rich, markdown‑formatted reports. It also adopts a scoring system where a memecoin is rated from **1 to 10** on how **risky to safe** it is to buy.

- **Automated Trading**  
  Executes buy/sell orders via PumpPortal based on parsed commands or agent‑computed thresholds.

- **Structured Protocols**  
  Leverages uAgents’ chat and structured‑output protocols for robust inter‑agent communication.

---

## ⬅️ Prerequisites

- **Python 3.9+**  
- **FetchAi uAgents SDK**  
- **ASI‑1 API key** (set via `AGENTVERSE_API_KEY` in environment or secrets)  
- **Bitquery API key** (`BITQUERY_API_KEY`)  
- **PumpPortal API key** (`PUMP_PORTAL_API_KEY`)  
- Network access to:  
  - `https://api.asi1.ai`  
  - `https://streaming.bitquery.io/eap`  
  - `https://pumpportal.fun/api/trade`

---

## 🔃 Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/praise04/fetchAi-pump-agent
2. **Install requirements**
   ```
        pip install requirements.txt
3. **Populate the .env file with API keys**
4. **Run agent\.py**
    
🔺 Usage
-----
**Interact via chat**

- This agent is designed to be interacted with through a large language model (LLM)-style chat user interface, enabling natural-language engagement while maintaining strict adherence to predefined command extraction logic. 
.
- Users issue instructions in free-form language, embedding within each message a specific intent (buy, sell, or request analysis), the contract address of the memecoin of interest, and, where applicable, a numerical value denoting the trade amount.
.
- The agent leverages an ASI-1-powered parser to analyze each user message and extract actionable commands in structured JSON format. The expected command structure is inferred from semantic cues and token positions, rather than rigid command syntax. 
.
- Consequently, users can phrase requests conversationally, provided the message contains sufficient context to unambiguously determine the intent, token, and amount.

### ⭕ Interaction Modes

  ####  1. Buy/Sell Commands
 - These must express a trading action **(buy or sell)**, reference a valid Solana token **contract address**, and specify the **amount** either as a direct SOL value (e.g., "0.002 sol") or as number of tokens (e.g 10000 units)

  **Example:**
  ``` This seems like a good time to enter into DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263, buy 0.002 sol worth for a start```

  **Interpretation:**
  ```A buy order for 0.002 SOL targeting token DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263 ```

 #### 2. Analysis Requests
  - These are interpreted when the user poses a question or prompts an evaluation related to a specific token without specifying a trade amount or action. Sentiment-laden phrases like "what's your take on" or "is now a good time to" will trigger an analysis response.

  **Example:**  
  ```Give me your analysis on DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263.```

  **Interpretation:**
  ``` The agent will fetch real-time 15-minute token activity data and return a comprehensive trading analysis, including price action, sentiment, liquidity, and safety score.```

### ➡️ Execution Flow

##### Once the message is interpreted

A command is extracted and parsed in this format:


    {
    "type": "analysis",
    "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "amount": "none"
    }
    
    or

    {
    "type": "buy",
    "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "amount": "0.001"
    }


-----

### 🏛️ File Structure

├── agent.py             # Entrypoint: sets up Agent and protocols
├── chat.py              # LLM parsing & command execution
├── query.py             # Bitquery GraphQL fetch and models
├── helpers.py           # Helper functions
├── README.md            # Project documentation
.

### 🕵️  Detailed Module Descriptions

#### chat\.py

*   **extract\_prompt(token\_info: str)** Sends raw user text to ASI‑1 to extract JSON commands (type, address, amount).
    
*   **get\_analysis\_from\_agent(token\_info: str)** Sends token info to ASI‑1 to generate detailed memecoin analysis and safety score.
    
*   **execute\_command(command: str)** Parses the JSON command and calls PumpPortal’s API to perform buy/sell trades.
    

#### query\.py

*   **TokenRequest / AnalysisResponse** uAgents Model schemas for incoming prompts and outgoing analysis.
    
*   **get\_memecoin\_info\_from\_address(address: str)** Constructs and sends a Bitquery GraphQL query to fetch 15‑min Coin metrics, returning raw JSON.
    

#### agent\.py

*   **Agent Initialization** Creates analysis\_agent, applies QuotaProtocol (30 req/hr).
    
*   **handle\_request**
    
    1.  Receives TokenRequest.
        
    2.  Calls extract\_prompt to determine action.
        
    3.  For "analyze," invokes get\_memecoin\_info\_from\_address and get\_analysis\_from\_agent and for "buy"/"sell" forward to execute command.
        
    4.  Sends back AnalysisResponse or ErrorMessage.
        
    5.  Logs each step and handles exceptions.
        
*   **Protocol Inclusion & Run** Includes chat, structured‑output, and quota protocols, then calls agent.run().
    

👾 Extending the Agent
-------------------

* 📊  **Make improvements to the scoring system**: Mostly by using more data and metrics
    
* 💡  **Additional On‑Chain Metrics**: Enhance query.py to fetch smart‑money activity, holder distribution, top trades, dev buy/sell etc.
    
* 🔗  **X API for trends and general sentiments**: The major factor in memecoin trading in my opinion, **NEWS**. Using X(Twitter) API to get every mention, news, KOL mentions etc. around a memecoin. To determine its sentiment.