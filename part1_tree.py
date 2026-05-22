from __future__ import annotations
import hashlib
from dataclasses import dataclass


def sha256_pair(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(left + right).digest()


@dataclass
class MerkleNode:
    hash: bytes
    left: MerkleNode | None = None
    right: MerkleNode | None = None


class MerkleTree:
    def __init__(self, leaves: list[bytes]):
        if not leaves:
            raise ValueError("leaves cannot be empty")

        self._leaf_count = len(leaves)
        leaf_hashes = [hashlib.sha256(leaf).digest() for leaf in leaves]
        self._levels: list[list[bytes]] = []
        self._build_levels(leaf_hashes)

    @property
    def root(self) -> bytes:
        return self._levels[-1][0]

    def _build_levels(self, leaf_hashes: list[bytes]) -> None:
        current = list(leaf_hashes)
        self._levels.append(current)

        while len(current) > 1:
            if len(current) % 2 == 1:
                current = current + [current[-1]]
                self._levels[-1] = current
            next_level = [
                sha256_pair(current[i], current[i + 1])
                for i in range(0, len(current), 2)
            ]
            self._levels.append(next_level)
            current = next_level

    def get_proof(self, index: int) -> list[dict]:
        if index < 0 or index >= self._leaf_count:
            raise IndexError(f"index {index} out of range for tree with {self._leaf_count} leaves")

        proof = []
        current_index = index

        for level in self._levels[:-1]:
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                position = "right"
            else:
                sibling_index = current_index - 1
                position = "left"

            proof.append({"hash": level[sibling_index], "position": position})
            current_index //= 2

        return proof


def verify_proof(leaf_data: bytes, proof: list[dict], expected_root: bytes) -> bool:
    current = hashlib.sha256(leaf_data).digest()
    for step in proof:
        if step["position"] == "left":
            current = sha256_pair(step["hash"], current)
        else:
            current = sha256_pair(current, step["hash"])
    return current == expected_root


if __name__ == "__main__":
    items = [b"alice", b"bob", b"carol", b"dave"]
    tree = MerkleTree(items)

    proof = tree.get_proof(2)
    assert verify_proof(b"carol", proof, tree.root), "Valid proof failed"
    assert not verify_proof(b"mallory", proof, tree.root), "Tampered data passed"

    tampered = [dict(step) for step in proof]
    tampered[0] = {"hash": b"\x00" * 32, "position": tampered[0]["position"]}
    assert not verify_proof(b"carol", tampered, tree.root), "Tampered proof passed"

    odd_tree = MerkleTree([b"x", b"y", b"z"])
    odd_proof = odd_tree.get_proof(2)
    assert verify_proof(b"z", odd_proof, odd_tree.root), "Odd tree proof failed"

    try:
        odd_tree.get_proof(3)
        raise AssertionError("Expected IndexError for ghost index on 3-leaf tree")
    except IndexError:
        pass

    print("Part 1: all assertions passed")
    print(f"Root: {tree.root.hex()}")
    print(f"Proof for 'carol': {[{'hash': s['hash'].hex(), 'position': s['position']} for s in proof]}")
