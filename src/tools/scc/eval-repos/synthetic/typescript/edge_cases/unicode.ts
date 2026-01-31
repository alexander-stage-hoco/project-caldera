/**
 * Unicode content test file.
 */

// Unicode in strings
const greeting: string = 'Hello, 世界! 🌍';
const emojiMath: string = '1️⃣ + 2️⃣ = 3️⃣';

// Various Unicode characters
const translations: Record<string, string> = {
  hello: '你好',
  world: 'мир',
  welcome: 'مرحبا',
  goodbye: 'さようなら',
  thanks: 'धन्यवाद',
};

function getTranslation(key: string): string | undefined {
  return translations[key];
}

// Unicode in template literals
function formatGreeting(name: string): string {
  return `Привет, ${name}! 👋 Welcome to 日本!`;
}

// Emoji in function
function getStatus(success: boolean): string {
  return success ? '✅ Success' : '❌ Failed';
}

// Unicode regex
const emojiPattern = /[\u{1F300}-\u{1F9FF}]/gu;

function countEmojis(text: string): number {
  const matches = text.match(emojiPattern);
  return matches ? matches.length : 0;
}

export {
  greeting,
  emojiMath,
  translations,
  getTranslation,
  formatGreeting,
  getStatus,
  countEmojis,
};
