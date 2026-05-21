const { parseJsonOutput } = require('../lib/parse-output.cjs');

module.exports = (output) => {
  const out = parseJsonOutput(output);
  if (!out) return false;

  return (
    typeof out.completeness_score === 'number' &&
    out.completeness_score >= 0 &&
    out.completeness_score <= 100 &&
    Array.isArray(out.deficiencies) &&
    Array.isArray(out.safety_flags)
  );
};
