import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { confusion } from '../site/explorer-model.mjs';

const data = JSON.parse(readFileSync(new URL('../site/assets/development-explorer.json', import.meta.url)));
const reference = JSON.parse(readFileSync(new URL('../site/assets/explorer-reference.json', import.meta.url)));

for (const expected of reference) {
  test(`browser counts agree with Python at threshold ${expected.threshold}`, () => {
    const actual = confusion(data.samples, expected.threshold);
    for (const key of ['tp', 'tn', 'fp', 'fn', 'sensitivity', 'specificity']) assert.equal(actual[key], expected[key]);
    assert.equal(actual.tp + actual.tn + actual.fp + actual.fn, data.samples.length);
  });
}
test('threshold equality is classified positive', () => {
  assert.equal(confusion([{ target: 1, probability: .5 }], .5).tp, 1);
});
test('invalid predictions and thresholds are rejected', () => {
  assert.throws(() => confusion(data.samples, NaN));
  assert.throws(() => confusion([{ target: 'M', probability: .5 }], .5));
});
