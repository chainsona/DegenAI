"""File Description

    This is the core of the agent's chat and executions, it contains the logic for
    receiving and sending text prompts and commands between the user -> agent -> other agents.
"""

# library imports
from datetime import datetime
from uuid import uuid4
from typing import Any
import requests
import json
from uagents import Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
from query import get_memecoin_info_from_address, TokenRequest, AnalysisResponse
from helpers import get_analysis_from_agent, extract_prompt, execute_command

# asi-1 LLM endpoint
ASI1_Endpoint = "https://api.asi1.ai/v1/chat/completions"

headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': f'Bearer {AGENTVERSE_API_KEY}'  # Replace with your agentverse API key
}

class Message(Model):
    message : str
    field : int

class ToLocal(Model):
    message: str


def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

chat_proto = Protocol(spec=chat_protocol_spec)
struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)

class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]

# Handler for incoming ChatMessage instances on the chat_proto protocol
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    # Log the receipt of the message along with the sender's address
    ctx.logger.info(f"Got a message from {sender}: {msg}")
    
    # Store the sender's address in the session storage using the session ID as the key
    ctx.storage.set(str(ctx.session), sender)
    
    # Send an acknowledgment back to the sender to confirm receipt of the message
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.utcnow(),  # Current UTC time
            acknowledged_msg_id=msg.msg_id  # ID of the received message
        ),
    )

    # Iterate through each content item in the received message, 1 in this case: text
    for item in msg.content:
        # Check if the content item indicates the start of a new session
        if isinstance(item, StartSessionContent):
            # Log the initiation of a new session
            ctx.logger.info(f"Got a start session message from {sender}")
            continue  # Move to the next content item

        # Check if the content item is textual
        elif isinstance(item, TextContent):
            # Log the received text message
            ctx.logger.info(f"Got 1 message from {sender}: {item.text}")
            
            # Store the sender's address again in the session storage (may be redundant)
            ctx.storage.set(str(ctx.session), sender)

            try:
                # function to extract command from user prompt on the frontend
                # extracts commands from prompts in this form {"type": "buy", "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "amount": 0.0001}
                command = await extract_prompt(str(item.text))
                data = json.loads(command["choices"][0]["message"]["content"])
                
                #ctx.logger.info(f'{(command["choices"][0]["message"]["content"])}')

                # prompt interpretation is resolved as a buy or sell order, execute order leveraging pumpportal API
                if data["type"] == "buy" or data["type"] == "sell":
                    resp = execute_command(f'{(command["choices"][0]["message"]["content"])}')
                    # on failure
                    if resp['errors'] != []:
                        await ctx.send(sender, create_text_chat(f'{data["type"]} order for {data["address"]}, amount: {data["amount"]} failed with an error. /n Inspect for the error here: https://solscan.io/tx/{resp["signature"]}'))
                    else:
                        # on success return message and solscan tx link
                        await ctx.send(sender, create_text_chat(f'{data["type"]} order for {data["address"]}, amount: {data["amount"]} executed successfully.   /n Transaction: https://solscan.io/tx/{resp["signature"]}'))
                    
                # if user prompts is interpreted by the LLM to indicate a memecoin analysis request:   
                elif data["type"] == "analysis":
                    # get coin data from bitquery api
                    info = await get_memecoin_info_from_address(data["address"])
                    # Our DegenAI gives its expert analysis and score
                    analysis = await get_analysis_from_agent(info)
                    final_analysis = analysis["choices"][0]["message"]["content"]
                    ctx.logger.info(f"Analysis for memecoin with CA {data['address']} completed")
                    # returns the analysis to the user on chat ui
                    await ctx.send(sender, create_text_chat(final_analysis))
                else:
                    ctx.logger.info("I was unable to extract a valid command from your input")
                

            except Exception as e:
                ctx.logger.error(f"Error processing message: {e}")
                await ctx.send(sender, create_text_chat("An error occurred while processing your request. Please try again later."))
        else:
            # Log any unexpected content types received
            ctx.logger.info(f"Got unexpected content from {sender}")

# msg acknowledgement
@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )

@struct_output_client_proto.on_message(StructuredOutputResponse)
async def handle_structured_output_response(
    ctx: Context, sender: str, msg: StructuredOutputResponse
):
    session_sender = ctx.storage.get(str(ctx.session))
    if session_sender is None:
        ctx.logger.error(
            "Discarding message because no session sender found in storage"
        )
        return

    if "<UNKNOWN>" in str(msg.output):
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't process your request. Please include a valid Memecoin contract address."
            ),
        )
        return

    try:
        # Parse the structured output to get the address
        analysis_request = TokenRequest.parse_obj(msg.output)
        contract_address = analysis_request.contract_address
        
        if not contract_address:
            await ctx.send(
                session_sender,
                create_text_chat(
                    "Sorry, I couldn't find a valid Memecoin contract address in your query."
                ),
            )
            return
        
        # Get the analysis for this token
        token_analysis = await get_analysis_from_agent(contract_address)
        
        # Create a nicely formatted response
        response_text = token_analysis

        # Send the response back to the user
        await ctx.send(session_sender, create_text_chat(response_text))
        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't process this request. I Give up"
            ),
        )
        return

