# dsh-warranty-calc — 质保期与索赔金额核对

`dsh-warranty-calc` 读取一份质保索赔台账——经销商表头加每笔索赔一行——核对这份台账自身的算术与期限自洽：每笔索赔是否记录了索赔单号或配件名称、索赔日期是否落在台账写明的质保期截止日之内、索赔时里程是否可解析为数值且不超过台账写明的质保里程、索赔金额是否等于数量乘单价、销售日期是否不晚于索赔日期、索赔单号是否重复。

## 它回答什么问题

| 你会问 | 它怎么答 |
|---|---|
| 台账没有填质保期截止日，索赔日期的核对就直接通过了？ | 不会。质保期截止日栏为空时，`WC-002` 报告自己进入 `skipped`：它不假定任何期限，也不用销售日期推算一个。该栏填了以后，它只核对索赔日期是否落在你写的销售日期与截止日之间；报了差异只表示与你写在台账里的期限不一致，不表示索赔已超保。 |
| 索赔金额与数量乘单价对不上，能查出来吗？ | 能。`WC-005` 核对 `claimAmount` 是否等于 `quantity` × `unitPrice`，超出 0.01 的容差即报出该行。它只覆盖配件金额：若本机构按「配件 + 工时 − 免赔额」结算（台账另有 `laborHours`、`laborRate`、`deductible` 三栏），本条会报差异——请把 `resultField` 指向配件金额栏，或停用本条。它不判断单价是否合理，也不判断该配件是否应当更换。 |
| 索赔时里程写的是 `48,600 公里`，还读得出来吗？超过上限又会怎样？ | 读得出来。`WC-003` 取其中的数字部分，`48600` 与 `48,600 公里` 都能解析；只有解析不了的里程才报出，它不判断里程是否超过上限。做这个比较的是 `WC-004`：它只拿台账写明的 `warrantyMiles` 上限相比，不内置任何里程数，命中只表示「超过你写在台账里的上限」，不表示索赔已超保——时间与里程是两个独立维度，以先到者为准。 |
| 同一个索赔单号在两行各出现一次。 | `WC-007` 会报出重复的 `claimNo`，比较时忽略空白字符，因为重复会让索赔金额合计被重复计算，也让厂商核销时对不上行。同一笔索赔分多行登记不同配件是正常的：请在配件名称栏加以区分。 |
| 某行的索赔单号和配件名称都没有填。 | `WC-001` 只在 `claimNo` 与 `partName` 一个都没填时报出该行，填了其中一个即可。它只核对最低可追溯信息是否填写，不判断该索赔是否在质保范围内、是否应当受理。 |
| 销售日期比索赔日期还晚。 | `WC-006` 拿台账里这两个日期相比，`saleDate` 晚于 `claimDate` 时报出该行。起算日取自你填的销售日期栏：本条所引条款写的是发票日与交付日两个起算点，本条不替你选定，实际起算以厂商承诺为准。日期解析不了会单独报出，不会静默跳过。 |

## 依据的标准

| 文件 | 文号 | 引用它的规则 |
|---|---|---|
| 《家用汽车产品修理更换退货责任规定》 | 市场监管总局令第43号（2021 年 7 月 22 日公布，自 2022 年 1 月 1 日起施行） | WC-001, WC-003, WC-005, WC-006, WC-007 |
| 各厂商质保政策与三包规定（本机构配置） | 无统一标准（本条依据为台账写明的质保期） | WC-002 |
| 各厂商质保政策（本机构配置） | 无统一标准（本条依据为台账写明的里程上限） | WC-004 |

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

| 项目 | 状态 |
|---|---|
| Harness | 对等版本范围 `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` —— 已实测同时接受 `0.2.0-rc.2` 与 `0.2.1-alpha.1`。**刻意不声明 `engines.dsh`**：它没有任何读取者，也无法拒装任何宿主 |
| Node | `^22.19.0 || >=24.0.0` |
| 平台 | 全平台（纯 ESM；无原生代码、无联网、不调用模型） |
| 工具模式 | `native` / `ptc` / `both` 均可；批量校验整个目录时建议 `ptc`，schema 成本只付一次 |

## What it does

规则表、字段说明与行为细节见 [README.md](README.md#what-it-does)（英文主版本）。本插件只列出材料与所引条款之间的字面差异，并对无法执行的检查在 `skipped` 中逐项说明。

## Install

```sh
dsh plugin --profile <name> add dsh-warranty-calc
dsh --profile <name> --dump-config | grep 'dsh-warranty-calc'
```

## Configuration

全部可调参数都在 `src/config.ts` 的 Schemastery schema 中，只改 `cordis.yml` 即可生效，无需改代码；逐条阈值在 `rules/` 下的规则库文件里。

| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rulesFile` | string | `rules/warranty-calc.yaml` | 规则库文件路径，相对插件包根目录 |
| `disabledRules` | string[] | `[]` | 要停用的规则 id 列表；每条都会出现在 `skipped` 中 |
| `onlyRules` | string[] | `[]` | 只执行这些规则 id；留空表示执行全部规则 |
| `skipNotes` | string | `""` | 附加到每条 `skipped` 说明后的备注 |
| `timeoutMs` | number | `120000` | 工具协作式超时预算（毫秒） |

## Material format

支持 JSON 与 YAML。完整字段示例见 [README.md](README.md#material-format)（英文主版本）。字段在读取层是可选的，由检查引擎校验，因此部分导出的材料会产生"缺项"类差异，而不是让程序崩溃。

## Rule sources

规则数据与代码分离，每条规则都带文件名、文号、按原文自身编号体系的条款号、逐字摘录与来源地址。加载期强制：摘录必须是真实引文且不少于八个字符；依据仅为原则性条款（`kind: derived-from-principle`，严重级上限 `warn`）或本机构配置（`kind: institutional-configuration`，上限 `info`）的检查不得标为 `error`。夸大依据的规则库会在加载期失败，而不会产出一份看起来很有底气的报告。

核验中确认的边界与"刻意没有作出的结论"见 [README.md](README.md#rule-sources)（英文主版本）与随包的 `rules/evidence/` 目录。

## Troubleshooting

- **插件装上了但工具不出现**：确认 `main` 指向 `lib/index.mjs` 且 `pnpm run build` 已生成该文件；`main` 写错会让加载器静默跳过该条目。
- **`dsh plugin add` 报版本不兼容**：peer 范围覆盖 `0.1.x` 与 `0.2.x`；若运行时在其之外，可显式豁免：`dsh plugin --profile <name> allow-version <包名@版本> --dsh-version <runtime> --accept-risk`
- **某条规则没有执行**：查看 `skipped` 数组，其中写明了规则 id 与原因。
- **`check` 报 `manifest-peers` 失败**：静态检查器比对的是一份早于 0.2 世代的硬编码 peer 范围；安装期的 peer 校验以运行时为准。这是 `dsh-plugin-dev` 的已知上游问题。
- **时间看起来偏移**：全部计算都是对输入字符串做墙上时钟运算，不做时区换算。

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-warranty-calc
```

第 4 项把 `../_shared` 的共享件同步进 `src/shared/`；每次改动共享件后都要重跑。

## License

[Apache License 2.0](LICENSE) © 2026 dsh-warranty-calc contributors.
