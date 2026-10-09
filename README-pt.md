# dsh-warranty-calc — Verificação da coerência entre o período de garantia e o valor da reclamação

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-warranty-calc` lê um registo de reclamações de garantia —o cabeçalho do concessionário mais uma linha por reclamação— e verifica a aritmética e a coerência de prazos desse mesmo registo: se cada reclamação anota o seu número de reclamação ou o nome da peça, se a data da reclamação cai dentro da data de fim de garantia que o registo declara, se a quilometragem na reclamação é analisável como número e não excede o limite de quilometragem que o registo declara, se o valor reclamado é igual a quantidade × preço unitário, se a data de venda não é posterior à data da reclamação e se não há números de reclamação repetidos.

## Como é a saída

![Terminal demo of dsh-warranty-calc: real output over its WC-003 fixture](https://raw.githubusercontent.com/PerryLink/dsh-warranty-calc/main/docs/assets/dsh-warranty-calc-demo.png)

Saída real deste plugin sobre o seu próprio fixture de teste `WC-003` — não é uma simulação. O pacote de regras não inventa citações, por isso cada achado nomeia a cláusula aplicada e avisa que o seu texto não foi obtido.

## O que ele responde

| Você pergunta | O que ele responde |
|---|---|
| O registo não tem data de fim de garantia. A verificação da data da reclamação passa sem mais? | Não. `WC-002` aparece em `skipped` quando a coluna do fim de garantia está vazia: não presume nenhum prazo nem o calcula a partir da data de venda. Com a coluna preenchida verifica apenas que a data da reclamação fique entre a data de venda e a data de fim que você escreveu, e uma diferença significa que não concorda com o prazo do seu próprio registo, não que a reclamação esteja fora de garantia. |
| O valor reclamado não é igual a quantidade × preço unitário — isso é detetado? | Sim. `WC-005` assinala a linha quando `claimAmount` se afasta de `quantity` × `unitPrice` mais do que a tolerância de 0.01. Cobre apenas o valor das peças: se o seu registo liquida como peças + mão de obra − franquia (`laborHours`, `laborRate` e `deductible` são colunas à parte), a regra reporta uma diferença; aponte `resultField` para uma coluna de valor de peças ou desative a regra. Não julga se o preço unitário é razoável nem se a peça devia ter sido substituída. |
| A quilometragem está escrita como `48,600 公里` — ainda é lida? E se exceder o limite? | Sim. `WC-003` toma a parte numérica, pelo que `48600` e `48,600 公里` são analisados; só reporta a quilometragem que não consegue analisar e não julga se excede o limite. Dessa comparação trata `WC-004`, que apenas confronta com o limite `warrantyMiles` declarado pelo registo —nenhum valor está incorporado— e cujo achado significa «acima do limite que você registou», nunca «fora de garantia»: tempo e quilometragem são limites independentes, o que ocorrer primeiro. |
| O mesmo número de reclamação aparece em duas linhas. | `WC-007` reporta um `claimNo` repetido, ignorando espaços, porque a repetição duplica o total reclamado e impede o fabricante de casar a linha. Registar a mesma reclamação em várias linhas por peças diferentes é normal: distinga-as na coluna do nome da peça. |
| Uma linha não tem número de reclamação nem nome da peça. | `WC-001` assinala a linha apenas quando nem `claimNo` nem `partName` estão preenchidos: basta um dos dois. Verifica que esteja a informação mínima de rastreabilidade, não se a reclamação está dentro da garantia ou deve ser aceite. |
| A data de venda é posterior à data da reclamação. | `WC-006` compara as duas datas do registo e assinala a linha quando `saleDate` é posterior a `claimDate`. A data de início é tomada da sua coluna de data de venda: a cláusula citada pela regra nomeia a data da fatura e a data da entrega como pontos de início, a regra não escolhe por você e o início real segue o compromisso do fabricante. Uma data que não consegue analisar é reportada à parte, não é omitida em silêncio. |

## Normas que segue

| Documento | Número | Regras que o citam |
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

| Superfície | Estado |
|---|---|
| Harness | Faixa de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificada para aceitar tanto `0.2.0-rc.2` quanto `0.2.1-alpha.1`. **`engines.dsh` não é declarado**: não tem leitor e não pode recusar nenhum host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sem código nativo, sem rede, sem chamada ao modelo) |
| Modo de ferramenta | Funciona em `native`, `ptc` e `both`; para um diretório inteiro use `ptc` |

## What it does

A tabela de regras, os campos e o comportamento detalhado estão em [README.md](README.md#what-it-does) (versão principal em inglês). O plugin apenas lista divergências literais frente às cláusulas citadas e indica em `skipped` cada verificação que não pôde ser executada.

## Install

```sh
dsh plugin --profile <name> add dsh-warranty-calc
dsh --profile <name> --dump-config | grep 'dsh-warranty-calc'
```

## Configuration

Todos os parâmetros ajustáveis ficam no esquema Schemastery de `src/config.ts`, portanto mudam pelo `cordis.yml` sem editar código; os limites por regra ficam no pacote de regras sob `rules/`.

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `rulesFile` | string | `rules/warranty-calc.yaml` | Caminho do pacote de regras, relativo à raiz do pacote |
| `disabledRules` | string[] | `[]` | Ids de regras a desativar; cada uma aparece em `skipped` |
| `onlyRules` | string[] | `[]` | Executar apenas estas regras; vazio executa todas |
| `skipNotes` | string | `""` | Nota acrescentada a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Orçamento de tempo limite cooperativo da ferramenta |

## Material format

Aceita JSON ou YAML. O exemplo completo de campos está em [README.md](README.md#material-format) (versão principal em inglês). Os campos são opcionais na camada de leitura e validados pelo motor, de modo que uma exportação parcial gera achados sobre o que falta em vez de falhar.

## Rule sources

Os dados das regras ficam separados do código: cada regra traz documento, número, cláusula na numeração própria da fonte, trecho literal e URL de origem. O carregador impõe que o trecho seja citação real de pelo menos oito caracteres e que uma verificação baseada apenas em princípio geral (`kind: derived-from-principle`, teto `warn`) ou em política local (`kind: institutional-configuration`, teto `info`) nunca seja declarada `error`.

Os limites verificados e as conclusões deliberadamente **não** afirmadas estão em [README.md](README.md#rule-sources) (versão principal em inglês) e em `rules/evidence/`.

## Troubleshooting

- **O plugin instala mas a ferramenta não aparece**: confirme que `main` resolve para `lib/index.mjs` e que `pnpm run build` o gerou.
- **`dsh plugin add` recusa o pacote**: a faixa de peers cobre `0.1.x` e `0.2.x`; fora dela, conceda isenção explícita com `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Uma regra não executou**: leia o arranjo `skipped`.
- **`check` informa `manifest-peers` como falha**: problema conhecido do `dsh-plugin-dev`; o runtime aplica a compatibilidade na instalação.
- **Os horários parecem deslocados**: toda a aritmética é de hora local sobre as cadeias fornecidas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-warranty-calc
```

O último comando copia o kit compartilhado de `../_shared` para `src/shared/`; execute-o novamente após cada alteração compartilhada.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-warranty-calc contributors.
