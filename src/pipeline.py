"""
pipeline.py
-----------
End-to-end orchestration:
  1. face_id.py       -> detect + encode the face in the input scan
  2. web_search.py     -> genuinely search the web for a matching post
  3. blockchain.py     -> fingerprint the discovered post and record it
                           on the simulated chain, then re-verify it

Usage:
    python src/pipeline.py path/to/face_scan.jpg

Requires environment variables IMGBB_API_KEY and SERPAPI_API_KEY
(see README.md for setup). Only run this on images you have the
right to search (your own photo, or a consenting volunteer's).
"""

import sys
import json
import time

from face_id import load_and_encode, NoFaceFoundError
from web_search import find_matching_post, SearchError
from blockchain import SimulatedChain, fingerprint_data


def run_pipeline(image_path: str):
    print(f"[1/3] Detecting and encoding face in {image_path} ...")
    encoding, location = load_and_encode(image_path)
    print(f"      Face found at {location}")

    print("[2/3] Searching the web for matching content (SerpApi reverse image search) ...")
    uploaded_url, results = find_matching_post(image_path)
    top_hit = results[0]
    print(f"      Uploaded scan to: {uploaded_url}")
    print(f"      Top match: {top_hit['title']} -> {top_hit['link']}")

    print("[3/3] Recording the discovered post on the simulated blockchain ...")
    record = {
        "source_image_url": uploaded_url,
        "matched_post_title": top_hit["title"],
        "matched_post_link": top_hit["link"],
        "matched_post_source": top_hit["source"],
        "face_encoding_fingerprint": fingerprint_data({"encoding": encoding.tolist()}),
        "recorded_at": time.time(),
    }
    fingerprint = fingerprint_data(record)
    on_chain_data = {"fingerprint": fingerprint, "record": record}

    chain = SimulatedChain()
    block = chain.add_record(on_chain_data)
    print(f"      Recorded as block #{block.index}, block hash: {block.hash}")

    # Immediately re-verify to demonstrate tamper-evidence
    still_valid = chain.verify_record(block.index, on_chain_data)
    print(f"      Chain valid: {chain.is_valid()} | Re-verified match: {still_valid}")

    output = {
        "block_index": block.index,
        "block_hash": block.hash,
        "record": record,
        "chain_valid": chain.is_valid(),
        "re_verified": still_valid,
    }
    return output


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pipeline.py <path_to_face_scan_image>")
        sys.exit(1)

    try:
        result = run_pipeline(sys.argv[1])
        print("\n=== FINAL RESULT ===")
        print(json.dumps(result, indent=2))
    except NoFaceFoundError as e:
        print(f"Face detection error: {e}")
        sys.exit(1)
    except SearchError as e:
        print(f"Web search error: {e}")
        sys.exit(1)
