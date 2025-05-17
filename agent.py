

""" File Description

    This module wires together three protocols into a single “analysis” agent that listens for incoming token‑analysis 
    requests, enforces rate limits, parses user commands (buy, sell, analyze), fetches on‑chain data via Bitquery when asked 
    to analyze, invokes the ASI‑1 LLM for deep memecoin insights, and then replies with either an AnalysisResponse or an 
    ErrorMessage. It does the following in sequence: (1) instantiates a base Agent, (2) applies a QuotaProtocol to throttle 
    to 30 requests/hour, (3) handles TokenRequest messages by extracting the intent, (4) if the intent is “analyze” it 
    retrieves token metrics and AI analysis, (5) logs each step, and (6) includes the chat and structured‑output protocols 
    before running the agent.
"""

# import neccesary dependencies
from uagents import Agent, Context, Model
from uagents.experimental.quota import QuotaProtocol, RateLimit
from uagents_core.models import ErrorMessage
from query import TokenRequest, AnalysisResponse, get_memecoin_info_from_address
from chat import chat_proto, struct_output_client_proto, get_analysis_from_agent

# new agent instance
analysis_agent = Agent()

proto = QuotaProtocol(
    storage_reference=analysis_agent.storage,
    name="Solana-Wallet-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=30),
)

@proto.on_message(
    TokenRequest, replies={AnalysisResponse, ErrorMessage}
)
async def handle_request(ctx: Context, sender: str, msg: TokenRequest):
    ctx.logger.info(f"Received token analysis request for CA: {msg.prompt}")
    try:
        command = extract_prompt(msg.prompt)
        data = json.loads(command)

        if data["type"] == "buy" | data["type"] == "sell":
            ##
            ctx.logger(data["type"])
        elif data["type"] == "analyze":
            info = await get_memecoin_info_from_address(msg.contract_address)
            analysis = await get_analysis_from_agent(info)
        else:
            ctx.logger("I was unable to extract a valid command from your input")
        
        final_analysis = analysis["choices"][0]["message"]["content"]
        ctx.logger.info(f"Analysis for memecoin with CA {msg.contract_address} completed")
        await ctx.send(sender, AnalysisResponse(analysis=final_analysis))
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(sender, ErrorMessage(error=str(err)))

analysis_agent.include(proto, publish_manifest=True)
analysis_agent.include(chat_proto, publish_manifest=True)
analysis_agent.include(struct_output_client_proto, publish_manifest=True)

if __name__ == "__main__":
    analysis_agent.run()