export function confusion(samples, threshold) {
  if (!Number.isFinite(threshold) || threshold < 0 || threshold > 1) throw new RangeError('Threshold must be between 0 and 1.');
  const counts = { tp: 0, tn: 0, fp: 0, fn: 0 };
  for (const sample of samples) {
    const { target, probability } = sample;
    if (![0, 1].includes(target) || !Number.isFinite(probability) || probability < 0 || probability > 1) throw new TypeError('Invalid prediction record.');
    const positive = probability >= threshold;
    counts[target === 1 ? (positive ? 'tp' : 'fn') : (positive ? 'fp' : 'tn')]++;
  }
  const positive = counts.tp + counts.fn;
  const negative = counts.tn + counts.fp;
  return { ...counts, n: samples.length,
    sensitivity: positive ? counts.tp / positive : null,
    specificity: negative ? counts.tn / negative : null };
}
