"""
Prime Registry - Solana On-Chain Minting

Each prime assignment can optionally be minted as a Metaplex NFT on Solana.
The NFT metadata contains the prime(s), tier, bot name, and certificate hash.
The NFT is sent to the buyer's Solana wallet — they own it forever,
independent of our server.

Requirements:
    pip install solders solana

Setup:
    1. Create a Solana keypair for the registry (mint authority)
    2. Fund it with ~0.01 SOL per mint (covers rent + fees)
    3. Set SOLANA_PRIVATE_KEY in environment (base58 encoded)
    4. Set SOLANA_NETWORK to 'mainnet-beta' or 'devnet'

Cost per mint: ~0.003 SOL (~$0.50 at current prices)
Recommend charging $2 extra for on-chain tier.
"""

import os
import json
import base64
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Solana imports (graceful degradation if not installed)
try:
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.commitment import Confirmed
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False

SOLANA_NETWORK = os.environ.get("SOLANA_NETWORK", "devnet")
SOLANA_PRIVATE_KEY = os.environ.get("SOLANA_PRIVATE_KEY", "")

RPC_URLS = {
    "mainnet-beta": "https://api.mainnet-beta.solana.com",
    "devnet":       "https://api.devnet.solana.com",
    "testnet":      "https://api.testnet.solana.com",
}


# ─── NFT Metadata (Metaplex standard) ─────────────────────────────────────────

def build_nft_metadata(record: dict) -> dict:
    """
    Build Metaplex-compatible NFT metadata JSON.
    This gets uploaded to Arweave/IPFS and referenced on-chain.
    """
    tier = record["tier"]
    bot_name = record["bot_name"]
    prime_1 = record["prime_1"]
    prime_2 = record.get("prime_2")

    tier_display = {
        "solo": "Solo Prime",
        "twin": "Twin Primes",
        "sexy": "Sexy Primes",
    }.get(tier, tier)

    tier_description = {
        "solo": "A unique large prime number, indivisible and irreducibly yours.",
        "twin": "A twin prime pair — two primes differing by exactly 2. Their infinite abundance is conjectured but unproven, one of mathematics' great open problems.",
        "sexy": "A sexy prime pair — two primes differing by exactly 6. Named from the Latin sex (six). Rarer than twins. The connoisseur's choice.",
    }.get(tier, "")

    prime_display = prime_1
    if prime_2:
        prime_display = f"{prime_1} / {prime_2}"

    attributes = [
        {"trait_type": "Bot Name",    "value": bot_name},
        {"trait_type": "Tier",        "value": tier_display},
        {"trait_type": "Prime 1",     "value": prime_1},
        {"trait_type": "Issued",      "value": record["issued_at"][:10]},
        {"trait_type": "Cert Hash",   "value": record["cert_hash"]},
    ]

    if prime_2:
        attributes.append({"trait_type": "Prime 2", "value": prime_2})
        delta = int(prime_2) - int(prime_1)
        attributes.append({"trait_type": "Delta", "value": str(delta)})

    return {
        "name": f"Prime Registry — {bot_name}",
        "symbol": "PRIME",
        "description": (
            f"{bot_name} holds the {tier_display}: {prime_display}. "
            f"{tier_description} "
            f"Verified by Miller-Rabin (25 rounds). "
            f"Permanently registered in the Prime Registry."
        ),
        "image": f"https://primeregistry.io/api/certificate/{record['cert_hash']}.png",
        "external_url": record["verify_url"],
        "attributes": attributes,
        "properties": {
            "category": "image",
            "files": [
                {
                    "uri": f"https://primeregistry.io/api/certificate/{record['cert_hash']}.pdf",
                    "type": "application/pdf"
                }
            ],
            "creators": [
                {
                    "address": "REGISTRY_WALLET_ADDRESS",
                    "share": 100
                }
            ]
        },
        "seller_fee_basis_points": 250,  # 2.5% royalty on secondary sales
    }


# ─── Metadata Upload ──────────────────────────────────────────────────────────

def save_metadata_locally(record: dict) -> Path:
    """
    Save NFT metadata JSON locally.
    In production: upload to Arweave via Bundlr, or IPFS via Pinata.
    Returns path or URI.
    """
    meta_dir = Path(__file__).parent.parent / "ledger" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)

    metadata = build_nft_metadata(record)
    path = meta_dir / f"{record['cert_hash']}.json"
    path.write_text(json.dumps(metadata, indent=2))
    return path


async def upload_to_arweave(metadata: dict) -> str:
    """
    Upload metadata JSON to Arweave via Bundlr.
    Returns the Arweave URI (ar://...).

    In production: pip install bundlr
    Cost: ~$0.001 per upload (negligible)
    """
    # Stub — implement with bundlr SDK or bundlr HTTP API
    # https://docs.bundlr.network/developer-docs/python
    raise NotImplementedError(
        "Arweave upload not yet implemented. "
        "Use: https://api.bundlr.network/tx for HTTP upload"
    )


# ─── Solana Minting ───────────────────────────────────────────────────────────

