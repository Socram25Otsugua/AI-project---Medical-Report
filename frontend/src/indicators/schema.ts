export type FieldType = 'text' | 'textarea' | 'number' | 'select' | 'checkbox'

export type FieldOption = { label: string; value: string }

export type FieldDef = {
  key: string
  label: string
  type: FieldType
  placeholder?: string
  options?: FieldOption[]
  unit?: string
}

export type SectionDef = {
  id: string
  title: string
  description?: string
  fields: FieldDef[]
}

export const sections: SectionDef[] = [
  {
    id: 'identity',
    title: 'Patient identity',
    fields: [
      { key: 'patient_name', label: 'Name / title', type: 'text' },
      { key: 'birthdate_cpr', label: 'Birthdate / CPR', type: 'text' },
      {
        key: 'gender',
        label: 'Gender',
        type: 'select',
        options: [
          { label: '—', value: '' },
          { label: 'Female', value: 'female' },
          { label: 'Male', value: 'male' },
          { label: 'Other / unknown', value: 'other' },
        ],
      },
      { key: 'nationality', label: 'Nationality', type: 'text' },
      { key: 'date', label: 'Date', type: 'text', placeholder: 'YYYY-MM-DD' },
      { key: 'utc_time', label: 'UTC time', type: 'text', placeholder: 'HH:MM' },
    ],
  },
  {
    id: 'ship',
    title: 'Ship / contact context',
    fields: [
      { key: 'shipping_company', label: 'Shipping company', type: 'text' },
      { key: 'ship_name', label: 'Ship name', type: 'text' },
      { key: 'ship_email', label: 'Ship e-mail', type: 'text' },
      { key: 'satellite_call_no', label: 'Satellite call no.', type: 'text' },
      { key: 'call_signal', label: 'Call signal', type: 'text' },
      { key: 'coordinates', label: 'Coordinates', type: 'text' },
      { key: 'destination_eta', label: 'Destination / ETA', type: 'text' },
      { key: 'nearest_port_eta', label: 'Nearest port and ETA', type: 'text' },
      { key: 'medicine_chest', label: 'Medicine chest', type: 'text' },
    ],
  },
  {
    id: 'allergies_meds',
    title: 'Allergies / medicines',
    fields: [
      { key: 'has_medicine', label: 'Does the patient take any medicine?', type: 'checkbox' },
      { key: 'medicines_list', label: 'If yes, which medicine(s)?', type: 'textarea' },
      { key: 'has_allergies', label: 'Does the patient have any allergies?', type: 'checkbox' },
      { key: 'allergies_list', label: 'If yes, which allergy/allergies?', type: 'textarea' },
    ],
  },
  {
    id: 'airway',
    title: 'A — Airway',
    fields: [
      { key: 'airway_clear', label: 'Clear airways', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      { key: 'jaw_lift', label: 'Jaw lift performed', type: 'checkbox' },
      { key: 'suction_applied', label: 'Suction applied', type: 'checkbox' },
      { key: 'guedel_airway', label: 'Guedel airway used', type: 'checkbox' },
      { key: 'cpr_initiated_at', label: 'If no breathing: CPR initiated at', type: 'text', placeholder: 'HH:MM' },
      { key: 'oxygen_admin_l_min', label: 'Oxygen administered', type: 'number', unit: 'l/min' },
      { key: 'neck_back_suspected_injury', label: 'Neck / back: suspicion of injury', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
    ],
  },
  {
    id: 'breathing',
    title: 'B — Breathing',
    fields: [
      { key: 'breathing_frequency', label: 'Breathing frequency', type: 'number', unit: '/min' },
      {
        key: 'breathing_depth',
        label: 'Breathing depth/quality',
        type: 'select',
        options: [
          { label: '—', value: '' },
          { label: 'Fast', value: 'fast' },
          { label: 'Slow', value: 'slow' },
          { label: 'Shallow', value: 'shallow' },
          { label: 'Deep', value: 'deep' },
          { label: 'Normal', value: 'normal' },
        ],
      },
      { key: 'spo2_percent', label: 'Oxygen saturation', type: 'number', unit: '%' },
      { key: 'oxygen_l_min', label: 'Oxygen', type: 'number', unit: 'l/min' },
      {
        key: 'oxygen_method',
        label: 'Oxygen method',
        type: 'select',
        options: [
          { label: '—', value: '' },
          { label: 'Nasal cannula', value: 'nasal_cannula' },
          { label: 'Hudson mask', value: 'hudson_mask' },
        ],
      },
      { key: 'breathing_description_free', label: 'Description of breathing (free text)', type: 'textarea' },
    ],
  },
  {
    id: 'circulation',
    title: 'C — Circulation',
    fields: [
      { key: 'capillary_response_sec', label: 'Capillary response', type: 'number', unit: 'sec' },
      { key: 'venous_cannula_inserted', label: 'If >2 sec: venous cannula inserted', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      {
        key: 'skin_color',
        label: 'Skin color',
        type: 'select',
        options: [
          { label: '—', value: '' },
          { label: 'Pale', value: 'pale' },
          { label: 'Reddish', value: 'reddish' },
          { label: 'Bluish', value: 'bluish' },
          { label: 'Normal', value: 'normal' },
        ],
      },
      { key: 'skin_temp_humidity', label: 'Skin temperature/humidity (how does it feel?)', type: 'textarea' },
      { key: 'pulse_bpm', label: 'Pulse', type: 'number', unit: 'bpm' },
      {
        key: 'pulse_measured_at',
        label: 'Measured at',
        type: 'select',
        options: [
          { label: '—', value: '' },
          { label: 'Wrist', value: 'wrist' },
          { label: 'Neck', value: 'neck' },
          { label: 'Groin', value: 'groin' },
        ],
      },
      { key: 'bp_systolic', label: 'Blood pressure systolic', type: 'number', unit: 'mmHg' },
      { key: 'bp_diastolic', label: 'Blood pressure diastolic', type: 'number', unit: 'mmHg' },
    ],
  },
  {
    id: 'disability',
    title: 'D — Disability',
    fields: [
      {
        key: 'consciousness_level',
        label: 'Level of consciousness (1–4)',
        type: 'select',
        options: [
          { label: '—', value: '' },
          { label: '1 — Awake, alert and well orientated', value: '1' },
          { label: '2 — Unclear, but responds to questions', value: '2' },
          { label: '3 — Responds to pain stimuli', value: '3' },
          { label: '4 — Unconscious, unresponsive to pain stimuli', value: '4' },
        ],
      },
      { key: 'convulsions', label: 'Convulsions', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      { key: 'paralysis', label: 'Paralysis', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      { key: 'pupil_reaction_normal', label: 'Pupil reaction normal', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      { key: 'pupil_reaction_description', label: 'If abnormal: describe', type: 'textarea' },
    ],
  },
  {
    id: 'exposure',
    title: 'E — Exposure',
    fields: [
      { key: 'top_to_toe_done', label: 'Top-to-toe examination performed', type: 'checkbox' },
      { key: 'signs_injury_illness_yes', label: 'Signs of injury/illness not recognized under A–B–C–D', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      { key: 'signs_injury_illness_details', label: 'If yes: symptoms/findings', type: 'textarea' },
      { key: 'hypo_hyperthermia_yes', label: 'Signs of hypothermia/overheating', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      { key: 'hypo_hyperthermia_details', label: 'If yes: symptoms/findings', type: 'textarea' },
      { key: 'temperature_measured', label: 'Temperature measurement taken', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      { key: 'temp_mouth_c', label: 'Temperature (mouth)', type: 'number', unit: '°C' },
      { key: 'temp_alt_c', label: 'Temperature (alternative measurement)', type: 'number', unit: '°C' },
    ],
  },
  {
    id: 'problem',
    title: 'Problem description',
    fields: [
      { key: 'problem_description', label: 'What happened / where / when / symptoms', type: 'textarea' },
      { key: 'other_notes', label: 'Other', type: 'textarea' },
    ],
  },
  {
    id: 'actions',
    title: 'Actions / treatments',
    fields: [
      { key: 'performed_actions', label: 'Performed actions not described above', type: 'textarea' },
      { key: 'medication_before_contact', label: 'Medication given before contacting Radio Medical', type: 'textarea' },
      { key: 'medical_officer_name', label: 'Name/title of the Medical Officer', type: 'text' },
      { key: 'timestamps', label: 'Timeline (times)', type: 'textarea', placeholder: 'e.g. 12:10 oxygen started; 12:20 BP taken…' },
    ],
  },
  {
    id: 'observation',
    title: 'Observation chart (single row)',
    description: 'This app captures one observation snapshot. You can paste multiple rows in the free-text timeline if needed.',
    fields: [
      { key: 'obs_date', label: 'Date', type: 'text' },
      { key: 'obs_time', label: 'Time', type: 'text' },
      { key: 'general_condition_1_4', label: 'General condition (1–4)', type: 'select', options: [{ label: '—', value: '' }, { label: '1', value: '1' }, { label: '2', value: '2' }, { label: '3', value: '3' }, { label: '4', value: '4' }] },
      { key: 'obs_consciousness_1_4', label: 'Level of consciousness (1–4)', type: 'select', options: [{ label: '—', value: '' }, { label: '1', value: '1' }, { label: '2', value: '2' }, { label: '3', value: '3' }, { label: '4', value: '4' }] },
      { key: 'obs_oxygen_l_min', label: 'Oxygen', type: 'number', unit: 'l/min' },
      { key: 'obs_rr', label: 'Breathing frequency', type: 'number', unit: '/min' },
      { key: 'obs_crt_sec', label: 'Capillary response', type: 'number', unit: 'sec' },
      { key: 'obs_spo2', label: 'Oxygen saturation', type: 'number', unit: '%' },
      { key: 'obs_hr', label: 'Heart rate', type: 'number', unit: 'bpm' },
      { key: 'obs_bp_sys', label: 'Blood pressure systolic', type: 'number', unit: 'mmHg' },
      { key: 'obs_bp_dia', label: 'Blood pressure diastolic', type: 'number', unit: 'mmHg' },
      { key: 'obs_temp_mouth', label: 'Temp. (mouth)', type: 'number', unit: '°C' },
      { key: 'obs_pupil_reaction', label: 'Pupil reaction', type: 'text', placeholder: 'e.g. Normal / Normal' },
      { key: 'obs_venous_cannula', label: 'Venous cannula inserted', type: 'select', options: [{ label: '—', value: '' }, { label: 'Yes', value: 'yes' }, { label: 'No', value: 'no' }] },
      { key: 'obs_iv_fluid_drops_min', label: 'IV fluid', type: 'number', unit: 'drops/min' },
      { key: 'obs_fluid_intake', label: 'Fluid intake / drink', type: 'text' },
      { key: 'obs_urine_24h', label: '24-hour urine', type: 'text' },
      { key: 'obs_urine_sticks', label: 'Urine sticks', type: 'text' },
      { key: 'obs_blood_sugar', label: 'Blood sugar', type: 'number', unit: 'mmol/L' },
      { key: 'obs_malaria_test', label: 'Malaria test', type: 'text' },
    ],
  },
]

export type IndicatorsState = Record<string, string | number | boolean>

export function defaultIndicatorsState(): IndicatorsState {
  const state: IndicatorsState = {}
  for (const s of sections) {
    for (const f of s.fields) {
      if (f.type === 'checkbox') state[f.key] = false
      else state[f.key] = ''
    }
  }
  return state
}

