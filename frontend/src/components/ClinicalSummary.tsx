import type { AnalyzeResultV2 } from '../types'
import type { IndicatorsState } from '../indicators/schema'

type VitalTier = 'normal' | 'watch' | 'critical' | 'unknown'

type VitalCard = {
  key: string
  label: string
  value: string
  unit: string
  tier: VitalTier
  normalRange: string
  icon: 'heart' | 'spo2' | 'resp' | 'bp' | 'temp' | 'pain'
}

type AbcdeItem = {
  letter: string
  title: string
  tier: VitalTier
  detail: string
}

type ClinicalSummaryProps = {
  indicators: IndicatorsState
  result: AnalyzeResultV2
  vitalsQualityLabel: string
  vitalsQualityLevel: 'green' | 'yellow' | 'orange' | 'red' | 'unknown'
}

function fieldValue(v: string | number | boolean | undefined): string {
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  return String(v ?? '').trim()
}

function toNumber(value: string | number | boolean | undefined): number | null {
  const parsed = Number(String(value ?? '').trim())
  if (Number.isNaN(parsed)) return null
  return parsed
}

function tierLabel(tier: VitalTier): string {
  if (tier === 'normal') return 'Normal'
  if (tier === 'watch') return 'Watch'
  if (tier === 'critical') return 'Critical'
  return 'Unknown'
}

function heartRateTier(hr: number | null): VitalTier {
  if (hr === null) return 'unknown'
  if (hr < 50 || hr > 120) return 'critical'
  if (hr < 60 || hr > 100) return 'watch'
  return 'normal'
}

function spo2Tier(spo2: number | null): VitalTier {
  if (spo2 === null) return 'unknown'
  if (spo2 <= 90) return 'critical'
  if (spo2 < 95) return 'watch'
  return 'normal'
}

function rrTier(rr: number | null): VitalTier {
  if (rr === null) return 'unknown'
  if (rr < 10 || rr > 25) return 'critical'
  if (rr < 12 || rr > 20) return 'watch'
  return 'normal'
}

function bpTier(sys: number | null, dia: number | null): VitalTier {
  if (sys === null || dia === null) return 'unknown'
  if (sys < 90) return 'critical'
  if (sys >= 130 || dia >= 80) return 'watch'
  return 'normal'
}

function tempTier(temp: number | null): VitalTier {
  if (temp === null) return 'unknown'
  if (temp < 35 || temp >= 39) return 'critical'
  if (temp < 36.1 || temp > 37.5) return 'watch'
  return 'normal'
}

function painTier(score: number | null): VitalTier {
  if (score === null) return 'unknown'
  if (score >= 7) return 'critical'
  if (score >= 4) return 'watch'
  return 'normal'
}

function buildVitalCards(indicators: IndicatorsState): VitalCard[] {
  const hr = toNumber(indicators.pulse_bpm)
  const spo2 = toNumber(indicators.spo2_percent)
  const rr = toNumber(indicators.breathing_frequency)
  const sys = toNumber(indicators.bp_systolic)
  const dia = toNumber(indicators.bp_diastolic)
  const temp = toNumber(indicators.temp_mouth_c) ?? toNumber(indicators.temp_alt_c)
  const pain = toNumber(indicators.consciousness_level) ? 10 - toNumber(indicators.consciousness_level)! * 2 : null

  return [
    {
      key: 'hr',
      label: 'Heart Rate',
      value: hr !== null ? String(hr) : '—',
      unit: 'bpm',
      tier: heartRateTier(hr),
      normalRange: 'Normal 60–100',
      icon: 'heart',
    },
    {
      key: 'spo2',
      label: 'SpO2',
      value: spo2 !== null ? String(spo2) : '—',
      unit: '%',
      tier: spo2Tier(spo2),
      normalRange: 'Normal ≥ 95',
      icon: 'spo2',
    },
    {
      key: 'rr',
      label: 'Resp. Rate',
      value: rr !== null ? String(rr) : '—',
      unit: '/min',
      tier: rrTier(rr),
      normalRange: 'Normal 12–20',
      icon: 'resp',
    },
    {
      key: 'bp',
      label: 'Blood Pressure',
      value: sys !== null && dia !== null ? `${sys}/${dia}` : '—',
      unit: 'mmHg',
      tier: bpTier(sys, dia),
      normalRange: 'Normal < 130/80',
      icon: 'bp',
    },
    {
      key: 'temp',
      label: 'Temperature',
      value: temp !== null ? temp.toFixed(1) : '—',
      unit: '°C',
      tier: tempTier(temp),
      normalRange: 'Normal 36.1–37.5',
      icon: 'temp',
    },
    {
      key: 'pain',
      label: 'Pain Score',
      value: pain !== null ? String(pain) : '—',
      unit: '/10',
      tier: painTier(pain),
      normalRange: 'Normal ≤ 3',
      icon: 'pain',
    },
  ]
}

