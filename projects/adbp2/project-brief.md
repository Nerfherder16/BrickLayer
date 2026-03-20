# Project Brief — ADBP v2

## What this system actually does

ADBP is a closed-loop utility credit platform. Employees pay $1 to mint a token worth $2 in
purchasing power at participating vendors. Tokens are auto-cycled B2B once per month. Each
B2B transaction (after the first spend) burns a percentage of the token and reimburses the
accepting vendor the full $2 face value of the burned portion from the escrow pool. Tokens
recirculate perpetually (vendor → employer → vendor → ...) until fully burned.

The $1 employee pays is the purchasing power amplification — they get $2 of real spending power
from $1 invested. The system sustains this through escrow management, fee income, and interest.

## The Key Invariants

1. **Token face value is always $2.00.** It never changes. There is no speculative value.
2. **Mint price is always $1.00.** Employees always pay $1 per token.
3. **First spend has no burn** — only an admin fee released from escrow. Burn begins on second+ B2B.
4. **Burns only activate when CRR >= 1.0** (pool-average escrow per token has reached $2.00).
5. **Reimbursement = $2.00 × burn_rate per token burned** — vendor is always made economically whole.
6. **Circulating tokens must always be <= 50% of total vendor acceptance capacity.**
7. **Escrow and Treasury are separate wallets. Treasury NEVER covers reimbursements.**
8. **If CRR < 0.40, minting pauses automatically.**
9. **Auto-cycle is system-enforced** — all tokens complete exactly 1 B2B transaction per month.
10. **Only employees can mint. Mint is capped at 5,000 tokens/employee/month.**

## What Has Been Misunderstood Before

- **Misunderstanding**: The entire $1 escrow is released each B2B transaction.
  **Correct**: Only the burned portion's backing is released (B% × $2). The rest stays locked.

- **Misunderstanding**: CRR should start at ~1.0.
  **Correct**: CRR starts at ~0.50 by design ($1 escrow per $2 obligation). This is the amplification feature. CRR rises toward 1.0 via fees + interest over time.

- **Misunderstanding**: Admin fees are recycled to escrow.
  **Correct**: Admin fees are paid OUT to the accepting party on each transaction. They leave the system.

- **Misunderstanding**: Burns happen from day one.
  **Correct**: Burns only activate when CRR >= 1.0 (pool escrow averages $2/token). This may take months to years depending on fee level.

- **Misunderstanding**: The treasury backstops reimbursements.
  **Correct**: If escrow can't cover reimbursements, minting pauses. Treasury is never touched for reimbursements.

## What This System Is NOT

- It is not a speculative cryptocurrency — token value is fixed at $2, no price discovery.
- It is not a stablecoin — tokens are not redeemable for $2 cash, only spendable at vendors.
- It is not a loyalty points system — tokens have real monetary backing and real burn mechanics.
- It is not a bank — there are no deposits, withdrawals, or interest paid to participants.

## The Numbers That Cannot Be Wrong

| Fact | Value | Source |
|------|-------|--------|
| Token face value | $2.00 USD | System design |
| Mint price | $1.00 USD | System design |
| Escrow deposit at mint | $1.00 USD | System design |
| Burn reimbursement rate | $2.00 per burned token | System design |
| Burn rate range | 2%–15% (dynamic) | Traditional tokenomics |
| Burn activation threshold | CRR ≥ 1.0 | System design |
| Capacity rule | Tokens ≤ 50% of vendor capacity | System design |
| Monthly auto-cycle | 1 B2B per token per month | System design |
| Employee mint cap | 5,000 tokens/month | System design |
| Expected employee mint | ~2,000 tokens/month | Usage assumption |
| Interest rate | 4% annual | T-bill/money market target |
| Year 5 employee target | 5,000,000 | Growth projection |

## Escrow Funding Path ($1 → $2 per Token)

Each token's escrow backing grows via the POOL (not individual tracking):
1. **Mint**: $1.00 locked per token
2. **Interest**: Escrow pool earns 4%/yr — adds ~$0.0033/token/month
3. **Employee fees (escrow share)**: Fee × FEE_TO_ESCROW_PCT / 2000 per token/month
4. **Treasury recycling** (minimize — preferred not to use): Optional T% recycled back

Since per-token escrow growth rate from fees = (fee × fee_to_escrow_pct) / 2000, this is
CONSTANT regardless of system scale. A $45/month fee at 60% to escrow adds ~$0.0135/token/month.
Combined with interest, burns activate around month 55–60 at that fee level.

## Research Scope

**In scope**:
- Minimum fee level to maintain CRR >= CRR_OPERATIONAL_TARGET through all growth phases
- Optimal BURN_SPLIT (R/AF/T) that maximizes treasury while keeping escrow solvent
- Month when first burns occur under different fee scenarios
- Treasury profitability timeline
- Solvency stress tests: slow growth, fast growth, fee reduction, vendor capacity shocks
- CRR trajectory under the defined growth curve

**Out of scope**:
- Token price discovery (price is fixed at $2)
- Solana smart contract implementation details
- Vendor recruitment strategy
- Regulatory/legal analysis

## Documents in docs/

| File | Authoritative for |
|------|------------------|
| (none yet) | Add ADBP specs, legal docs, prior model files here |
