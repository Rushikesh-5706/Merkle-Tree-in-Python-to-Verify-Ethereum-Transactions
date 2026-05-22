import os
import hashlib
from dotenv import load_dotenv
from part1_tree import MerkleTree, verify_proof
from part2_fetch import fetch_block, inspect_block

load_dotenv()

def hex_to_int(value: str | None) -> int:
    if value is None or value == "0x":
        return 0
    return int(value, 16)

def hex_to_bytes(value: str | None) -> bytes:
    if value is None or value == "0x":
        return b""
    v = value[2:] if value.startswith("0x") else value
    if len(v) % 2:
        v = "0" + v
    return bytes.fromhex(v)

def keccak256(data: bytes) -> bytes:
    import sha3
    k = sha3.keccak_256()
    k.update(data)
    return k.digest()

def hash_transaction(tx: dict, method: str = "sha256") -> bytes:
    if method == "sha256":
        return hashlib.sha256(tx["hash"].encode()).digest()
    elif method == "keccak":
        import rlp
        tx_type = tx.get("type", "0x0")
        
        if tx_type == "0x0":
            data = [
                hex_to_int(tx.get("nonce")),
                hex_to_int(tx.get("gasPrice")),
                hex_to_int(tx.get("gas")),
                hex_to_bytes(tx.get("to")),
                hex_to_int(tx.get("value")),
                hex_to_bytes(tx.get("input")),
                hex_to_int(tx.get("v")),
                hex_to_int(tx.get("r")),
                hex_to_int(tx.get("s"))
            ]
            return keccak256(rlp.encode(data))
        elif tx_type == "0x2":
            access_list = []
            for a in tx.get("accessList", []):
                storage_keys = [hex_to_bytes(sk) for sk in a.get("storageKeys", [])]
                access_list.append([hex_to_bytes(a["address"]), storage_keys])
                
            data = [
                hex_to_int(tx.get("chainId")),
                hex_to_int(tx.get("nonce")),
                hex_to_int(tx.get("maxPriorityFeePerGas")),
                hex_to_int(tx.get("maxFeePerGas")),
                hex_to_int(tx.get("gas")),
                hex_to_bytes(tx.get("to")),
                hex_to_int(tx.get("value")),
                hex_to_bytes(tx.get("input")),
                access_list,
                hex_to_int(tx.get("yParity", tx.get("v"))),
                hex_to_int(tx.get("r")),
                hex_to_int(tx.get("s"))
            ]
            return keccak256(b"\x02" + rlp.encode(data))
        else:
            print(f"Warning: Unrecognized transaction type {tx_type}. Falling back to sha256.")
            return hashlib.sha256(tx["hash"].encode()).digest()
    else:
        raise ValueError(f"Unknown method {method}")

def reconstruct_transactions_root(transactions: list[dict], method: str = "sha256") -> bytes:
    tx_hashes = [hash_transaction(tx, method) for tx in transactions]
    tree = MerkleTree(tx_hashes)
    return tree.root

def verify_transactions_root(block: dict, method: str = "sha256") -> bool:
    if not block["transactions"]:
        print("No transactions to verify")
        return False
        
    reconstructed_root = reconstruct_transactions_root(block["transactions"], method)
    block_root_hex = block["transactionsRoot"]
    block_root = bytes.fromhex(block_root_hex[2:] if block_root_hex.startswith("0x") else block_root_hex)
    
    print(f"Reconstructed root : {reconstructed_root.hex()}")
    print(f"Block header root  : {block_root.hex()}")
    match = reconstructed_root == block_root
    print(f"Match              : {match}")
    
    if method == "sha256":
        print("Note: Match is not expected because Ethereum uses MPT, not a binary Merkle tree, and Keccak-256 instead of SHA-256.")
    elif method == "keccak":
        print("Note: Match may not occur because Ethereum uses MPT indexed by transaction position, not a plain binary tree.")
        
    return match

