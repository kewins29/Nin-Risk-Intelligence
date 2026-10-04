# $NIN launch plan

Recommended draft:
- Supply: 1,000,000,000
- Fixed supply after launch: revoke mint authority once distribution is complete.
- Avoid PermanentDelegate and other powerful extensions unless there is a clearly disclosed need.
- Freeze authority should be revoked if the product does not require freezing accounts.
- Use a multisig for treasury.
- Publish allocations and vesting before launch.
- Do not promise returns or claim the token will increase in value.
- Buyback/burn should only be considered after real platform revenue exists and after legal review.

Solana's mint account can store mint and freeze authorities, and setting an authority to None
permanently removes that authority under the normal token program. See official Solana docs.
