# "What a full grant changes": the grant-effect assumption

The Grant Desk sidebar setting **"What a full grant changes"** (agent parameter `assumption`,
code: `CLOSURE_RISK_REDUCTION` in [`scoring.py`](../agent/grant_advisor/tools/scoring.py)) answers the one
question no dataset can: **how much does a grant actually help a business survive?**

The challenge asks for this explicitly: *"A grant changes a probability, not an outcome. Say what you
are assuming."* We make the assumption explicit and show the answer across a range.

## The three settings

If a business receives its **full request**, its chance of closing in the next 12 months drops by:

| Setting | Closure-risk reduction | Plain meaning |
|---|---|---|
| **Pessimistic** | **−5 points** (e.g. 30% → 25%) | The grant buys a little time but rarely changes the outcome (the floor) |
| **Base** (default) | **−10 points** (e.g. 30% → 20%) | A meaningful but modest effect: our **central estimate** |
| **Optimistic** | **−20 points** (e.g. 30% → 10%) | The grant often decides whether the business survives (the ceiling) |

> **These values are our assumptions, not figures from research.** Say so in the deck and the memo.

## What it changes, and what it does not

It changes only the **expected impact**:

```
expected businesses spared = closure-risk reduction × downstream businesses exposed × (award ÷ request)
```

Real data (Central Market, $50,000 fund, 2026-10-20):

| Applicant | Exposed (2 hops) | Pessimistic | Base | Optimistic |
|---|---:|---:|---:|---:|
| Cumaica Coffee ($20k of $20k) | 148 | ~7.4 | ~14.8 | ~29.6 |
| Sour Flour ($25k of $25k) | 148 | ~7.4 | ~14.8 | ~29.6 |
| G.Rabbit ($5k of $12k, partial) | 18 | ~0.4 | ~0.75 | ~1.5 |

It does **not** change the **ranking or the allocation**. The same assumption applies to every
applicant, so their order is unchanged (checked by `test_assumption_changes_expected_effect_not_order`).
That is why "Re-rank with the pessimistic assumption" returns *same businesses funded, impact halved*.

## Why we need Base, and why not just pick Optimistic

The three settings are not competing answers. They are a **range**: low / middle / high guesses for
something nobody can measure.

- **Base** is the **central estimate**: one defensible number for the headline and the memo.
- **Pessimistic** and **Optimistic** are the **bounds** that show how sensitive the impact is.

Do not default to **Optimistic**:

1. **It overclaims.** "$20k spares ~30 businesses" invites the judge question *"says who?"*. The judging
   guide rewards honesty: *"A team that volunteers its limitations shows more skill than one that oversells."*
2. **It does not change the decision.** The same three businesses are funded under all three settings,
   so Optimistic only inflates the impact number.
3. **The strength is that it does not matter.** *"Same decision whether grants help a little or a lot"*
   is a stronger statement than any single number.

## How to say it in the pitch

> "We don't know what $20,000 does to a bakery's survival odds, and nobody does. So we state the
> assumption, show the result under three settings, and show that the decision doesn't depend on which
> one you believe. Only the size of the impact does."

## Possible improvements (not implemented)

- **Show the range instead of a drop-down.** Replace the selector with one line per applicant, e.g.
  *"Cumaica Coffee: ~15 businesses spared (range 7–30 depending on how much a grant helps). Decision
  unchanged across the range."* The memo would carry the same line. This removes the "which one should
  I choose?" confusion.
- **Let the assumption affect the decision.** Make the effect depend on grant size relative to each
  business's need (e.g. diminishing returns for large requests). That would favour smaller grants spread
  wider, and it also bears on the open hub question (two hubs currently receive $45k of $50k).

Related: decision log [D8 and D12](decisions.md), partial awards in [`scoring.py`](../agent/grant_advisor/tools/scoring.py).