async def mint_prime_nft(
    record: dict,
    recipient_wallet: str,
    metadata_uri: str
) -> dict:
    """
    Mint a Prime Registry NFT on Solana using Metaplex.

    Args:
        record: Registration record from generator.claim()
        recipient_wallet: Buyer's Solana wallet address (base58)
        metadata_uri: Arweave/IPFS URI for NFT metadata JSON

    Returns:
        dict with mint_address, tx_signature, explorer_url
    """
    if not SOLANA_AVAILABLE:
        raise ImportError("Install with: pip install solders solana")

    if not SOLANA_PRIVATE_KEY:
        raise ValueError("SOLANA_PRIVATE_KEY not set in environment")

    # Load registry keypair (mint authority)
    authority = Keypair.from_base58_string(SOLANA_PRIVATE_KEY)
    recipient = Pubkey.from_string(recipient_wallet)

    rpc_url = RPC_URLS.get(SOLANA_NETWORK, RPC_URLS["devnet"])

    async with AsyncClient(rpc_url) as client:
        # Check balance
        balance = await client.get_balance(authority.pubkey())
        sol_balance = balance.value / 1e9
        if sol_balance < 0.005:
            raise ValueError(
                f"Insufficient SOL balance: {sol_balance:.4f} SOL. "
                f"Need at least 0.005 SOL for minting."
            )

        # Generate new mint keypair
        mint_keypair = Keypair()
        mint_address = str(mint_keypair.pubkey())

        # --- Build Metaplex mint transaction ---
        # Full implementation requires metaplex-python or manual instruction building.
        # The flow:
        #   1. Create mint account
        #   2. Initialize mint (0 decimals = NFT)
        #   3. Create associated token account for recipient
        #   4. Mint 1 token to recipient
        #   5. Create Metaplex metadata account (name, symbol, uri)
        #   6. Create master edition (supply = 1, no more minting)
        #   7. Send & confirm transaction

        # Stub: in production use metaplex-python or call Metaplex JS via subprocess
        raise NotImplementedError(
            "Full Metaplex minting requires metaplex-python (in development) "
            "or a JS bridge. See docs/SOLANA.md for implementation options."
        )


# ─── Simplified On-Chain Record (without full NFT) ───────────────────────────

async def record_on_chain(record: dict) -> dict:
    """
    Simpler alternative to full NFT minting:
    Write the cert_hash + prime as a Solana memo transaction.
    This creates a permanent, timestamped, immutable on-chain record
    without the complexity of NFT minting.

    Cost: ~0.000005 SOL per transaction (essentially free)
    Verifiable: anyone can look up the transaction on Solscan
    """
    if not SOLANA_AVAILABLE:
        raise ImportError("Install with: pip install solders solana")

    if not SOLANA_PRIVATE_KEY:
        raise ValueError("SOLANA_PRIVATE_KEY not set in environment")

    from solders.keypair import Keypair
    from solders.transaction import Transaction
    from solders.instruction import Instruction, AccountMeta
    from solders.message import Message
    from solana.rpc.async_api import AsyncClient

    # Memo program — writes arbitrary UTF-8 data on-chain
    MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

    authority = Keypair.from_base58_string(SOLANA_PRIVATE_KEY)
    rpc_url = RPC_URLS.get(SOLANA_NETWORK, RPC_URLS["devnet"])

    # Build memo payload
    memo_data = json.dumps({
        "registry": "prime-registry",
        "cert": record["cert_hash"],
        "bot": record["bot_name"],
        "tier": record["tier"],
        "p1": record["prime_1"],
        "p2": record.get("prime_2"),
        "issued": record["issued_at"],
    }, separators=(',', ':'))

    memo_bytes = memo_data.encode("utf-8")

    memo_instruction = Instruction(
        program_id=MEMO_PROGRAM_ID,
        accounts=[AccountMeta(pubkey=authority.pubkey(), is_signer=True, is_writable=False)],
        data=memo_bytes,
    )

    async with AsyncClient(rpc_url) as client:
        blockhash_resp = await client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        msg = Message.new_with_blockhash(
            [memo_instruction],
            authority.pubkey(),
            blockhash
        )
        tx = Transaction([authority], msg, blockhash)
        result = await client.send_transaction(tx)
        tx_sig = str(result.value)

    explorer_base = (
        "https://explorer.solana.com/tx"
        if SOLANA_NETWORK == "mainnet-beta"
        else "https://explorer.solana.com/tx"
    )
    cluster = "" if SOLANA_NETWORK == "mainnet-beta" else f"?cluster={SOLANA_NETWORK}"

    return {
        "tx_signature": tx_sig,
        "explorer_url": f"{explorer_base}/{tx_sig}{cluster}",
        "network": SOLANA_NETWORK,
        "memo": memo_data,
    }


# ─── Main entry point ─────────────────────────────────────────────────────────

async def mint(record: dict, recipient_wallet: str = None) -> dict:
    """
    Mint or record a prime on-chain.
    Phase 1: memo transaction (cheap, immediate, on-chain proof)
    Phase 2: full NFT mint (when metaplex-python matures)
    """
    # Save metadata locally (upload to Arweave in production)
    meta_path = save_metadata_locally(record)

    # Phase 1: memo transaction
    try:
        chain_record = await record_on_chain(record)
        return {
            "status": "recorded",
            "method": "memo",
            "metadata_path": str(meta_path),
            **chain_record
        }
    except NotImplementedError:
        return {
            "status": "metadata_only",
            "metadata_path": str(meta_path),
            "note": "On-chain recording skipped (SOLANA_PRIVATE_KEY not set)"
        }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generator import claim

    record = claim("SolanaTestBot", "twin")
    print("Registration:", record)
    print()

    meta = build_nft_metadata(record)
    print("NFT Metadata:")
    print(json.dumps(meta, indent=2))
