/**
 * dsh-warranty-calc — table shape and material contract.
 *
 * The plugin is data-only: this file declares which columns the material may use
 * and how they map onto canonical field names; the shared kit supplies the reader
 * and the check engine, and the rule pack declares every check. Adding a check
 * that fits an existing kind is a rule-pack edit, not a code change.
 */

import { canonicaliseRow, parseTable, type TableSpec } from './shared/table.ts'
import { runTableCheck, type TableCheckOptions, type TableInput } from './shared/rows.ts'
import type { Ruleset } from './shared/rules.ts'

/** Tool id exposed to the model, and the row id in `cordis.patch.yml`. */
export const TOOL_NAME = 'warranty_calc'

/** The register's column aliases, declared once so both the spec and the guard see them. */
const COLUMNS = {
  claimNo: ['索赔单号', '工单号', '编号', 'claimNo'],
  partNo: ['配件编号', '零件号', 'partNo'],
  partName: ['配件名称', '零件名称', '项目名称', 'partName'],
  saleDate: ['销售日期', '购机日期', '交付日期', 'saleDate'],
  mileageAtClaim: ['索赔时里程', '行驶里程', '里程', 'mileageAtClaim'],
  warrantyMonths: ['质保期月数', '质保期', '保修期', 'warrantyMonths'],
  warrantyMiles: ['质保里程', '质保公里数', 'warrantyMiles'],
  /**
   * The date the warranty period ends, as the register states it.
   *
   * The plugin never derives this from the sale date and a month count: months vary in
   * length and the period may start at delivery or registration rather than sale, so a
   * computed date would look precise while possibly being wrong. The user works it out
   * under the applicable policy and records it here.
   */
  warrantyEndAt: ['质保期截止日', '质保到期日', '保修截止日期', 'warrantyEndAt'],
  claimDate: ['索赔日期', '报修日期', '申报日期', 'claimDate'],
  quantity: ['数量', '更换数量', 'quantity'],
  unitPrice: ['单价', '配件单价', 'unitPrice'],
  laborHours: ['工时', '工时定额', 'laborHours'],
  laborRate: ['工时费率', '工时单价', 'laborRate'],
  deductible: ['免赔额', '客户承担', '自付额', 'deductible'],
  claimAmount: ['索赔金额', '结算金额', '金额', 'claimAmount'],
  decision: ['处理结论', '判定', 'decision'],
} as const

/** How the material declares its table. */
export const SPEC: TableSpec = {
  rowKeys: ['rows', 'items', 'claims', '索赔'],
  columns: COLUMNS,
  header: {
  dealer: ['dealer', '经销商', '服务站'],
  manufacturer: ['manufacturer', '厂商', '主机厂'],
  policyVersion: ['policyVersion', '质保政策版本'],
  checkedAt: ['checkedAt', '核对日期'],
  },
}

/** Fields the material must carry somewhere for the reader to accept it. */
export const REQUIRE_ANY_OF = [
  '索赔单号',
  'claimNo',
  '销售日期',
  'saleDate',
  '索赔日期',
  'claimDate',
  '索赔金额',
  'claimAmount',
]

/**
 * Parse the material and attach its canonical field names.
 * @param source - JSON or YAML text.
 * @param target - description of where the material came from.
 * @returns the normalized table, with each row's aliases resolved to field names.
 */
export function parseMaterial(source: string, target: string): TableInput {
  const table = parseTable(source, target, {
    ...SPEC,
    ...(REQUIRE_ANY_OF === undefined ? {} : { requireAnyOf: REQUIRE_ANY_OF }),
  })
  for (const row of table.rows) canonicaliseRow(row, SPEC)
  return table
}

/**
 * Run the rule pack against the material.
 * @param input - normalized table.
 * @param ruleset - validated rule pack.
 * @param options - plugin identity, clock value, rule selection and overrides.
 * @returns the report.
 */
export function runCheck(input: TableInput, ruleset: Ruleset, options: TableCheckOptions) {
  return runTableCheck(input, ruleset, options)
}

export type { TableCheckOptions, TableInput }
