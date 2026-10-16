/* eslint-disable @typescript-eslint/no-require-imports */
const test = require('node:test');
const assert = require('node:assert/strict');
const { SerialJsonObjects, parseSignalLine } = require('./bridge-protocol');

const sample = {
  type: 'SOS', timestamp: '2026-09-04T13:35:43.340933Z', latitude: 18.65899,
  longitude: 73.8946419, peopleAffected: 3,
  conditions: ['evacuationRequired', 'trapped'], additionalDetails: 'help me i am here',
};

test('maps the Android payload without losing fields', () => {
  const signal = parseSignalLine(JSON.stringify(sample));
  assert.deepEqual(signal.report, sample);
  assert.equal(signal.manualLocation, '18.65899, 73.8946419');
  assert.match(signal.message, /People affected: 3/);
  assert.match(signal.message, /evacuation Required, trapped/);
  assert.match(signal.ticketId, /^TKT-\d{12}$/);
});

test('buffers compact JSON split at every possible serial boundary', () => {
  const bytes = Buffer.from(JSON.stringify(sample));
  for (let index = 0; index < bytes.length; index++) {
    const input = new SerialJsonObjects();
    assert.deepEqual(input.push(bytes.subarray(0, index)), []);
    const lines = input.push(bytes.subarray(index));
    assert.equal(lines.length, 1);
    assert.deepEqual(parseSignalLine(lines[0]).report, sample);
  }
});

test('ignores diagnostics, accepts pretty JSON and supports multiple packets', () => {
  const input = new SerialJsonObjects();
  const lines = input.push(Buffer.from(`Base Station Ready\nSOS JSON:\n${JSON.stringify(sample, null, 2)}\n{"type":"ACK","status":"BASE_STATION_RECEIVED"}\n${JSON.stringify({ ...sample, timestamp: '2026-09-04T13:36:43Z' })}\n`));
  assert.equal(lines.map(parseSignalLine).filter(Boolean).length, 2);
});

test('braces and escaped quotes inside details do not split a packet', () => {
  const report = { ...sample, additionalDetails: 'Victim says "help" near {stairwell}' };
  const input = new SerialJsonObjects();
  const objects = [];
  for (const byte of Buffer.from(JSON.stringify(report))) objects.push(...input.push(Buffer.from([byte])));
  assert.equal(objects.length, 1);
  assert.deepEqual(parseSignalLine(objects[0]).report, report);
});

test('rejects malformed field values before posting to the website', () => {
  for (const patch of [{ type: '' }, { timestamp: 'nope' }, { latitude: 91 }, { longitude: 'x' }, { peopleAffected: -1 }, { conditions: 'trapped' }, { additionalDetails: [] }]) {
    assert.throws(() => parseSignalLine(JSON.stringify({ ...sample, ...patch })));
  }
});
