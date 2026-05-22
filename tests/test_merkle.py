import unittest
import hashlib
from part1_tree import MerkleTree, verify_proof, sha256_pair


class TestMerkleTree(unittest.TestCase):
    def test_even_leaves(self):
        leaves = [b"a", b"b", b"c", b"d"]
        tree = MerkleTree(leaves)
        self.assertEqual(len(tree.root), 32)

        h_a = hashlib.sha256(b"a").digest()
        h_b = hashlib.sha256(b"b").digest()
        h_c = hashlib.sha256(b"c").digest()
        h_d = hashlib.sha256(b"d").digest()

        h_ab = sha256_pair(h_a, h_b)
        h_cd = sha256_pair(h_c, h_d)
        expected_root = sha256_pair(h_ab, h_cd)
        self.assertEqual(tree.root, expected_root)

    def test_odd_leaves(self):
        leaves = [b"a", b"b", b"c"]
        tree = MerkleTree(leaves)
        self.assertEqual(len(tree.root), 32)

        proof = tree.get_proof(2)
        self.assertTrue(verify_proof(b"c", proof, tree.root))

    def test_single_leaf(self):
        leaves = [b"a"]
        tree = MerkleTree(leaves)
        expected_root = hashlib.sha256(b"a").digest()
        self.assertEqual(tree.root, expected_root)

    def test_proof_generation(self):
        leaves = [b"a", b"b", b"c", b"d"]
        tree = MerkleTree(leaves)
        for i, leaf in enumerate(leaves):
            proof = tree.get_proof(i)
            self.assertTrue(verify_proof(leaf, proof, tree.root))

    def test_tampered_data_fails(self):
        leaves = [b"a", b"b", b"c", b"d"]
        tree = MerkleTree(leaves)
        proof = tree.get_proof(0)
        self.assertFalse(verify_proof(b"x", proof, tree.root))

    def test_tampered_proof_fails(self):
        leaves = [b"a", b"b", b"c", b"d"]
        tree = MerkleTree(leaves)
        proof = tree.get_proof(0)
        proof[0]["hash"] = b"\x00" * 32
        self.assertFalse(verify_proof(b"a", proof, tree.root))

    def test_empty_leaves_raises(self):
        with self.assertRaises(ValueError):
            MerkleTree([])

    def test_index_out_of_bounds_raises(self):
        leaves = [b"a", b"b", b"c", b"d"]
        tree = MerkleTree(leaves)
        with self.assertRaises(IndexError):
            tree.get_proof(-1)
        with self.assertRaises(IndexError):
            tree.get_proof(4)

    def test_large_tree(self):
        leaves = [str(i).encode() for i in range(100)]
        tree = MerkleTree(leaves)
        proof_37 = tree.get_proof(37)
        self.assertTrue(verify_proof(b"37", proof_37, tree.root))
        proof_99 = tree.get_proof(99)
        self.assertTrue(verify_proof(b"99", proof_99, tree.root))

    def test_odd_number_six_leaves(self):
        # 5 is odd — the last leaf must be duplicated before pairing
        leaves = [b"a", b"b", b"c", b"d", b"e"]
        tree = MerkleTree(leaves)
        self.assertEqual(len(tree.root), 32)
        # Verify proof for the last leaf (index 4) which triggered duplication
        proof = tree.get_proof(4)
        self.assertTrue(verify_proof(b"e", proof, tree.root))
        # The padded ghost index must not be reachable
        with self.assertRaises(IndexError):
            tree.get_proof(5)


if __name__ == "__main__":
    unittest.main()
