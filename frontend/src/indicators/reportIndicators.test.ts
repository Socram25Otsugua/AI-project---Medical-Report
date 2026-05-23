import { describe, expect, test } from 'vitest'
import { serializeObservationChart, createEmptyObservationChart } from './observationChart'
import { defaultIndicatorsState, OBSERVATION_CHART_STATE_KEY } from './schema'
import { completenessTierFromIndicators } from './reportIndicators'

describe('completenessTierFromIndicators', () => {
  test('returns red for mostly empty reports', () => {
    expect(completenessTierFromIndicators(defaultIndicatorsState())).toBe('r')
  })

  test('returns green when most fields are filled', () => {
    const state = defaultIndicatorsState()
    for (const key of Object.keys(state)) {
      if (key === OBSERVATION_CHART_STATE_KEY) continue
      state[key] = typeof state[key] === 'boolean' ? true : 'filled'
    }

    const chart = createEmptyObservationChart()
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
    state[OBSERVATION_CHART_STATE_KEY] = serializeObservationChart(chart)

    expect(completenessTierFromIndicators(state)).toBe('g')
  })
})
