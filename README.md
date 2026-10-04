# NIN v1 — runnable Solana scanner

Run:
  python server.py

Then open:
  http://localhost:8080

Optional:
  set SOLANA_RPC_URL to a paid/private Solana RPC endpoint for production use.

Current live checks:
- mint exists / account is a token mint
- mint authority
- freeze authority
- total supply / decimals
- top-20 token account concentration

Not yet a complete security audit. It does not prove a token is sellable and does not replace
a smart-contract/security audit. Production needs DEX liquidity/pool data, transaction behavior,
creator-wallet clustering, rate limiting, caching, logging, tests, and security review.
