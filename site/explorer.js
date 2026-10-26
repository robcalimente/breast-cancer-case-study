import { confusion } from './explorer-model.mjs';

const container = document.querySelector('#threshold-explorer');
if (container) {
  const status = document.querySelector('#explorer-status');
  try {
    const response = await fetch(new URL('assets/development-explorer.json', import.meta.url));
    if (!response.ok) throw new Error('Prediction data unavailable.');
    const data = await response.json();
    const slider = document.querySelector('#threshold');
    const thresholds = [...new Set([...Array.from({ length: 1001 }, (_, i) => i / 1000), data.selected_threshold])].sort((a, b) => a - b);
    slider.max = String(thresholds.length - 1);
    slider.disabled = false;
    document.querySelector('#reset-threshold').disabled = false;
    const setText = (id, text) => { document.getElementById(id).textContent = text; };
    const percent = value => `${(100 * value).toFixed(1)}%`;
    function render() {
      const threshold = thresholds[Number(slider.value)];
      const result = confusion(data.samples, threshold);
      setText('threshold-value', threshold.toFixed(4));
      slider.setAttribute('aria-valuetext', `Malignant probability threshold ${threshold.toFixed(4)}`);
      for (const key of ['tp', 'tn', 'fp', 'fn']) setText(`${key}-count`, String(result[key]));
      setText('sensitivity', percent(result.sensitivity));
      setText('specificity', percent(result.specificity));
      const positives = result.tp + result.fn, negatives = result.tn + result.fp;
      setText('malignant-detected', `${result.tp}/${positives}`);
      setText('benign-cleared', `${result.tn}/${negatives}`);
      document.querySelector('#malignant-good').style.width = percent(result.sensitivity);
      document.querySelector('#malignant-error').style.width = percent(1 - result.sensitivity);
      document.querySelector('#benign-good').style.width = percent(result.specificity);
      document.querySelector('#benign-error').style.width = percent(1 - result.specificity);
      setText('explorer-status', `At threshold ${threshold.toFixed(4)}, ${result.fn} malignant samples are missed and ${result.fp} benign samples are flagged. Sensitivity ${percent(result.sensitivity)}; specificity ${percent(result.specificity)}.`);
    }
    function reset() { slider.value = String(thresholds.indexOf(data.selected_threshold)); render(); }
    slider.addEventListener('input', render);
    document.querySelector('#reset-threshold').addEventListener('click', reset);
    reset();
  } catch (error) {
    status.textContent = 'The interactive predictions could not be loaded. The development results and CSV remain available in the methods page.';
    status.classList.remove('visually-hidden');
  }
}
