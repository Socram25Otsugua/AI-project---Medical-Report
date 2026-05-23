import { describe, expect, test } from 'vitest'
import { defaultIndicatorsState, sections } from './schema'
import { indicatorsToReportText } from './render'

describe('indicatorsToReportText', () => {
  test('keeps explicit No values for key clinical negatives', () => {
    const state = defaultIndicatorsState()
    state.patient_name = 'John Doe'
    state.has_allergies = false
    state.has_medicine = false

    const text = indicatorsToReportText(sections, state)

    expect(text).toContain('Does the patient have any allergies?: No')
    expect(text).toContain('Does the patient take any medicine?: No')
  })
})
