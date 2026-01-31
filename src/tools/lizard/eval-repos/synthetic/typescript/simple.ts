/**
 * Simple TypeScript module demonstrating basic types and interfaces.
 */

// Basic interface
interface User {
    id: number;
    name: string;
    email: string;
    active: boolean;
}

// Type alias
type UserId = number;

// Simple function with type annotations
function greet(user: User): string {
    return `Hello, ${user.name}!`;
}

// Arrow function with optional parameter
const formatEmail = (email: string, uppercase?: boolean): string => {
    return uppercase ? email.toUpperCase() : email.toLowerCase();
};

// Function with union type
function processId(id: UserId | string): string {
    return typeof id === "number" ? `ID-${id}` : id;
}

// Simple class
class Counter {
    private count: number = 0;

    increment(): void {
        this.count++;
    }

    decrement(): void {
        this.count--;
    }

    getCount(): number {
        return this.count;
    }
}

// Enum
enum Status {
    Pending = "pending",
    Active = "active",
    Completed = "completed",
}

// Array operations
function filterActiveUsers(users: User[]): User[] {
    return users.filter((user) => user.active);
}

// Object with readonly properties
interface Config {
    readonly apiUrl: string;
    readonly timeout: number;
}

const defaultConfig: Config = {
    apiUrl: "https://api.example.com",
    timeout: 5000,
};

export { User, UserId, Status, Counter, greet, formatEmail, processId, filterActiveUsers, defaultConfig };
