/**
 * Unicode content test file.
 */

// Unicode in strings
const greeting = 'Hello, 世界! 🌍';
const emojiMath = '1️⃣ + 2️⃣ = 3️⃣';

// Various Unicode characters
const translations = {
  hello: '你好',
  world: 'мир',
  welcome: 'مرحبا',
  goodbye: 'さようなら',
  thanks: 'धन्यवाद',
};

function getTranslation(key) {
  return translations[key] ?? null;
}

// Unicode in template literals
function formatGreeting(name) {
  return `Привет, ${name}! 👋 Welcome to 日本!`;
}

// Emoji in function
function getStatus(success) {
  return success ? '✅ Success' : '❌ Failed';
}

// Unicode regex
const emojiPattern = /[\u{1F300}-\u{1F9FF}]/gu;

function countEmojis(text) {
  const matches = text.match(emojiPattern);
  return matches ? matches.length : 0;
}

module.exports = {
  greeting,
  emojiMath,
  translations,
  getTranslation,
  formatGreeting,
  getStatus,
  countEmojis,
};