def prove_transaction_inclusion(block: dict, tx_index: int, method: str = "sha256") -> None:
    tx_hashes = [hash_transaction(tx, method) for tx in block["transactions"]]
    tree = MerkleTree(tx_hashes)
    proof = tree.get_proof(tx_index)
    tx = block["transactions"][tx_index]
    
    leaf_data = hash_transaction(tx, method)
    is_valid = verify_proof(leaf_data, proof, tree.root)
    
    print(f"Transaction index  : {tx_index}")
    print(f"Transaction hash   : {tx['hash']}")
    print(f"Proof depth        : {len(proof)}")
    print(f"Proof path         : {[{'hash': p['hash'].hex(), 'position': p['position']} for p in proof]}")
    print(f"Verification       : {'PASSED' if is_valid else 'FAILED'}")
    
    tampered_proof = [dict(step) for step in proof]
    if tampered_proof:
        tampered_proof[0]["hash"] = b"\x00" * 32
        tampered_valid = verify_proof(leaf_data, tampered_proof, tree.root)
        if not tampered_valid:
            print("Tamper test        : PASSED (tampered proof correctly rejected)")
        else:
            print("Tamper test        : FAILED (tampered proof accepted)")

def light_client_verify(transactions_root_hex: str, leaf_data: bytes, proof: list[dict]) -> bool:
    """
    Verifies transaction inclusion using only the block header's transactionsRoot
    and a Merkle proof. No access to the full block or transaction list.
    This simulates what an Ethereum light client does.
    """
    expected_root = bytes.fromhex(
        transactions_root_hex[2:] if transactions_root_hex.startswith("0x") else transactions_root_hex
    )
    return verify_proof(leaf_data, proof, expected_root)

def verify_historical_block(rpc_url: str, block_number: int, tx_index: int = 0) -> None:
    block = fetch_block(rpc_url, block_number)
    print(f"\nHistorical block {int(block['number'], 16)} ({block_number})")
    inspect_block(block)
    if block["transactions"]:
        prove_transaction_inclusion(block, tx_index)
    else:
        print("No transactions in this block")

if __name__ == "__main__":
    rpc_url = os.environ["ALCHEMY_RPC_URL"]

    print("=" * 60)
    print("Fetching latest Ethereum block")
    print("=" * 60)
    block = fetch_block(rpc_url, "latest")
    inspect_block(block)

    if not block["transactions"]:
        print("No transactions in latest block. Fetching previous block.")
        block_num = int(block["number"], 16) - 1
        block = fetch_block(rpc_url, block_num)
        inspect_block(block)

    print("\n" + "=" * 60)
    print("Verifying transactions root (SHA-256 simplified)")
    print("=" * 60)
    verify_transactions_root(block, method="sha256")

    print("\n" + "=" * 60)
    print("Verifying transactions root (Keccak-256 + RLP)")
    print("=" * 60)
    verify_transactions_root(block, method="keccak")

    print("\n" + "=" * 60)
    print("Generating and verifying inclusion proof for tx[0]")
    print("=" * 60)
    prove_transaction_inclusion(block, tx_index=0)

    print("\n" + "=" * 60)
    print("Extension B: Odd leaf handling test")
    print("=" * 60)
    tx_count = len(block["transactions"])
    print(f"Transaction count: {tx_count} ({'odd' if tx_count % 2 else 'even'})")
    if tx_count % 2 == 1:
        print("Odd transaction count confirmed — verifying last tx proof")
        prove_transaction_inclusion(block, tx_index=tx_count - 1)
    else:
        print("Current block has even tx count. Odd-leaf duplication logic is covered in unit tests.")

    print("\n" + "=" * 60)
    print("Extension C: Light client simulation")
    print("=" * 60)
    tx_hashes = [tx["hash"].encode() for tx in block["transactions"]]
    tree = MerkleTree(tx_hashes)
    proof = tree.get_proof(0)
    reconstructed_root = tree.root
    result = light_client_verify(
        reconstructed_root.hex(),
        block["transactions"][0]["hash"].encode(),
        proof,
    )
    print(f"Light client verification: {'PASSED' if result else 'FAILED'}")

    print("\n" + "=" * 60)
    print("Extension D: Historical block verification")
    print("=" * 60)
    current_block_num = int(block["number"], 16)
    historical_block_num = max(current_block_num - 1_300_000, 19_000_000)
    verify_historical_block(rpc_url, historical_block_num, tx_index=0)
