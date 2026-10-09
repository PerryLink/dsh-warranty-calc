# dsh-warranty-calc — Verificación de la coherencia entre el período de garantía y el importe de la reclamación

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-warranty-calc` lee un registro de reclamaciones de garantía —la cabecera del concesionario más una fila por reclamación— y comprueba la aritmética y la coherencia de plazos de ese mismo registro: que cada reclamación anote su número de reclamación o el nombre de la pieza, que la fecha de la reclamación caiga dentro de la fecha de fin de garantía que el registro declara, que el kilometraje en la reclamación se pueda analizar como número y no supere el límite de kilometraje que el registro declara, que el importe reclamado sea igual a cantidad × precio unitario, que la fecha de venta no sea posterior a la fecha de la reclamación y que no se repitan los números de reclamación.

## Cómo se ve la salida

![Terminal demo of dsh-warranty-calc: real output over its WC-003 fixture](https://raw.githubusercontent.com/PerryLink/dsh-warranty-calc/main/docs/assets/dsh-warranty-calc-demo.png)

Salida real de este plugin sobre su propio fixture de prueba `WC-003` — no es un montaje. El paquete de reglas no inventa citas, así que cada hallazgo nombra la cláusula aplicada y advierte que su texto no se obtuvo.

## Qué responde

| Usted pregunta | Qué responde |
|---|---|
| El registro no tiene fecha de fin de garantía. ¿La comprobación de la fecha de la reclamación pasa sin más? | No. `WC-002` aparece en `skipped` cuando la columna del fin de garantía está vacía: no supone ningún plazo ni lo calcula a partir de la fecha de venta. Con la columna rellena solo comprueba que la fecha de la reclamación quede entre la fecha de venta y la fecha de fin que usted escribió, y una diferencia significa que no concuerda con el plazo de su propio registro, no que la reclamación esté fuera de garantía. |
| El importe reclamado no es igual a cantidad × precio unitario, ¿se detecta? | Sí. `WC-005` señala la fila cuando `claimAmount` se aparta de `quantity` × `unitPrice` más de la tolerancia de 0.01. Cubre solo el importe de las piezas: si su registro liquida como piezas + mano de obra − franquicia (`laborHours`, `laborRate` y `deductible` son columnas aparte), la regla informará de una diferencia; apunte `resultField` a una columna de importe de piezas o desactive la regla. No juzga si el precio unitario es razonable ni si la pieza debía sustituirse. |
| El kilometraje figura como `48,600 公里`, ¿se lee igual? ¿Y si supera el límite? | Sí. `WC-003` toma la parte numérica, así que `48600` y `48,600 公里` se analizan; solo informa del kilometraje que no puede analizar y no juzga si supera el límite. De esa comparación se ocupa `WC-004`, que solo contrasta con el límite `warrantyMiles` que declara el registro —ninguna cifra está incorporada— y cuyo hallazgo significa «por encima del límite que usted registró», nunca «fuera de garantía»: tiempo y kilometraje son límites independientes, el que se cumpla primero. |
| El mismo número de reclamación aparece en dos filas. | `WC-007` informa de un `claimNo` repetido, ignorando los espacios, porque la repetición duplica el total reclamado e impide que el fabricante case la línea. Registrar una misma reclamación en varias filas por piezas distintas es normal: distíngalas en la columna del nombre de la pieza. |
| Una fila no tiene número de reclamación ni nombre de pieza. | `WC-001` señala la fila solo cuando no está relleno ni `claimNo` ni `partName`: basta con uno de los dos. Comprueba que esté la información mínima de trazabilidad, no si la reclamación está dentro de garantía o debe aceptarse. |
| La fecha de venta es posterior a la fecha de la reclamación. | `WC-006` compara las dos fechas del registro y señala la fila cuando `saleDate` es posterior a `claimDate`. La fecha de inicio se toma de su columna de fecha de venta: la cláusula que cita la regla nombra la fecha de factura y la fecha de entrega como puntos de inicio, la regla no elige por usted y el inicio real sigue el compromiso del fabricante. Una fecha que no puede analizar se informa aparte, no se omite en silencio. |

## Normas que sigue

| Documento | Número | Reglas que lo citan |
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

| Superficie | Estado |
|---|---|
| Harness | Rango de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificado para aceptar tanto `0.2.0-rc.2` como `0.2.1-alpha.1`. **No se declara `engines.dsh`**: no tiene lector y no puede rechazar ningún host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sin código nativo, sin red, sin llamada al modelo) |
| Modo de herramienta | Funciona en `native`, `ptc` y `both`; para un directorio completo use `ptc` |

## What it does

La tabla de reglas, los campos y el comportamiento detallado están en [README.md](README.md#what-it-does) (versión principal en inglés). El plugin sólo enumera divergencias literales frente a las cláusulas citadas e indica en `skipped` cada comprobación que no pudo ejecutarse.

## Install

```sh
dsh plugin --profile <name> add dsh-warranty-calc
dsh --profile <name> --dump-config | grep 'dsh-warranty-calc'
```

## Configuration

Todos los parámetros ajustables viven en el esquema Schemastery de `src/config.ts`, por lo que se cambian desde `cordis.yml` sin tocar el código; los umbrales por regla están en el paquete de reglas bajo `rules/`.

| Clave | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `rulesFile` | string | `rules/warranty-calc.yaml` | Ruta del paquete de reglas, relativa a la raíz del paquete |
| `disabledRules` | string[] | `[]` | Ids de reglas que se dejan de ejecutar; cada una aparece en `skipped` |
| `onlyRules` | string[] | `[]` | Ejecutar solo estas reglas; vacío ejecuta todas |
| `skipNotes` | string | `""` | Nota añadida a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Presupuesto de tiempo de espera cooperativo de la herramienta |

## Material format

Acepta JSON o YAML. El ejemplo completo de campos está en [README.md](README.md#material-format) (versión principal en inglés). Los campos son opcionales en la capa de lectura y los valida el motor, de modo que una exportación parcial produce hallazgos sobre lo que falta en lugar de un fallo.

## Rule sources

Los datos de las reglas están separados del código: cada regla lleva documento, número, cláusula en la numeración propia de la fuente, extracto literal y URL de origen. El cargador impone que el extracto sea una cita real de al menos ocho caracteres y que una comprobación basada sólo en un principio general (`kind: derived-from-principle`, tope `warn`) o en una política local (`kind: institutional-configuration`, tope `info`) nunca se declare `error`.

Los límites verificados y las conclusiones deliberadamente **no** afirmadas están en [README.md](README.md#rule-sources) (versión principal en inglés) y en `rules/evidence/`.

## Troubleshooting

- **El plugin se instala pero la herramienta no aparece**: compruebe que `main` resuelve a `lib/index.mjs` y que `pnpm run build` lo generó.
- **`dsh plugin add` rechaza el paquete**: la faixa de peers cubre `0.1.x` y `0.2.x`; fuera de ella, conceda una exención explícita con `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Una regla no se ejecutó**: lea el arreglo `skipped`.
- **`check` informa `manifest-peers` como fallo**: es un problema conocido de `dsh-plugin-dev`; el runtime aplica la compatibilidad al instalar.
- **Los horarios parecen desplazados**: toda la aritmética es de hora local sobre las cadenas entregadas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-warranty-calc
```

El último comando copia el kit compartido de `../_shared` a `src/shared/`; vuelva a ejecutarlo tras cada cambio compartido.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-warranty-calc contributors.
