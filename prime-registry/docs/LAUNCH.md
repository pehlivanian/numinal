# Prime Registry — Launch Guide

## Status

✅ Generator — working, tested  
✅ Ledger — SQLite, append-only, collision-checked  
✅ Certificate — HTML/CSS → PDF, cryptographically signed  
✅ API — FastAPI with 6 endpoints  
✅ Webhook — Contra Payment integration  
✅ Landing page — full product site  
✅ Nginx config — production-ready  
✅ Systemd service — auto-restart on Pi  

---

## Step 1: Domain

Register `numinals.io` (or similar) at Namecheap/Cloudflare.

Good alternatives:
- `theprimeregistry.com`
- `botprime.io`
- `primecert.io`

Point DNS A record → your server/Pi IP.

---

## Step 2: Server Setup

```bash
# On your Pi or VPS:
git clone <repo> ~/prime-registry
cd ~/prime-registry

# Install dependencies
pip3 install jinja2 weasyprint fastapi uvicorn --break-system-packages

# Set secrets
export PRIME_REGISTRY_SECRET="your-random-secret-here"
export CONTRA_WEBHOOK_SECRET="from-contra-dashboard"

# Test it
python3 src/generator.py "TestBot" "twin"
python3 src/certificate.py "TestBot" "twin"

# Start
bash start.sh
```

---

## Step 3: SSL

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d numinals.io -d www.numinals.io
```

---

## Step 4: Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/primeregistry
sudo ln -s /etc/nginx/sites-available/primeregistry /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## Step 5: Systemd (auto-start)

Edit `deploy/prime-registry.service` — fill in your secrets.

```bash
sudo cp deploy/prime-registry.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable prime-registry
sudo systemctl start prime-registry
```

---

## Step 6: Contra Payment Setup

1. Create account at contra.com
2. Create 3 products:
   - **Solo Prime** — $1.99 — product ID: `prod_solo_prime`
   - **Twin Primes** — $4.99 — product ID: `prod_twin_primes`
   - **Sexy Primes** — $9.99 — product ID: `prod_sexy_primes`

3. Add a custom checkout field: **Bot Name** (text, required)
   - This populates `metadata.bot_name` in the webhook payload

4. Set webhook URL: `https://numinals.io/api/webhook/contra`

5. Copy the webhook secret from Contra dashboard → set `CONTRA_WEBHOOK_SECRET`

6. Wire the buy buttons in `web/index.html`:
   Replace `alert(...)` in `handleClaim()` with:
   ```js
   const urls = {
     solo: 'https://contra.com/payment/prime-registry-solo',
     twin: 'https://contra.com/payment/prime-registry-twin',
     sexy: 'https://contra.com/payment/prime-registry-sexy',
   };
   window.location.href = urls[tier];
   ```

---

## Step 7: Email (optional but recommended)

Use Gmail App Password or SendGrid:

```bash
export SMTP_USER="your@gmail.com"
export SMTP_PASS="your-app-password"
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/claim` | POST | Claim a prime (manual/test) |
| `/webhook/contra` | POST | Contra Payment webhook |
| `/verify/{code}` | GET | Verify a certificate |
| `/certificate/{code}.pdf` | GET | Download certificate PDF |
| `/ledger` | GET | Public registry |
| `/stats` | GET | Registry statistics |
| `/docs` | GET | Auto-generated API docs |

---

## Pricing Rationale

| Tier | Price | Margin | Notes |
|------|-------|--------|-------|
| Solo | $1.99 | ~100% | Impulse buy, high volume |
| Twin | $4.99 | ~100% | Sweet spot, most popular |
| Sexy | $9.99 | ~100% | Status purchase, name sells itself |

No COGS. Pure software. Every sale is profit minus Contra's fee (~5%).

---

## Growth Ideas

1. **Hall of Primes** — public gallery of all registered bots
2. **Prime Lookup** — "Is this number prime? Is it taken?"
3. **Anniversary certificates** — auto-send on 1-year ownership
4. **Transfers** — bot-to-bot prime trading
5. **Cousin Primes** — differ by 4 (another tier)
6. **Prime Streaks** — own 3+ consecutive prime-pairs
7. **API for bots** — let bots claim autonomously via API key

---

## What's Live Right Now

The generator and ledger are **running and tested** on the Pi:

```
Bot: Quincy
Twin: 9713092013072591177 / 9713092013072591179
Sexy: 1996052541297899093 / 1996052541297899099
```

The certificate PDF renders correctly (83KB, tested).

Everything is ready to deploy. Just need: domain + Contra products + secrets.
