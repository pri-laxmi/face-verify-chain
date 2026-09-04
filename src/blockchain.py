"""
blockchain.py
-------------
Step 3 of the pipeline: a small, dependency-free simulated blockchain
used to create a tamper-evident, re-verifiable record of a discovered
web/social media post.

Design:
  - Each Block stores: index, timestamp, data (the post fingerprint +
    metadata), previous_hash, nonce, and its own hash.
  - Blocks are mined with a simple proof-of-work (find a nonce so the
    block's hash starts with N leading zeros). This is intentionally
    lightweight -- the point is to demonstrate the tamper-evidence
    property, not to build a production consensus system.
  - The chain is persisted to a JSON file on disk (data/chain.json)
    so records survive between runs.
  - verify_record() re-hashes a piece of data and checks it against
    what's stored on-chain, proving the data hasn't been altered since
    it was recorded.

This satisfies the assignment's "any blockchain may be used, including
a local/simulated chain" allowance. See README.md for how to swap this
out for a real testnet (e.g. Ethereum Sepolia via web3.py) if desired.
"""

import hashlib
import json
import time
import os

DEFAULT_CHAIN_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chain.json")
DIFFICULTY = 3  # number of leading zeros required in a block's hash


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fingerprint_data(data: dict) -> str:
    """Deterministically hash a dict of post data (image/text/metadata)."""
    canonical = json.dumps(data, sort_keys=True)
    return sha256(canonical)


class Block:
    def __init__(self, index, timestamp, data, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }, sort_keys=True)
        return sha256(block_string)

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @staticmethod
    def from_dict(d):
        b = Block(d["index"], d["timestamp"], d["data"], d["previous_hash"], d["nonce"])
        b.hash = d["hash"]  # trust stored hash; verify() will catch tampering
        return b


class SimulatedChain:
    def __init__(self, path: str = DEFAULT_CHAIN_PATH):
        self.path = path
        self.chain = []
        self._load_or_genesis()

    def _load_or_genesis(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                raw = json.load(f)
            self.chain = [Block.from_dict(b) for b in raw]
        else:
            genesis = Block(0, time.time(), {"note": "genesis block"}, "0" * 64)
            genesis.hash = self._mine(genesis)
            self.chain = [genesis]
            self._save()

    def _mine(self, block: Block) -> str:
        block.nonce = 0
        h = block.compute_hash()
        while not h.startswith("0" * DIFFICULTY):
            block.nonce += 1
            h = block.compute_hash()
        return h

    def _save(self):
        with open(self.path, "w") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=2)

    def add_record(self, data: dict) -> Block:
        """Mine and append a new block containing `data`. Returns the block."""
        last = self.chain[-1]
        new_block = Block(
            index=last.index + 1,
            timestamp=time.time(),
            data=data,
            previous_hash=last.hash,
        )
        new_block.hash = self._mine(new_block)
        self.chain.append(new_block)
        self._save()
        return new_block

    def is_valid(self) -> bool:
        """Walk the whole chain and confirm hashes/links haven't been tampered with."""
        for i in range(1, len(self.chain)):
            current, previous = self.chain[i], self.chain[i - 1]
            if current.previous_hash != previous.hash:
                return False
            if current.hash != current.compute_hash():
                return False
            if not current.hash.startswith("0" * DIFFICULTY):
                return False
        return True

    def get_block(self, index: int) -> Block:
        return self.chain[index]

    def verify_record(self, index: int, data: dict) -> bool:
        """
        Re-verify: does the given data (e.g. a freshly re-fetched post's
        fingerprint) match what's stored on-chain at `index`, and is the
        chain itself untampered?
        """
        if not self.is_valid():
            return False
        block = self.get_block(index)
        return block.data == data


if __name__ == "__main__":
    chain = SimulatedChain()
    demo_record = {
        "type": "demo",
        "content_hash": fingerprint_data({"hello": "world"}),
    }
    block = chain.add_record(demo_record)
    print(f"Added block #{block.index}, hash={block.hash}")
    print("Chain valid:", chain.is_valid())
    print("Re-verify matches:", chain.verify_record(block.index, demo_record))
