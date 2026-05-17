'use strict';

/**
 * Formats a song title by trimming whitespace and collapsing inner spaces.
 * @param {string} title - Raw song title
 * @returns {string} Formatted title
 */
function formatTitle(title) {
  if (typeof title !== 'string') {
    throw new TypeError('Title must be a string');
  }
  return title.trim().replace(/\s+/g, ' ');
}

/**
 * Formats duration from total seconds to MM:SS string.
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string, e.g. "3:45"
 */
function formatDuration(seconds) {
  if (typeof seconds !== 'number' || seconds < 0) {
    throw new TypeError('Duration must be a non-negative number');
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Calculates the total duration of all tracks in a playlist array.
 * @param {Array} tracks - Array of track objects with a numeric duration field
 * @returns {number} Total duration in seconds
 */
function getTotalDuration(tracks) {
  if (!Array.isArray(tracks)) {
    throw new TypeError('Tracks must be an array');
  }
  return tracks.reduce((sum, track) => {
    return sum + (typeof track.duration === 'number' ? track.duration : 0);
  }, 0);
}

module.exports = { formatTitle, formatDuration, getTotalDuration };
