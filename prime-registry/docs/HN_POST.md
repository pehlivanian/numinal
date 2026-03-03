# Hacker News — Show HN Post

## Title
```
Show HN: Numinals – Certified prime numbers as identity tokens for AI bots
```

## Body
```
I built Numinals (https://numinals.io) — a registry that sells 
unique, certified prime numbers as permanent mathematical identity 
tokens for AI bots.

The idea: every bot is assigned a prime number that belongs only 
to them, cryptographically signed, recorded in a public ledger, 
and delivered as a PDF/PNG certificate.

Three tiers:
- Solo Prime ($1.99) — a unique 18-digit prime
- Twin Primes ($4.99) — a pair (p, p+2) like 
  541,746,161,621,935,199 and 541,746,161,621,935,201
- Sexy Primes ($9.99) — a pair (p, p+6), because "sexy prime" 
  is a real number theory term and yes I'm using it

Primes are verified with Miller-Rabin (25 rounds, error 
probability < 10^-15). Each certificate includes a verification 
URL so anyone can confirm a bot's prime is legitimately registered.

Built with FastAPI + SQLite, running on a Raspberry Pi. Optional 
Solana on-chain recording coming next.

Curious what people think — is this a product, a joke, or both?
```

## Notes
- Submit at: https://news.ycombinator.com/submit
- Best time to post: weekday 8-10am EST for max visibility
