# dsh-warranty-calc

**Boundary:** this plugin checks a **质保索赔台账** for arithmetic and period self-consistency — that a claim
records its number or part name, that the claim date falls inside the warranty end date the register states,
that mileage parses and does not exceed the mileage cap the register states, that the claim amount equals
quantity × unit price, that the sale date does not follow the claim date, and that claim numbers do not repeat.
It does **not** decide whether a claim should be accepted, whether a failure is covered, or whether it was
caused by misuse or normal wear.

> ### ⚠️ Warranty policy is the manufacturer's, and this pack does not pretend to quote one
>
> Period length, mileage cap, labour rates and deductibles are set by **each manufacturer's warranty policy**
> and by the three-guarantee rules for the relevant product category. **No unified standard exists**, so every
> rule's `basis` says exactly that and stays at `warn` or `info`.
>
> Three consequences are worth knowing before trusting a finding:
>
> - **The plugin never derives a warranty end date.** It does not compute "sale date + 36 months", because
>   months vary in length and the period may start at delivery or at registration rather than at sale — a
>   computed date would look precise while possibly being wrong. **You work the date out under the applicable
>   policy and record it in the 质保期截止日 column**, and `WC-002` compares against that.
> - **`WC-004`'s mileage cap comes from the register too.** No figure is built in, and a finding means "above
>   the cap you recorded", never "out of warranty" — time and mileage are **independent limits, whichever comes
>   first**, and policies differ on what happens past either.
> - **`WC-005` covers parts only.** Real claim amounts often add labour and material and subtract a deductible,
>   and this register has separate columns for those. A register settling as "parts + labour − deductible" will
>   report a difference; repoint `resultField` at a parts-amount column, or disable the rule.
>
> **Every `excerpt` in the rule pack says, in so many words, that the clause text was not obtained.** When the
> texts are in hand, replace each `excerpt` with the real clause and raise `kind` to `direct`.

## Compatibility

| Surface | Status |
|---|---|
| Harness | Peer range `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verified to accept both `0.2.0-rc.2` and `0.2.1-alpha.1`. `engines.dsh` is deliberately not declared: it has no reader and cannot reject a host |
| Node | `^22.19.0 || >=24.0.0` |
| Platforms | All (plain ESM; no native code, no network, no model call) |
| Tool mode | Works in `native`, `ptc` and `both`; for a batch of claims use `ptc` |

## What it does

Registers the `warranty_calc` tool. It reads one claim register — the dealer header plus one row per claim —
applies a versioned rule pack, and returns a report.

| Rule | Check | Severity | Basis kind |
|---|---|---|---|
| `WC-001` | the claim records its number or part name | warn | principle |
| `WC-002` | the claim date falls inside the recorded warranty end | info | local |
| `WC-003` | mileage at claim parses as a number | warn | principle |
| `WC-004` | mileage at claim does not exceed the recorded cap | info | local |
| `WC-005` | the claim amount equals quantity × unit price | warn | principle |
| `WC-006` | the sale date does not follow the claim date | warn | principle |
| `WC-007` | claim numbers do not repeat | warn | principle |

## Install

```sh
dsh plugin --profile <name> add dsh-warranty-calc
dsh --profile <name> --dump-config | grep 'dsh-warranty-calc'
```

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `rulesFile` | string | `rules/warranty-calc.yaml` | Rule-pack path, relative to the package root |
| `disabledRules` | string[] | `[]` | Rule ids to stop running; each appears in `skipped` |
| `onlyRules` | string[] | `[]` | Run only these rule ids; empty runs every rule |
| `skipNotes` | string | `""` | Note appended to every `skipped` reason |
| `timeoutMs` | number | `120000` | Cooperative tool timeout budget |

Rule-level parameters worth knowing:

- `WC-002` needs the register's 质保期截止日 / `warrantyEndAt` column; without it the rule reports itself in
  `skipped`. The plugin never computes the date from a month count.
- `WC-004` needs `warrantyMiles` from the register. No mileage figure is built in.
- `WC-005` `resultField` / `factorFields` / `tolerance` — the parts arithmetic; repoint it if your settlement
  includes labour and a deductible.

## Material format

The tool accepts JSON or YAML:

```yaml
dealer: 某某服务站
manufacturer: 某某厂商
policyVersion: 2026 版质保政策
rows:
  - { 索赔单号: SP-2026-0018, 配件名称: 前制动片, 销售日期: 2024-03-10,
      索赔时里程: '48600', 质保期月数: '36', 质保里程: '100000',
      质保期截止日: 2027-03-09, 索赔日期: 2026-03-05,
      数量: '2', 单价: '180', 索赔金额: '360', 处理结论: 同意索赔 }
```

Column names are matched case-insensitively and ignoring spaces, underscores and hyphens; the register's own
column names are kept, so a finding names the column it read.

## Rule sources

Rule data lives in `rules/warranty-calc.yaml`. Because warranty policy is a manufacturer's instrument rather
than a standard, the pack's `basis` entries say so explicitly instead of citing one. The load-time guard still
requires a document, clause, excerpt and source per rule, and still forbids a locally configured check from
being `error`.

## Troubleshooting

- **`WC-002` reports itself as skipped.** The register records no warranty end date. The plugin will not
  compute one: months vary in length and the period may start at delivery or registration.
- **`WC-002` fires although I believe the claim is covered.** The recorded end date disagrees with the claim
  date. Recheck how the end date was worked out under the applicable policy.
- **`WC-004` fires on a claim I consider covered.** The mileage exceeds the cap you recorded — but time and
  mileage are independent limits, and this finding alone does not mean the claim is out of warranty.
- **`WC-005` fires on a correct settlement.** The amount probably includes labour and a deductible. Point
  `resultField` at a parts-only column, or disable the rule.
- **`WC-006` fires on dates I can read.** The reader accepts `2026-03-05` or `2026-03-05 09:30`;
  `2026年3月5日` is reported as unparseable on purpose.
- **The plugin installs but the tool never appears.** Check that `main` resolves to `lib/index.mjs` and
  that `pnpm run build` produced it; a wrong `main` makes the loader skip the entry silently.
- **`dsh plugin add` refuses the package as incompatible.** The peer range covers `0.1.x` and `0.2.x`; if
  your runtime sits outside it, grant an explicit exemption:
  `dsh plugin --profile <name> allow-version dsh-warranty-calc@0.1.0 --dsh-version <runtime> --accept-risk`
- **`check` reports `manifest-peers` as failed.** The static checker compares against a hard-coded peer
  range that predates the 0.2 line. The runtime enforces peer compatibility at install time, so the
  declared range is the correct one; this is a known upstream issue in `dsh-plugin-dev`.

## Development

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm test            # vitest, the shared table-plugin suite plus paired fixtures
pnpm run build       # tsdown -> lib/index.mjs + lib/index.d.mts
node ../scripts/sync-shared.mjs dsh-warranty-calc   # refresh src/shared from ../_shared
```

The plugin is **data-only**: `src/model.ts` declares the table shape, the shared kit supplies the reader and
the check engine, and the rule pack declares every check.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-warranty-calc contributors.
