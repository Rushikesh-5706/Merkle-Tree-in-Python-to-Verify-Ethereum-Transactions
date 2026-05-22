import os
import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_block(rpc_url: str, block_number: int | str = "latest") -> dict:
    block_tag = hex(block_number) if isinstance(block_number, int) else block_number
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [block_tag, True],
        "id": 1
    }
    response = requests.post(rpc_url, json=payload).json()
    
    if "error" in response:
        raise RuntimeError(response["error"].get("message", "RPC Error"))
        
    result = response.get("result")
    if result is None:
        raise ValueError("block not found")
        
    return result

def fetch_transaction_proof(rpc_url: str, tx_hash: str) -> dict:
    # Ethereum's actual transaction trie proofs require MPT traversal and are not natively exposed via standard JSON-RPC
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionByHash",
        "params": [tx_hash],
        "id": 1
    }
    response = requests.post(rpc_url, json=payload).json()
    
    if "error" in response:
        raise RuntimeError(response["error"].get("message", "RPC Error"))
        
    result = response.get("result")
    if result is None:
        raise ValueError("transaction not found")
        
    return result

def inspect_block(block: dict) -> None:
    print(f"Block Number      : {int(block['number'], 16)}")
    print(f"Timestamp         : {int(block['timestamp'], 16)}")
    print(f"Transaction Count : {len(block['transactions'])}")
    print(f"Transactions Root : {block['transactionsRoot']}")
    print(f"Miner/Validator   : {block['miner']}")
    print(f"Gas Used          : {int(block['gasUsed'], 16)} / {int(block['gasLimit'], 16)}")

if __name__ == "__main__":
    rpc_url = os.environ["ALCHEMY_RPC_URL"]
    block = fetch_block(rpc_url, "latest")
    inspect_block(block)
    if block["transactions"]:
        tx = fetch_transaction_proof(rpc_url, block["transactions"][0]["hash"])
        print(f"\nFirst transaction index: {int(tx['transactionIndex'], 16)}")
        print(f"From: {tx['from']}")
        print(f"To:   {tx['to']}")
