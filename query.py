""" File Description

    This module defines a data model and a GraphQL‑based fetcher for retrieving 15‑minute (I decided on 15 minutes due to
    experience trading these coins and how volatile they can be, and after testing with 5, 30 and 1hour. 15 seemed to give the 
    most accurate analysis and predictions ) trading metrics on a given Solana memecoin from Bitquery, then returns the raw JSON (or an error message) for downstream 
    analysis; it sets up structured request/response schemas (TokenRequest and AnalysisResponse), constructs 
    a parameterized query that grabs price, trade counts, volumes (buys vs. sells), unique maker/buyer/seller counts, 
    and quantiles, and handles HTTP calls with logging, error catching, and RFC‑3339 timestamping.
"""

import requests
import os
import logging
import json
import datetime
from uagents import Model, Field

#logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# bitquery endpoint for fetching memecoin data
GRAPHQL_ENDPOINT = "https://streaming.bitquery.io/eap"


class TokenRequest(Model):
    prompt: str = Field(
        description="Command from user",
    )

class AnalysisResponse(Model):
    analysis: str = Field(
        description="Expert Agent Response",
    )

# function to fetch and return memecoin data from bitquery
async def get_memecoin_info_from_address(address: str) -> str:
    """
    Get info for a memecoin token using Bitquery
    
    Args:
        address: Memecoin address
        
    Returns:
        Formatted response string
    """
    

    try:
        logger.info(f"Getting info for token: {address}")

        headers = {
            'Content-Type': 'application/json',
            'Authorization': BITQUERY_API_KEY
        }


        query = """
            query MyQuery($token: String!, $time_15min_ago: DateTime!) {
                Solana(dataset: realtime) {
                    DEXTradeByTokens(
                    where: {Transaction: {Result: {Success: true}}, Trade: {Currency: {MintAddress: {is: $token}}, Market: {MarketAddress: {}}}, Block: {Time: {since: $time_15min_ago}}}
                    limit: {count: 1}
                    ) {
                    Trade {
                        Currency {
                        Name
                        MintAddress
                        Symbol
                        }
                        start: PriceInUSD(minimum: Block_Time)
                        end: PriceInUSD(maximum: Block_Time)
                    }
                    makers_15min: count(
                        distinct: Transaction_Signer
                        if: {Block: {Time: {after: $time_15min_ago}}}
                    )
                    buyers_15min: count(
                        distinct: Transaction_Signer
                        if: {Trade: {Side: {Type: {is: buy}}}, Block: {Time: {after: $time_15min_ago}}}
                    )
                    sellers_15min: count(
                        distinct: Transaction_Signer
                        if: {Trade: {Side: {Type: {is: sell}}}, Block: {Time: {after: $time_15min_ago}}}
                    )
                    trades_15min: count(if: {Block: {Time: {after: $time_15min_ago}}})
                    traded_volume_15min: sum(
                        of: Trade_Side_AmountInUSD
                        if: {Block: {Time: {after: $time_15min_ago}}}
                    )
                    buy_volume_15min: sum(
                        of: Trade_Side_AmountInUSD
                        if: {Trade: {Side: {Type: {is: buy}}}, Block: {Time: {after: $time_15min_ago}}}
                    )
                    sell_volume_15min: sum(
                        of: Trade_Side_AmountInUSD
                        if: {Trade: {Side: {Type: {is: sell}}}, Block: {Time: {after: $time_15min_ago}}}
                    )
                    buys_15min: count(
                        if: {Trade: {Side: {Type: {is: buy}}}, Block: {Time: {after: $time_15min_ago}}}
                    )
                    sells_15min: count(
                        if: {Trade: {Side: {Type: {is: sell}}}, Block: {Time: {after: $time_15min_ago}}}
                    )
                    price_15min_allTimeHigh: quantile(of: Trade_PriceInUSD, level: 0.99)
                    }
                }
                }

        """

        time_15_minutes_ago = (datetime.datetime.now() - datetime.timedelta(minutes=15)).replace(microsecond=0).isoformat() + "Z"

        variables = {
            "token": address,
            "time_15min_ago": time_15_minutes_ago
        }

        response = requests.post(GRAPHQL_ENDPOINT, json={"query": query, "variables": variables}, headers=headers)

        if response.status_code == 200:
            json_data = response.text
            return json_data
        else:
            print(f"Error: {response.status_code}, {response.text}")

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return error_msg
