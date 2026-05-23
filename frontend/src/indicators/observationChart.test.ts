import { describe, expect, test } from 'vitest'
import {
  createEmptyObservationChart,
  getFirstColumnMissingFields,
  isObservationChartReadyForSend,
  observationChartToReportText,
  serializeObservationChart,
} from './observationChart'

describe('observation chart validation', () => {
  test('requires first column through temperature before send', () => {
    const chart = createEmptyObservationChart()
    expect(isObservationChartReadyForSend(chart)).toBe(false)
    expect(getFirstColumnMissingFields(chart).length).toBeGreaterThan(0)

    chart.columns[0] = {
      date: '2026-05-21',
      time: '14:30',
      general_condition: '2',
      consciousness: '1',
      oxygen_l_min: '2',
      breathing_frequency: '16',
      spo2: '97',
      capillary_response: '1',
      heart_rate: '72',
      blood_pressure: '125/78',
      pupil_reaction: '+ / +',
      temperature: '37.1',
    }

    expect(isObservationChartReadyForSend(chart)).toBe(true)
    expect(getFirstColumnMissingFields(chart)).toEqual([])
  })

  test('serializes populated columns into report text', () => {
    const chart = createEmptyObservationChart()
    chart.columns[0] = {
      date: '2026-05-21',
      time: '14:30',
      temperature: '37.1',
    }

    const text = observationChartToReportText(chart)
    expect(text).toContain('## Observation chart')
    expect(text).toContain('up to 8 columns')
    expect(text).toContain('Observation column 1')
    expect(text).toContain('Date: 2026-05-21')
    expect(text).toContain('Temp. measured in the mouth/rectal: 37.1')
    expect(serializeObservationChart(chart)).toContain('"date":"2026-05-21"')
  })
})
