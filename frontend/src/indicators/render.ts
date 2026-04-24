import type { IndicatorsState, SectionDef } from './schema'

function valToString(v: string | number | boolean): string {
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  return String(v ?? '').trim()
}

export function indicatorsToReportText(sections: SectionDef[], state: IndicatorsState): string {
  const lines: string[] = []
  lines.push('Radio Medical Record (structured entry)')
  lines.push('')

  for (const s of sections) {
    lines.push(`## ${s.title}`)
    if (s.description) lines.push(s.description)
    for (const f of s.fields) {
      const v = state[f.key]
      const vs = valToString(v)
      if (vs === '' || vs === 'No') {
        // keep empties out; checkboxes false are noise
        continue
      }
      const unit = f.unit ? ` ${f.unit}` : ''
      lines.push(`- ${f.label}: ${vs}${unit}`)
    }
    lines.push('')
  }

  return lines.join('\n').trim() + '\n'
}

