# Face Scan → Web Match → Blockchain Verification

An end-to-end pipeline: take a face scan, genuinely search the live web for a
matching post, then record that discovery on a tamper-evident blockchain and
re-verify it against the on-chain record.

**Pipeline shape:** Face scan input → web/social search (SerpApi reverse image
search) → blockchain upload + re-verification (local simulated chain).

## ⚠️ Ethics / consent note

This project performs real reverse-image search against the live web. The
technique (face → find someone's other photos/social presence online) is the
same one behind commercial tools like PimEyes/Clearview AI, which are
controversial because they can enable stalking or doxxing.

**Only run this on your own photo, or a photo of someone who has explicitly
agreed to be looked up for this test.** Don't point it at photos of people who
haven't consented. This is a demo/assignment tool, not a surveillance product.

## What it does

1. **Face identification** (`src/face_id.py`) — detects a face in the input
   image and produces a 128-dimension encoding via the `face_recognition`
   library (built on dlib).
2. **Web/social search** (`src/web_search.py`) — uploads the image to imgbb to
   get a temporary public URL, then runs a genuine Google Reverse Image
   search via SerpApi against that URL. This is a live search, not a
   hardcoded result — whatever SerpApi returns is what gets used.
3. **Blockchain verification** (`src/blockchain.py`) — fingerprints the
   discovered post (title, link, source, source image URL, and the face
   encoding's own hash) with SHA-256, mines it into a block on a local
   simulated blockchain (proof-of-work with adjustable difficulty, hash-linked
   blocks, persisted to `data/chain.json`), then immediately re-verifies the
   record against the chain to demonstrate tamper-evidence.

`src/pipeline.py` orchestrates all three steps.

## Why a simulated chain (and how to swap in a real one)

The assignment allows any blockchain, including a local/simulated one. I used
a simulated chain to keep the project runnable with zero blockchain
infrastructure and no gas fees, while still demonstrating the core property
that matters: **the record is hash-linked and re-verifiable, and any
tampering with historical data is detectable** (`chain.is_valid()` will
return `False`).

To swap in a real chain (e.g. Ethereum Sepolia testnet):
- Install `web3.py`
- Get a free RPC endpoint (Infura/Alchemy) and Sepolia testnet ETH from a
  faucet
- Replace `blockchain.py`'s `add_record`/`verify_record` with a call that
  writes the same SHA-256 fingerprint to a simple storage contract (or even
  just to `eth_sendTransaction`'s `data` field), and reads it back to verify

This wasn't done in the primary submission because it adds an external
dependency (RPC access, funded testnet wallet) that isn't available in every
grading environment; the simulated chain keeps `python src/pipeline.py` fully
self-contained.

## Setup

```bash
git clone <this-repo>
cd face-verify-chain
pip install -r requirements.txt   # dlib may take a few minutes to build
cp .env.example .env
# edit .env with your keys:
#   IMGBB_API_KEY   -> https://api.imgbb.com/  (free)
#   SERPAPI_API_KEY -> https://serpapi.com/    (free tier available)
export $(cat .env | xargs)        # or use python-dotenv / your shell's method
```

## Running it

```bash
python src/pipeline.py path/to/your_face_scan.jpg
```

Example output:

```
[1/3] Detecting and encoding face in scan.jpg ...
      Face found at (top, right, bottom, left)
[2/3] Searching the web for matching content (SerpApi reverse image search) ...
      Uploaded scan to: https://i.ibb.co/xxxxx/scan.jpg
      Top match: <post title> -> <post url>
[3/3] Recording the discovered post on the simulated blockchain ...
      Recorded as block #1, block hash: 000abc123...
      Chain valid: True | Re-verified match: True

=== FINAL RESULT ===
{ ... JSON summary ... }
```

You can also run each module standalone for debugging:

```bash
python src/face_id.py scan.jpg
python src/web_search.py scan.jpg
python src/blockchain.py
```

## Known limitations

- **Search coverage**: SerpApi's reverse image search returns whatever Google
  has indexed; it may not find a match for private/unindexed photos, or may
  return visually-similar-but-different-person images. The pipeline downloads
  each candidate image when an image URL is available and independently
  verifies its detected faces against the input. Candidates without a
  downloadable image, a detected face, or a close enough face distance are
  rejected. If no candidate passes, the pipeline stops without recording a
  match.
- **Simulated blockchain**: not a distributed ledger — it proves internal
  tamper-evidence (any edit to `data/chain.json` breaks `is_valid()`), but
  doesn't provide the decentralization/censorship-resistance guarantees of a
  real chain. See "Why a simulated chain" above for how to upgrade this.
- **imgbb dependency**: SerpApi's reverse-image endpoint needs a public image
  URL, so the scan is briefly uploaded to a third-party image host. Anyone
  running this should be aware the scan becomes (temporarily) publicly
  accessible at that URL.
- **dlib install**: `face_recognition`/dlib can be slow to build from source
  on some machines; a prebuilt wheel or conda-forge install is often faster.
- **Rate limits**: both imgbb's and SerpApi's free tiers are rate-limited;
  heavy testing may hit those limits.

## Project structure

```
face-verify-chain/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   └── chain.json          (created on first run)
└── src/
    ├── face_id.py
    ├── web_search.py
    ├── blockchain.py
    └── pipeline.py
```
