const { parseJsonOutput } = require('../lib/parse-output.cjs');

const VITALS_KEYWORDS =
  /\b(vital|vitals|blood pressure|bp\b|pulse|heart rate|hr\b|spo2|oxygen saturation|respiratory rate|rr\b|temperature|temp\b|avpu|gcs)\b/i;

module.exports = (output) => {
  const out = parseJsonOutput(output);
  if (!out) return false;

  const questions = Array.isArray(out.questions_for_participants) ? out.questions_for_participants : [];
  const hasQuestions = questions.some((q) => typeof q === 'string' && q.trim().length > 0);

  const actions = Array.isArray(out.immediate_actions) ? out.immediate_actions.join(' ') : '';
  const addressesVitalsGap = VITALS_KEYWORDS.test(actions);

  // Sparse reports should yield either targeted questions or explicit vitals work-up steps.
  return hasQuestions || addressesVitalsGap;
};
