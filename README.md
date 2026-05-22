# Merkle Tree in Python to Verify Ethereum Transactions

A binary Merkle tree built from scratch in Python, connected to the live Ethereum mainnet.
Fetches real blocks via Alchemy's JSON-RPC, hashes transactions with both SHA-256 and Keccak-256,
generates inclusion proofs, and verifies them without accessing the full block. Covers all four
extension challenges: RLP encoding, odd-leaf handling, light client simulation, and historical
block verification.

## Architecture

```
                        ┌─────────────────────────────────┐
                        │         Ethereum Node           │
                        │       (Alchemy RPC)             │
                        └──────────────┬──────────────────┘
                                       │ eth_getBlockByNumber
                                       ▼
                        ┌─────────────────────────────────┐
                        │         part2_fetch.py          │
                        │   fetch_block / inspect_block   │
                        └──────────────┬──────────────────┘
                                       │ raw transactions[]
                                       ▼
                        ┌─────────────────────────────────┐
                        │         part3_verify.py         │
                        │   hash_transaction (SHA256/     │
                        │   Keccak+RLP) per transaction   │
                        └──────────────┬──────────────────┘
                                       │ leaf hashes[]
                                       ▼
                        ┌─────────────────────────────────┐
                        │         part1_tree.py           │
                        │         MerkleTree              │
                        │                                 │
                        │  leaf0  leaf1  leaf2  leaf3     │
                        │    \   /         \   /          │
                        │   node01        node23          │
                        │       \         /               │
                        │           root                  │
                        └──────────────┬──────────────────┘
                                       │
                          ┌────────────┴────────────┐
                          │                         │
                   get_proof(i)            verify_proof(data,
                          │                proof, root)
                          ▼                         ▼
                   proof path              True / False
```

## Project Structure

```
merkle-ethereum/
├── part1_tree.py       Core Merkle tree implementation
├── part2_fetch.py      Ethereum RPC interaction
├── part3_verify.py     End-to-end verification, all extensions
├── main.py             Orchestration entry point
├── tests/
│   ├── conftest.py     Pytest path setup
│   └── test_merkle.py  Unit tests for tree logic
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| requests | 2.31+ |
| rlp | 3.0+ |
| safe-pysha3 | 1.0.2+ |
| python-dotenv | 1.0+ |
| pytest | 7.0+ |
| Docker | 20.10+ |
| docker-compose | 2.0+ |

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your Alchemy RPC URL
3. Install dependencies: `pip install -r requirements.txt`
4. Run the tests: `python -m pytest tests/ -v`
5. Run each part individually: `python part1_tree.py`, `python part2_fetch.py`, `python part3_verify.py`
6. Run the full pipeline: `python main.py`

## Docker Usage

```bash
# Build and run
docker-compose up --build

# Or build manually
docker build -t rushi5706/merkle-ethereum:latest .
docker run --env-file .env rushi5706/merkle-ethereum:latest
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| ALCHEMY_RPC_URL | Yes | Ethereum mainnet JSON-RPC endpoint from Alchemy |

See `.env.example` for the format.

## Core Concepts

| Concept | Definition |
|---|---|
| Merkle root | SHA-256 hash at the top of the tree committing to all leaf data |
| Leaf node | Hash of a raw data item (transaction) |
| Internal node | Hash of two children concatenated |
| Merkle proof | Sibling hashes from leaf to root sufficient to recompute the root |
| transactionsRoot | The Merkle root stored in the Ethereum block header |
| RLP | Recursive Length Prefix — Ethereum's binary serialization format |
| Keccak-256 | Ethereum's hash function (distinct from NIST SHA3-256) |
| MPT | Merkle Patricia Trie — Ethereum's actual transaction index structure |

## Implementation Notes

The reconstructed root using the SHA-256 method will not match the block header's `transactionsRoot`. This is expected because standard binary Merkle trees pair adjacent leaves, whereas Ethereum uses a Merkle Patricia Trie (MPT) indexed by the transaction's position in the block. Additionally, Ethereum uses the Keccak-256 hash function rather than NIST SHA-256.

Extension A introduces the Keccak-256 hash function and Ethereum's Recursive Length Prefix (RLP) serialization for transactions. While this accurately recreates the leaf hashes as they appear in Ethereum, the final root will still not match the header's root without a full MPT implementation to structure the tree nodes correctly.

Extension C simulates a light client verifying a transaction. It demonstrates that a node does not need to download the full block or all transactions to verify inclusion. Given the header's `transactionsRoot` and a Merkle proof provided by a full node, the light client can cryptographically confirm the transaction's presence.

Extension D demonstrates the immutability of historical data. By fetching a block from six months ago and verifying a transaction against its header, it shows that the on-chain root from the past can reliably prove the inclusion of past transactions without retaining the entire historical block data.

## Running Extensions

| Extension | Description | How to run |
|---|---|---|
| A | Keccak-256 + RLP transaction hashing | Runs automatically in part3_verify.py |
| B | Odd leaf count handling | Triggered automatically if block has odd tx count |
| C | Light client simulation | Runs automatically in part3_verify.py |
| D | Historical block verification | Runs automatically in part3_verify.py |

## Testing

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run with coverage (if coverage is installed)
python -m pytest tests/ --cov=. --cov-report=term-missing
```

| Test | Covers |
|---|---|
| test_even_leaves | Basic tree construction with 4 leaves |
| test_odd_leaves | Odd-leaf duplication with 3 leaves |
| test_single_leaf | Single-element tree edge case |
| test_proof_generation | Proof validity for all indices in a 4-leaf tree |
| test_tampered_data_fails | Data integrity — wrong leaf rejected |
| test_tampered_proof_fails | Proof integrity — zeroed sibling hash rejected |
| test_empty_leaves_raises | ValueError on empty input |
| test_index_out_of_bounds_raises | IndexError on invalid proof index |
| test_large_tree | Correctness at scale with 100 leaves |
| test_odd_number_six_leaves | Odd duplication with 5 leaves, ghost index rejection |
