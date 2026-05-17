'use strict';

const assert = require('assert');
const { formatTitle, formatDuration, getTotalDuration } = require('../src/utils');

// ─── formatTitle ───────────────────────────────────────────────────────────

describe('formatTitle()', () => {

  it('обрезает пробелы по краям строки', () => {
    assert.strictEqual(formatTitle('  Bohemian Rhapsody  '), 'Bohemian Rhapsody');
  });

  it('схлопывает несколько пробелов внутри строки в один', () => {
    assert.strictEqual(formatTitle('Stairway   to   Heaven'), 'Stairway to Heaven');
  });

  it('возвращает строку без изменений, если она уже чистая', () => {
    assert.strictEqual(formatTitle('Hotel California'), 'Hotel California');
  });

  it('выбрасывает TypeError, если передать не строку', () => {
    assert.throws(() => formatTitle(123), TypeError);
    assert.throws(() => formatTitle(null), TypeError);
  });

});

// ─── formatDuration ────────────────────────────────────────────────────────

describe('formatDuration()', () => {

  it('форматирует 225 секунд как "3:45"', () => {
    assert.strictEqual(formatDuration(225), '3:45');
  });

  it('добавляет ведущий ноль к секундам, если их меньше 10', () => {
    assert.strictEqual(formatDuration(65), '1:05');
  });

  it('форматирует 0 секунд как "0:00"', () => {
    assert.strictEqual(formatDuration(0), '0:00');
  });

  it('выбрасывает TypeError для отрицательного значения', () => {
    assert.throws(() => formatDuration(-1), TypeError);
  });

  it('выбрасывает TypeError, если передать не число', () => {
    assert.throws(() => formatDuration('3:45'), TypeError);
  });

});

// ─── getTotalDuration ──────────────────────────────────────────────────────

describe('getTotalDuration()', () => {

  it('возвращает 0 для пустого массива', () => {
    assert.strictEqual(getTotalDuration([]), 0);
  });

  it('суммирует длительность всех треков', () => {
    const tracks = [
      { title: 'Track A', duration: 120 },
      { title: 'Track B', duration: 240 }
    ];
    assert.strictEqual(getTotalDuration(tracks), 360);
  });

  it('игнорирует треки с нечисловой длительностью', () => {
    const tracks = [
      { title: 'Track A', duration: 100 },
      { title: 'Track B', duration: 'unknown' }
    ];
    assert.strictEqual(getTotalDuration(tracks), 100);
  });

  it('выбрасывает TypeError, если передать не массив', () => {
    assert.throws(() => getTotalDuration('not an array'), TypeError);
    assert.throws(() => getTotalDuration(null), TypeError);
  });

});
