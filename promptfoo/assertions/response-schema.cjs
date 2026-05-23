const { parseJsonOutput, isNonEmptyStringArray } = require('../lib/parse-output.cjs');

module.exports = (output) => {
  const out = parseJsonOutput(output);
  if (!out) return false;

  return (
    isNonEmptyStringArray(out.immediate_actions) &&
    Array.isArray(out.monitoring_parameters) &&
    Array.isArray(out.escalation_criteria) &&
    Array.isArray(out.rationale_bullets) &&
    Array.isArray(out.questions_for_participants)
  );
};
