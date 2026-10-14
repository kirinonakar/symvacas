import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {advancedStatisticsSchema} from '../advanced-statistics-schema.js';

test('generated Web schema preserves every Android definition, control, help and example', () => {
  const android = JSON.parse(readFileSync(new URL('../../app/src/main/assets/advanced_statistics.json', import.meta.url), 'utf8'));
  assert.deepEqual(advancedStatisticsSchema, android);
});
