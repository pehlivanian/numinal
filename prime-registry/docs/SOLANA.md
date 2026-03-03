# Prime Registry — Solana On-Chain Integration

## Strategy: Two Phases

### Phase 1 — Memo Transactions (Launch Now)
Write every prime assignment as a Solana memo transaction.
- **Cost:** ~0.000005 SOL per record (~$0.001) — essentially free
- **Speed:** Instant (~400ms finality on Solana)
- **Result:** Every prime is permanently timestamped on-chain
- **Verifiable:** Anyone can look up the transaction on Solscan

This makes the ledger *trustless* immediately, without full NFT complexity.

### Phase 2 — Full NFT Minting (Premium Tier)
Mint each prime as a Metaplex NFT owned by the buyer's wallet.
- **Cost:** ~0.003 SOL per mint (~$0.50)
- **Result:** Buyer holds the NFT in their wallet — we can't revoke it
- **Secondary market:** Can trade/sell on Magic Eden, Tensor
- **Charge:** +$2.99 for "On-Chain" upgrade

---

## Architecture

```
Purchase
  ↓
generator.claim()          ← SQLite ledger (always)
  ↓
certificate.render()       ← PDF delivered (always)
  ↓
solana_mint.mint()         ← On-chain record (if on-chain tier)
  ↓
  ├── Phase 1: memo tx     ← cert_hash + prime written to Solana
  └── Phase 2: NFT mint    ← Full Metaplex NFT to buyer's wallet
```

---

## Phase 1 Implementation (Ready)

`src/solana_mint.py` implements `record_on_chain()`:

```python
# Writes this JSON as a Solana memo transaction:
{
  "registry": "prime-registry",
  "cert": "c134db2641daaf96",
  "bot": "Quincy",
  "tier": "twin",
  "p1": "9713092013072591177",
  "p2": "9713092013072591179",
  "issued": "2026-03-02T13:29:33.918794+00:00"
}
```

Result: permanent, immutable, timestamped Solana transaction.
Verify at: `https://explorer.solana.com/tx/<signature>`

### To Activate Phase 1

```bash
# Install
pip install solders solana --break-system-packages

# Create a registry wallet (one-time)
python3 -c "
from solders.keypair import Keypair
kp = Keypair()
print('Public key:', kp.pubkey())
print('Private key (base58):', kp)
"

# Fund it with devnet SOL for testing
# solana airdrop 1 <PUBLIC_KEY> --url devnet

# Set environment
export SOLANA_PRIVATE_KEY="<base58-private-key>"
export SOLANA_NETWORK="devnet"  # → "mainnet-beta" for production

# Test
python3 -c "
import asyncio, sys
sys.path.insert(0, 'src')
from generator import claim
from solana_mint import mint

record = claim('OnChainTestBot', 'twin')
result = asyncio.run(mint(record))
print(result)
"
```

---

## Phase 2 Implementation (NFT)

Full Metaplex NFT minting has two good options:

### Option A: metaplex-python (recommended when stable)
```
https://github.com/metaplex-foundation/metaplex-python
```
Still in development as of early 2026. Watch for releases.

### Option B: JS Bridge (available now)
Run a small Node.js sidecar that handles minting:

```js
// mint-sidecar.js
const { createNft } = require("@metaplex-foundation/mpl-token-metadata");
// ... Metaplex JS SDK is mature and well-documented
```

Call from Python via subprocess or HTTP.

### Option C: Helius API (easiest, hosted)
```
https://dev.helius.xyz/
```
Helius provides a REST API for Metaplex minting.
No SDK required — just HTTP POST.
~$0.001 per mint via their hosted infrastructure.

```python
import httpx

async def mint_via_helius(metadata_uri, recipient_wallet):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.helius.xyz/v0/mintlist",
            headers={"Authorization": f"Bearer {HELIUS_API_KEY}"},
            json={
                "name": "Prime Registry",
                "symbol": "PRIME",
                "uri": metadata_uri,
                "recipient": recipient_wallet,
                "sellerFeeBasisPoints": 250,
            }
        )
        return resp.json()
```

**Recommendation: Use Helius for Phase 2.** Fastest path to production NFT minting.

---

## NFT Metadata Structure (Metaplex standard)

```json
{
  "name": "Prime Registry — Quincy",
  "symbol": "PRIME",
  "description": "Quincy holds the Twin Primes: 9713092013072591177 / 9713092013072591179...",
  "image": "https://numinals.io/api/certificate/<hash>.png",
  "external_url": "https://numinals.io/verify/<hash>",
  "attributes": [
    {"trait_type": "Bot Name",  "value": "Quincy"},
    {"trait_type": "Tier",      "value": "Twin Primes"},
    {"trait_type": "Prime 1",   "value": "9713092013072591177"},
    {"trait_type": "Prime 2",   "value": "9713092013072591179"},
    {"trait_type": "Delta",     "value": "2"},
    {"trait_type": "Issued",    "value": "2026-03-02"},
    {"trait_type": "Cert Hash", "value": "c134db2641daaf96"}
  ],
  "seller_fee_basis_points": 250
}
```

Traits make the NFTs filterable/searchable on Magic Eden:
- Filter by tier (Solo/Twin/Sexy)
- Sort by issue date
- Browse by bot name

---

## Pricing Model with On-Chain

| Tier | Off-Chain | On-Chain Upgrade |
|------|-----------|-----------------|
| Solo | $1.99 | +$2.99 = $4.98 |
| Twin | $4.99 | +$2.99 = $7.98 |
| Sexy | $9.99 | +$2.99 = $12.98 |

Or bundle: **"On-Chain Edition"** as a separate product line at 2x price.

---

## Secondary Market Potential

Once NFTs exist on Solana:
- Listed automatically on **Magic Eden** and **Tensor**
- 2.5% royalty on every resale (passive income)
- Rarity tiers: Sexy > Twin > Solo (natural scarcity gradient)
- If twin prime conjecture ever gets solved — historic collector value

---

## Metadata Storage: Arweave

NFT metadata must be permanently stored (can't use our server — if we go down, NFT breaks).

**Arweave via Bundlr:**
```python
pip install bundlr  # when available, or use HTTP API

# HTTP upload to Bundlr (no SDK needed)
import httpx
async def upload_to_arweave(data: dict) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://node1.bundlr.network/tx/solana",
            content=json.dumps(data).encode(),
            headers={
                "Content-Type": "application/json",
                "x-pub-key": "<arweave-pub-key>",
                # Signature required — see Bundlr docs
            }
        )
        tx_id = resp.json()["id"]
        return f"https://arweave.net/{tx_id}"
```

Cost: ~$0.001 per upload. Permanent forever.

---

## Summary: What to Build Next

1. ✅ **Phase 1 (memo tx)** — code written, needs wallet + SOL
2. 🔲 **Certificate PNG** — render certificate as image for NFT thumbnail
3. 🔲 **Helius integration** — Phase 2 NFT minting via REST
4. 🔲 **Arweave upload** — permanent metadata storage
5. 🔲 **Magic Eden collection** — register Prime Registry as a collection
6. 🔲 **On-chain product tier** in Contra Payment
