/**
 * Test file for DD smell D1_EMPTY_CATCH detection.
 * Contains multiple empty catch blocks.
 */

async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        return await response.json();
    } catch (error) {
        // D1_EMPTY_CATCH: Empty catch block - swallows errors silently
    }
}

function parseJsonSafe(jsonString) {
    try {
        return JSON.parse(jsonString);
    } catch (e) {
        // D1_EMPTY_CATCH: Another empty catch
    }
    return null;
}

function processItems(items) {
    const results = [];
    for (const item of items) {
        try {
            const processed = transformItem(item);
            results.push(processed);
        } catch (error) {
            // D1_EMPTY_CATCH: Empty catch in loop
        }
    }
    return results;
}

async function loadConfiguration() {
    try {
        const config = await readConfigFile();
        validateConfig(config);
        return config;
    } catch (err) {
        // D1_EMPTY_CATCH: Silently ignore config errors
    }
    return {};
}

function riskyDivision(a, b) {
    try {
        if (b === 0) throw new Error("Division by zero");
        return a / b;
    } catch {
        // D1_EMPTY_CATCH: Bare catch with empty body
    }
    return 0;
}

// Helper stubs
function transformItem(item) { return item; }
async function readConfigFile() { return {}; }
function validateConfig(config) { return true; }
