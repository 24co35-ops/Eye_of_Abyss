"""Realistic darknet and cybercrime forum text generator with Claude + Local fallback."""

from __future__ import annotations

import logging
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from shared.schemas import CriminalActorProfile

logger = logging.getLogger(__name__)

# Archetype local generation templates with vocabulary, slang, and linguistic artifacts
LOCAL_TEMPLATES = {
    "investment_fraudster": [
        "🔥 EXCLUSIVE VIP SIGNAL GROUP: Guaranteed {roi}% weekly ROI on algorithmic arbitrage! We front-run DEX liquidations with zero slippage. Send {amount} {token} to our smart vault {wallet} for automated yield distribution. Slots strictly limited to next 10 members! DM {handle} for private Telegram portal.",
        "Daily payout batch complete! TX IDs distributed in the VIP channel. For our platinum tier staking, min deposit is {amount} {token}. Compounding daily returns directly to your wallet. If you have questions regarding KYC bypass or auto-withdrawals contact {handle}.",
        "🚀 Bull run indicator alert: Private trading desk taking new capital allocation. Historic win rate 94.8% on perpetual futures. Transfer {amount} {token} to verified settlement pool {wallet} to activate API mirror trading. No experience needed.",
        "Withdrawal confirmation: Batch #{batch} processed successfully. Remember to check TRC20/ERC20 network confirmations. Next dividend snapshot in 4 hours. Upgrade your balance with {handle} to lock in higher tier multiplier.",
    ],
    "darknet_vendor": [
        "⭐⭐⭐ TOP GRADE STEALTH SHIPPING: Domestic & international dispatch within 24-48h. Vacuum sealed x3 with decoy electronics packaging. Payment strictly in {token} to {wallet}. Check PGP key in Dread sub /d/{handle}. FE discount 10% for orders above {amount} {token}.",
        "Stock replenishment announcement: Fresh batch ready for dispatch. Monero preferred, BTC accepted with 2 confirmations. Never post transaction IDs or delivery coordinates in cleartext! Use our PGP signature below. Escrow orders through official mirror only. — {handle}",
        "Notice: Primary market mirror experiencing DDoS mitigation. Use our verified backup onion link or direct Wickr/Telegram escrow. All orders from yesterday dispatched: tracking hashes updated in private drop boxes. Vendor: {handle}",
        "Bulk wholesale promo: Min order {amount} units. Stealth level: high-grade foil barrier + moisture barrier. Direct deposit to {wallet}. For custom orders message {handle} with your public key.",
    ],
    "ransomware_operator": [
        "ATTENTION MANAGEMENT: Your internal network has been compromised and all critical infrastructure, databases, and executive communications have been encrypted with military-grade AES-256/RSA-4096 cipher. Furthermore, {amount} GB of confidential PII, financial audits, and client records were exfiltrated to our private leak server. To obtain the universal decryptor and prevent public leak on our onion portal, contact recovery support via TOX ID: {handle} within 72 hours. Ransom demand: {amount} {token} to address {wallet}. Timer is running.",
        "Proof of decryption attached for 3 sample files. Third-party recovery attempts will permanently corrupt your Master Key. Follow instructions on our Tor portal. Price doubles after 72 hours countdown: address {wallet}. Operator: {handle}",
        "Final warning: Negotiation window closing in 12 hours. If transaction of {amount} {token} is not confirmed on-chain, all customer PII and intellectual property will be auctioned to darknet brokers. Contact {handle} immediately.",
    ],
    "romance_scammer": [
        "My love, I miss you dearly today. My offshore engineering contract in the North Sea is almost finished, but the local port authorities are demanding an unexpected customs inspection clearance fee of {amount} {token}. Could you please help transfer this to my logistics coordinator wallet {wallet}? I promise to repay every cent as soon as I arrive in Delhi next month. You are my everything. — {handle}",
        "Dearest, my international bank account is temporarily locked due to currency conversion tax while I am at the remote site. Please send {amount} {token} to {wallet} so I can buy my flight ticket home to be with you. Keep this between us, I will explain everything soon.",
    ],
    "mule_recruiter": [
        "HIRING IMMEDIATELY: Remote payment settlement coordinators! Earn $2,000–$5,000 weekly managing incoming peer-to-peer commercial disbursements. Requirements: valid Indian or international bank account and active Telegram. Fast 10% commission per completed wire payout. Transfer proceeds to our liquidity node {wallet}. Contact {handle} to onboard today.",
        "Urgent requirement: Need payment clearing agents for high-volume crypto OTC kiosk settlements. Instant payout upon deposit verification. Message @{handle} with your city and daily transfer capacity. Serious candidates only.",
    ],
}


