/**
 * Test file for DD smell D1_EMPTY_CATCH detection.
 * Contains multiple empty catch blocks.
 */

interface User {
    id: number;
    name: string;
    email: string;
}

async function fetchUserData(userId: number): Promise<User | null> {
    try {
        const response = await fetch(`/api/users/${userId}`);
        return await response.json();
    } catch (error) {
        // D1_EMPTY_CATCH: Empty catch block - swallows errors silently
    }
    return null;
}

function parseJsonSafe<T>(jsonString: string): T | null {
    try {
        return JSON.parse(jsonString) as T;
    } catch (e) {
        // D1_EMPTY_CATCH: Another empty catch
    }
    return null;
}

async function processItems<T, R>(items: T[], transform: (item: T) => R): Promise<R[]> {
    const results: R[] = [];
    for (const item of items) {
        try {
            const processed = transform(item);
            results.push(processed);
        } catch (error) {
            // D1_EMPTY_CATCH: Empty catch in loop
        }
    }
    return results;
}

class DataService {
    private cache: Map<string, unknown> = new Map();

    async loadData(key: string): Promise<unknown> {
        try {
            const data = await this.fetchFromApi(key);
            this.cache.set(key, data);
            return data;
        } catch (err) {
            // D1_EMPTY_CATCH: Silently ignore errors
        }
        return null;
    }

    private async fetchFromApi(key: string): Promise<unknown> {
        return {};
    }

    clearCache(): void {
        try {
            this.cache.clear();
        } catch {
            // D1_EMPTY_CATCH: Bare catch with empty body
        }
    }
}

export { User, DataService, fetchUserData, parseJsonSafe, processItems };
