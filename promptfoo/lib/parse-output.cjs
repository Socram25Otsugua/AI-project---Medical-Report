/**
 * Extract the first JSON object from an LLM response.
 * Used by Promptfoo JavaScript assertions (Node CJS).
 */
function parseJsonOutput(output) {
  const text = String(output ?? '');
  const match = text.match(/\{[\s\S]*\}/);
  if (!match) return null;
  try {
    return JSON.parse(match[0]);
  } catch {
    return null;
  }
}

function isNonEmptyStringArray(value) {
  return Array.isArray(value) && value.length > 0 && value.every((item) => typeof item === 'string' && item.trim().length > 0);
}

module.exports = { parseJsonOutput, isNonEmptyStringArray };
