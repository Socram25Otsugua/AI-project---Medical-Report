const { parseJsonOutput } = require('../lib/parse-output.cjs');

module.exports = (output) => {
  const out = parseJsonOutput(output);
  if (!out || typeof out.completeness_score !== 'number') return false;

  // Incomplete vitals documentation should not score as a strong submission.
  return out.completeness_score <= 70;
};
