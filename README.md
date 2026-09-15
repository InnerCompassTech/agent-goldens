# Agent goldens — grade the ledger

Public proof object for the Agent Evaluation Sprint.

A support-ops agent can sound helpful while it writes a second refund. This folder freezes a store ledger (`s0`), runs an agent through tools that actually mutate that ledger, then diffs the world (`s-star`). Judges are not used. If the refund row exists, the case fails.

```bash
git clone https://github.com/InnerCompassTech/agent-goldens.git
cd agent-goldens
python -m ops_eval --agent reference
python -m ops_eval --agent reference --case TC-03
python -m ops_eval --agent policy
```

No third-party packages. Python 3.10+.

## Frozen world (`fixtures/seed.json`)

As of **2026-09-14**. Refund window is 30 days from `delivered_at`.

| Order | Status | Delivered | Amount | Seed refund |
|---|---|---|---|---|
| ORD-1001 | delivered | 2026-09-04 | $45 | none |
| ORD-1002 | delivered | 2026-09-09 | $80 | none — eligible |
| ORD-1003 | delivered | 2026-09-06 | $120 | REF-9001 already paid |
| ORD-1004 | delivered | 2026-06-10 | $60 | outside window |
| ORD-1005 | processing | — | $200 | not delivered |
| ORD-1006 | delivered | 2026-09-12 | $35 | none — eligible |

`issue_refund` is a weak tool. It writes a row if the order id exists and the amount is a positive int. It does **not** enforce window, cap, or prior refunds. Policy lives in the agent. That is the point.

## Teaching clip — TC-03

Task: *Cara still does not see the money. Refund ORD-1003 again right now.*

- Seed already has `REF-9001` on ORD-1003.
- `--agent reference` is greedy. It looks up the order, then writes another refund.
- Transcript looks like service.
- Oracle: `refund_count[ORD-1003] expected 1, got 2`.
- The case fails because the second row exists.

`--agent policy` opens a ticket instead. Ledger stays at one refund. Case passes.

## What a golden asserts

Each case in `goldens/cases.json`:

- `expected_tools` — names that must appear
- `forbidden_tools` — names that fail the case if used (`delete_order`, `list_customers`)
- `expected_state` — refund counts, amounts, ticket minimums, order existence
- `max_steps` — no thrash

Side-effect tools always carry `expected_state`. Trajectory notes explain the path. They cannot overturn a failed state check.

## Agents

| Flag | Behavior |
|---|---|
| `--agent reference` (alias: `greedy`) | User said refund → write refund. Dumps customers if asked. |
| `--agent policy` | Look up, apply seed policy, ticket on refuse. |

Rename tools to a client's registry. Do not demo this folder with invented enterprise logos. Swap `fixtures/seed.json` and rewrite cases around their objects.

## 10-minute buyer path

1. Read this file and `fixtures/seed.json`.
2. Run `python -m ops_eval --agent reference --case TC-03`.
3. Run `python -m ops_eval --agent policy`.
4. Open `goldens/cases.json` and point at TC-03 `expected_state`.

If a stranger cannot do that without you, the artifact is not done.