function abcdeFromIndicators(indicators: IndicatorsState): AbcdeItem[] {
  const airwayClear = fieldValue(indicators.airway_clear)
  const breathingDesc = fieldValue(indicators.breathing_description_free)
  const rr = fieldValue(indicators.breathing_frequency)
  const sys = fieldValue(indicators.bp_systolic)
  const dia = fieldValue(indicators.bp_diastolic)
  const hr = fieldValue(indicators.pulse_bpm)
  const cap = fieldValue(indicators.capillary_response_sec)
  const consciousness = fieldValue(indicators.consciousness_level)
  const exposureDetails =
    fieldValue(indicators.signs_injury_illness_details) || fieldValue(indicators.hypo_hyperthermia_details)

  const airwayTier: VitalTier =
    airwayClear === 'no' ? 'critical' : airwayClear === 'yes' || airwayClear === 'Yes' ? 'normal' : 'watch'
  const breathingTier: VitalTier = rrTier(toNumber(indicators.breathing_frequency))
  const circulationTier: VitalTier = bpTier(toNumber(indicators.bp_systolic), toNumber(indicators.bp_diastolic))
  const disabilityTier: VitalTier =
    consciousness === '4' ? 'critical' : consciousness === '3' ? 'watch' : consciousness ? 'normal' : 'unknown'
  const exposureTier: VitalTier = exposureDetails ? 'critical' : 'normal'

  return [
    {
      letter: 'A',
      title: 'Airway',
      tier: airwayTier,
      detail:
        airwayClear === 'yes'
          ? 'Patent, speaking in full sentences'
          : airwayClear === 'no'
            ? 'Airway compromise reported'
            : 'Airway status not fully documented',
    },
    {
      letter: 'B',
      title: 'Breathing',
      tier: breathingTier,
      detail: breathingDesc || (rr ? `Bilateral air entry, RR ${rr}` : 'Respiratory assessment pending'),
    },
    {
      letter: 'C',
      title: 'Circulation',
      tier: circulationTier,
      detail:
        sys && dia && hr
          ? `BP ${sys}/${dia}, HR ${hr}${cap ? `, cap refill ${cap}s` : ''}`
          : 'Circulation assessment incomplete',
    },
    {
      letter: 'D',
      title: 'Disability',
      tier: disabilityTier,
      detail:
        consciousness === '1'
          ? 'GCS 15, alert and oriented'
          : consciousness
            ? `Consciousness level ${consciousness}`
            : 'Neurologic status not documented',
    },
    {
      letter: 'E',
      title: 'Exposure',
      tier: exposureTier,
      detail: exposureDetails || 'No additional exposure findings documented',
    },
  ]
}