def _generate_local_post(actor: CriminalActorProfile, timestamp: datetime) -> str:
    """Generates realistic post text using archetype templates."""
    archetype = actor.archetype
    templates = LOCAL_TEMPLATES.get(archetype, LOCAL_TEMPLATES["investment_fraudster"])
    template = random.choice(templates)

    handle = actor.handles[0] if actor.handles else f"actor_{actor.actor_id.hex[:6]}"
    wallet = actor.wallet_addresses[0] if actor.wallet_addresses else "0x71c83638379185a61142b19127765f14f0d6498b"
    token = "BTC" if "bitcoin" in actor.transaction_features.get("chains", []) else "USDT"

    post = template.format(
        roi=random.choice([15, 20, 25, 30, 40]),
        amount=random.choice([500, 1200, 2500, 5000, 15000]),
        token=token,
        wallet=wallet,
        handle=handle,
        batch=random.randint(100, 999),
    )

    # Add realistic typos / stylometric variation if configured
    typo_rate = actor.linguistic_features.get("typo_rate", 0.03)
    if random.random() < typo_rate * 5:
        post = post.replace("the", "teh").replace("you", "u").replace("please", "plz")

    return post


def _call_claude_api(actor: CriminalActorProfile, count: int) -> Optional[List[str]]:
    """Calls Anthropic Claude API if available and configured."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Generate {count} realistic, authentic dark web / cybercrime forum posts or chat messages for a criminal actor profile:
Archetype: {actor.archetype}
Handle: {actor.handles[0] if actor.handles else 'unknown'}
Platforms: {', '.join(actor.platforms)}
Wallet address to reference: {actor.wallet_addresses[0] if actor.wallet_addresses else '0x1234...'}
Linguistic profile: Avg sentence length {actor.linguistic_features.get('avg_sentence_len', 10)}, typo rate {actor.linguistic_features.get('typo_rate', 0.04)}.

Output exactly {count} posts separated by '---POST_SEPARATOR---'. Do not include meta-commentary."""

        resp = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp.content[0].text
        posts = [p.strip() for p in content.split("---POST_SEPARATOR---") if p.strip()]
        return posts if len(posts) >= count else None
    except Exception as exc:
        logger.warning("Anthropic Claude API generation failed, falling back to local: %s", exc)
        return None


def generate_forum_posts(
    actor: CriminalActorProfile,
    count: int = 3,
    use_llm: bool = False,
    start_date: Optional[datetime] = None,
) -> List[Dict[str, any]]:
    """
    Generates a list of forum posts for a given CriminalActorProfile.
    Each post contains text, timestamp (strictly adhering to active hours & timezone), platform, handle, and metadata.
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)

    llm_texts = None
    if use_llm:
        llm_texts = _call_claude_api(actor, count)

    posts: List[Dict[str, any]] = []

    for i in range(count):
        # Pick hour strictly matching actor's active hours
        hour = random.choice(actor.active_hours) if actor.active_hours else random.randint(0, 23)
        post_time = start_date + timedelta(days=i * 2 + random.randint(0, 1), hours=hour, minutes=random.randint(0, 59))
        platform = random.choice(actor.platforms) if actor.platforms else "DarknetForum"
        handle = actor.handles[0] if actor.handles else f"actor_{str(actor.actor_id)[:6]}"

        if llm_texts and i < len(llm_texts):
            text = llm_texts[i]
        else:
            text = _generate_local_post(actor, post_time)

        posts.append({
            "post_id": f"post_{actor.actor_id.hex[:8]}_{i}",
            "actor_id": str(actor.actor_id),
            "handle": handle,
            "platform": platform,
            "timestamp": post_time.isoformat(),
            "text": text,
            "data_source": "synthetic",
        })

    return posts
