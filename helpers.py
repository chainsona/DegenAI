"""File Description
    This is a helper module which defines two asynchronous functions —> extract_prompt and get_analysis_from_agent—that
    send user input to Fetch.ai’s ASI‑1 API with different system prompts (one to parse commands into JSON,
    the other to generate a detailed memecoin analysis), then a synchronous execute_command function that reads 
    that JSON, determines if it’s a buy or sell order, and if so calls PumpPortal’s trading API to execute the trade; 
    overall, it bridges user‑friendly prompts, LLM‑driven parsing and analysis, and on‑chain trading into a single 
    automated workflow.
"""

import requests
import json

ASI1_Endpoint = "https://api.asi1.ai/v1/chat/completions"
apikey = PUMP_PORTAL_API_KEY


headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': f'Bearer {AGENTVERSE_API_KEY}'  # agentverse api key; stored in agent secrets
}


async def extract_prompt(token_info: str):
    payload = json.dumps({
        "model": "asi1-mini",
        "messages": [
            {
            "role": "system",
            "content": """
                    You are a hyper-efficient Solana transaction parser that ruthlessly extracts token addresses and actions from user messages with machine-like precision.
                     Your sole purpose is to convert casual crypto chatter into structured JSON output—no explanations, no pleasantries, just cold, surgical extraction.
                      When users mention tokens, you instantly identify base58 addresses and categorize intent (analysis/buy/sell) with 100% accuracy, always responding in the exact specified JSON format.
                       You ignore all irrelevant text and never deviate from the output schema—addresses must be case-perfect, amounts precisely quantified, and errors returned only when absolutely necessary.
                        No emojis, no markdown, just raw structured data ready for API consumption.
                        
                        Your replies should only be in the format: {"type": "buy|sell|analyze", "address": "token_address", "amount": amount}
                        
                        If you cant extract this perfectly from a user's prompt then say you could not extract any commands and that's all.
                        
                        example: if the user says buy 0.1sol worth of fNtHtsFz24kTUWUxS7wQJQnN8eQ37CcucaSkbA5pump. return:
                        {
                             "type": "buy",
                              "address": "fNtHtsFz24kTUWUxS7wQJQnN8eQ37CcucaSkbA5pump"
                              "amount": 0.1
                        }.
                        
                        or if the user says sell half of or 50% of fNtHtsFz24kTUWUxS7wQJQnN8eQ37CcucaSkbA5pump. return:
                        {
                             "type": "sell",
                              "address": "fNtHtsFz24kTUWUxS7wQJQnN8eQ37CcucaSkbA5pump"
                              "amount": 50
                        }.
                        
                        or if the user says provide an analysis or whats your take on, or is now a good time to buy or sell
                        fNtHtsFz24kTUWUxS7wQJQnN8eQ37CcucaSkbA5pump. If its structured as a question return:
                        {
                             "type": "analysis",
                              "address": "fNtHtsFz24kTUWUxS7wQJQnN8eQ37CcucaSkbA5pump",
                              "amount": "none"
                        }.

            """
            },
            {
            "role": "user",
            "content": f"{token_info}"
            }
        ],
        "temperature": 0.2,
        "stream": False,
        "max_tokens": 5000
    })

    response = requests.request("POST", ASI1_Endpoint, headers=headers, data=payload)

    return response.json()


async def get_analysis_from_agent(token_info: str):
    payload = json.dumps({
        "model": "asi1-mini",
        "messages": [
            {
            "role": "system",
            "content": """
                    You are DEGEN‑ALPHA PRO, a ruthless Solana memecoin strategist who analyzes each token’s latest 15‑minute DEX
                    and on‑chain data and returns a detailed Markdown briefing with these sections: Summary, 15m Price Action,
                    Volume & Liquidity, Order Flow & Sentiment, Technical Outlook, and Risk & Strategy. You must use plenty of 
                    emojis to enhance readability and speak in full sentences like a crypto expert without resorting to three‑word commands
                    or terse bullet points. Be as specific as possible by referencing key metrics (e.g., buy‑sell delta, slippage rates)
                    and explain why each matters to a 15‑minute scalp 📊🔍. Also, always output price in this manner: price(marketcap) for example $0.001(1m market cap),
                    Assume every new token is a rug until it proves profitable, and close with a bold three‑word trade command (e.g., “Scale In Now”) 🚀🔒. Lastly give each token
                    a score from 1-10 based on how safe it is to buy the coin, you must consider every available informatio about that coin before
                    giving it a well thought out score. 
            """
            },
            {
            "role": "user",
            "content": f"{token_info}"
            }
        ],
        "temperature": 0.2,
        "stream": False,
        "max_tokens": 5000
    })

    response = requests.request("POST", ASI1_Endpoint, headers=headers, data=payload)
    return response.json()


def execute_command(command:str):
    data = json.loads(command)

    if data["type"] == "buy" or data["type"] == "sell":
        order_type = data["type"]
        amount = data["amount"]
        address = data["address"]
        denominatedInSol = "true" if order_type=="buy" else "false"

        response = requests.post(url=f"https://pumpportal.fun/api/trade?api-key={apikey}", data={
            "action": order_type,  # "buy" or "sell"
            "mint": address,  # contract address of the token you want to trade
            "amount": amount,  # amount of SOL or tokens to trade
            "denominatedInSol": denominatedInSol,  # "true" if amount is amount of SOL, "false" if amount is number of tokens
            "slippage": 10,  # percent slippage allowed
            "priorityFee": 0.0000,  # amount used to enhance transaction speed
            "pool": "auto"  # exchange to trade on. "pump", "raydium", "pump-amm", "launchlab", "raydium-cpmm" or "auto"
        })
        
        resp = response.json()  # Tx signature or error(s)
        return resp
    else:
        print("we encountered an error")