function VitalIcon({ icon }: { icon: VitalCard['icon'] }) {
  if (icon === 'heart') {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 20.5s-7-4.6-9-8.8C1.4 8.4 3.6 5.5 6.8 5.5c1.8 0 3.2.9 4 2.1.8-1.2 2.2-2.1 4-2.1 3.2 0 5.4 2.9 3.8 6.2-2 4.2-9 8.8-9 8.8Z"
          stroke="currentColor"
          strokeWidth="1.6"
        />
      </svg>
    )
  }
  if (icon === 'spo2') {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M4 12h2l2-5 3 10 2-6 2 4h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  }
  if (icon === 'resp') {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M8 8c0-2.2 1.8-4 4-4s4 1.8 4 4v8c0 2.2-1.8 4-4 4s-4-1.8-4-4V8Z" stroke="currentColor" strokeWidth="1.6" />
        <path d="M12 4V2M8 6 6 4M16 6l2-2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    )
  }
  if (icon === 'bp') {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="5" y="4" width="14" height="16" rx="3" stroke="currentColor" strokeWidth="1.6" />
        <path d="M9 9h6M9 13h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    )
  }
  if (icon === 'temp') {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 3v13.2a4 4 0 1 1-2 0V3a2 2 0 1 1 4 0Z" stroke="currentColor" strokeWidth="1.6" />
      </svg>
    )
  }
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3 4 21h16L12 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M12 10v4M12 17h.01" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function DetailIcon({ kind }: { kind: 'name' | 'birth' | 'gender' | 'language' | 'ship' | 'location' }) {
  const common = { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none' as const, 'aria-hidden': true as const }
  if (kind === 'name') {
    return (
      <svg {...common}>
        <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.6" />
        <path d="M5 20c1.5-3.5 4.2-5.5 7-5.5s5.5 2 7 5.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    )
  }
  if (kind === 'birth') {
    return (
      <svg {...common}>
        <rect x="4" y="6" width="16" height="14" rx="2" stroke="currentColor" strokeWidth="1.6" />
        <path d="M8 4v4M16 4v4M4 11h16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    )
  }
  if (kind === 'gender') {
    return (
      <svg {...common}>
        <circle cx="10" cy="8" r="3" stroke="currentColor" strokeWidth="1.6" />
        <path d="M14 6l4-4M18 2v4M16 4h4M10 11v9M7 17h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    )
  }
  if (kind === 'language') {
    return (
      <svg {...common}>
        <path d="M4 6h8M8 6v12M4 12h8M14 8c2 0 4 2 4 5s-2 5-4 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    )
  }
  if (kind === 'ship') {
    return (
      <svg {...common}>
        <path d="M4 18h16l-2-8H6l-2 8ZM8 10V6h8v4" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      </svg>
    )
  }
  return (
    <svg {...common}>
      <path d="M12 21s6-5.2 6-10a6 6 0 1 0-12 0c0 4.8 6 10 6 10Z" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="11" r="2" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  )
}

export function ClinicalSummary({ indicators, result, vitalsQualityLabel, vitalsQualityLevel }: ClinicalSummaryProps) {
  const vitals = buildVitalCards(indicators)
  const abcde = abcdeFromIndicators(indicators)
  const filledAbcde = abcde.filter((item) => item.detail && item.tier !== 'unknown').length

  const patientName = fieldValue(indicators.patient_name) || 'Unnamed patient'
  const gender = fieldValue(indicators.gender) || '—'
  const cpr = fieldValue(indicators.birthdate_cpr) || '—'
  const nationality = fieldValue(indicators.nationality) || '—'
  const ship = fieldValue(indicators.ship_name) || '—'
  const coordinates = fieldValue(indicators.coordinates) || '—'
  const measuredAt = fieldValue(indicators.utc_time) || new Date().toUTCString().slice(17, 22) + ' UTC'

  const chiefComplaint = fieldValue(indicators.problem_description) || 'Chief complaint not documented.'
  const workingTitle =
    result.patient_evaluation?.suspected_problems?.[0] ||
    result.patient_evaluation?.summary?.split('.')[0] ||
    'Clinical assessment in progress'
  const workingBody =
    result.patient_evaluation?.summary ||
    [
      ...(result.response.immediate_actions ?? []),
      ...(result.response.monitoring_parameters ?? []),
    ]
      .filter(Boolean)
      .join(' ') ||
    'Awaiting final clinical impression.'

  const dialClass =
    vitalsQualityLevel === 'green'
      ? 'csDialGreen'
      : vitalsQualityLevel === 'yellow'
        ? 'csDialYellow'
        : vitalsQualityLevel === 'orange'
          ? 'csDialOrange'
          : vitalsQualityLevel === 'red'
            ? 'csDialRed'
            : 'csDialUnknown'

  const detailCards = [
    { kind: 'name' as const, label: 'Name', value: patientName },
    { kind: 'birth' as const, label: 'Birthdate / CPR', value: cpr },
    { kind: 'gender' as const, label: 'Gender', value: gender },
    { kind: 'language' as const, label: 'Language', value: nationality },
    { kind: 'ship' as const, label: 'Ship', value: ship },
    { kind: 'location' as const, label: 'Coordinates', value: coordinates },
  ]

  return (
    <div className="clinicalSummary">
      <div className="csHero">
        <div className="csHeroMain">
          <div className="csDraftBadge">
            <span className="csDraftDot" aria-hidden="true" />
            Clinical summary · Draft
          </div>
          <h2 className="csPatientName">{patientName}</h2>
          <div className="csDemographics">
            {gender} · CPR {cpr} · {nationality}
          </div>
          <div className="csContextTags">
            <span className="csContextTag">
              <DetailIcon kind="ship" />
              {ship}
            </span>
            <span className="csContextTag">
              <DetailIcon kind="location" />
              {coordinates}
            </span>
          </div>
        </div>
        <div className={`csVitalsDial ${dialClass}`}>
          <div className="csVitalsDialInner">
            <div className="csVitalsDialValue">{vitalsQualityLabel}</div>
            <div className="csVitalsDialLabel">Vitals quality</div>
          </div>
        </div>
      </div>

      <div className="csBodyGrid">
        <aside className="csSidebar">
          <div className="csSidebarHead">
            <div className="csSidebarTitle">Patient details</div>
            <div className="csSidebarTag">Identity</div>
          </div>
          <div className="csDetailList">
            {detailCards.map((card) => (
              <div key={card.label} className="csDetailCard">
                <div className="csDetailIcon">
                  <DetailIcon kind={card.kind} />
                </div>
                <div>
                  <div className="csDetailLabel">{card.label}</div>
                  <div className="csDetailValue">{card.value}</div>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <div className="csMain">
          <section className="csComplaintCard">
            <div className="csSectionEyebrow">Chief complaint</div>
            <div className="csComplaintTitle">
              <span className="csWarningIcon" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M12 3 2 21h20L12 3Z" fill="currentColor" />
                  <path d="M12 10v4M12 17h.01" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </span>
              {chiefComplaint.split(/[.!?\n]/)[0]?.trim() || chiefComplaint}
            </div>
            <p className="csComplaintBody">{chiefComplaint}</p>
          </section>

          <section className="csVitalsSection">
            <div className="csVitalsHead">
              <div className="csVitalsTitle">Vitals</div>
              <div className="csVitalsTime">Measured {measuredAt}</div>
            </div>
            <div className="csVitalsGrid">
              {vitals.map((vital) => (
                <div key={vital.key} className={`csVitalCard csVital-${vital.tier}`}>
                  <div className="csVitalTop">
                    <div className="csVitalIcon">
                      <VitalIcon icon={vital.icon} />
                    </div>
                    <div className={`csVitalStatus csStatus-${vital.tier}`}>• {tierLabel(vital.tier)}</div>
                  </div>
                  <div className="csVitalValueRow">
                    <span className="csVitalValue">{vital.value}</span>
                    <span className="csVitalUnit">{vital.unit}</span>
                  </div>
                  <div className="csVitalNormal">{vital.normalRange}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="csAbcdeCard">
            <div className="csAbcdeHead">
              <div className="csAbcdeTitle">ABCDE recap</div>
              <div className="csAbcdeCount">{filledAbcde} of 5 sections</div>
            </div>
            <div className="csAbcdeGrid">
              {abcde.map((item) => (
                <div key={item.letter} className="csAbcdeItem">
                  <div className="csAbcdeItemTop">
                    <div className="csAbcdeLetter">{item.letter}</div>
                    <div className="csAbcdeItemTitle">{item.title}</div>
                    <div className={`csAbcdeStatus csStatus-${item.tier}`}>{tierLabel(item.tier).toUpperCase()}</div>
                  </div>
                  <div className="csAbcdeDetail">{item.detail}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="csImpressionCard">
            <div className="csImpressionHead">
              <div className="csImpressionIcon" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M8 4h8l4 4v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinejoin="round"
                  />
                  <path d="M14 4v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="csImpressionEyebrow">Working impression</div>
            </div>
            <h3 className="csImpressionTitle">{workingTitle}</h3>
            <p className="csImpressionBody">{workingBody}</p>
          </section>
        </div>
      </div>

      <footer className="csFooter">
        <div>⚓ Danish Maritime Authority · Radio Medical</div>
        <div>
          Generated {measuredAt} · Draft v1
        </div>
      </footer>
    </div>
  )
}
