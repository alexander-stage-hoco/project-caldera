/**
 * Format a greeting message.
 * @param {string} name - The name to greet
 * @returns {string} The greeting
 */
export function greet(name) {
    return `Hello, ${name}!`;
}

export function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

export const VERSION = "1.0.0";

function _internal() {
    return 42;
}
