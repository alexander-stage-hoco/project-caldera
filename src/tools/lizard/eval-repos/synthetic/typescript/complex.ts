/**
 * Complex TypeScript module demonstrating advanced type features.
 * Includes generics, decorators, type guards, and advanced patterns.
 */

// Generic interface
interface Repository<T, K extends keyof T> {
    find(id: K): Promise<T | null>;
    findAll(): Promise<T[]>;
    save(entity: T): Promise<T>;
    delete(id: K): Promise<boolean>;
}

// Generic class with constraints
class InMemoryRepository<T extends { id: number }> implements Repository<T, "id"> {
    private items: Map<number, T> = new Map();

    async find(id: "id"): Promise<T | null> {
        // This is a simplified implementation
        return null;
    }

    async findById(id: number): Promise<T | null> {
        return this.items.get(id) || null;
    }

    async findAll(): Promise<T[]> {
        return Array.from(this.items.values());
    }

    async save(entity: T): Promise<T> {
        this.items.set(entity.id, entity);
        return entity;
    }

    async delete(id: "id"): Promise<boolean> {
        return true;
    }

    async deleteById(id: number): Promise<boolean> {
        return this.items.delete(id);
    }
}

// Conditional types
type NonNullable<T> = T extends null | undefined ? never : T;
type ExtractArrayType<T> = T extends (infer U)[] ? U : never;

// Mapped types
type Readonly<T> = {
    readonly [P in keyof T]: T[P];
};

type Partial<T> = {
    [P in keyof T]?: T[P];
};

type Required<T> = {
    [P in keyof T]-?: T[P];
};

// Type guards
interface Dog {
    bark(): void;
    breed: string;
}

interface Cat {
    meow(): void;
    color: string;
}

type Pet = Dog | Cat;

function isDog(pet: Pet): pet is Dog {
    return "bark" in pet;
}

function isCat(pet: Pet): pet is Cat {
    return "meow" in pet;
}

function handlePet(pet: Pet): string {
    if (isDog(pet)) {
        pet.bark();
        return `Dog of breed ${pet.breed}`;
    } else if (isCat(pet)) {
        pet.meow();
        return `Cat with ${pet.color} color`;
    }
    return "Unknown pet";
}

// Decorator factory (experimental)
function log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args: any[]) {
        console.log(`Calling ${propertyKey} with args:`, args);
        const result = originalMethod.apply(this, args);
        console.log(`${propertyKey} returned:`, result);
        return result;
    };
    return descriptor;
}

// Class with decorators
class Calculator {
    @log
    add(a: number, b: number): number {
        return a + b;
    }

    @log
    multiply(a: number, b: number): number {
        return a * b;
    }

    @log
    divide(a: number, b: number): number {
        if (b === 0) {
            throw new Error("Division by zero");
        }
        return a / b;
    }
}

// Advanced generics with multiple constraints
interface Comparable<T> {
    compareTo(other: T): number;
}

interface Serializable {
    serialize(): string;
}

class SortedList<T extends Comparable<T> & Serializable> {
    private items: T[] = [];

    add(item: T): void {
        this.items.push(item);
        this.items.sort((a, b) => a.compareTo(b));
    }

    getAll(): T[] {
        return [...this.items];
    }

    serializeAll(): string[] {
        return this.items.map((item) => item.serialize());
    }
}

// Template literal types
type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";
type ApiEndpoint = `/api/${string}`;
type ApiRoute = `${HttpMethod} ${ApiEndpoint}`;

// Recursive types
interface TreeNode<T> {
    value: T;
    children: TreeNode<T>[];
}

function traverseTree<T>(node: TreeNode<T>, callback: (value: T) => void): void {
    callback(node.value);
    for (const child of node.children) {
        traverseTree(child, callback);
    }
}

// Utility type implementations
type Pick<T, K extends keyof T> = {
    [P in K]: T[P];
};

type Omit<T, K extends keyof any> = Pick<T, Exclude<keyof T, K>>;

// Complex async patterns
interface AsyncResult<T, E = Error> {
    success: boolean;
    data?: T;
    error?: E;
}

async function tryCatch<T>(
    fn: () => Promise<T>
): Promise<AsyncResult<T>> {
    try {
        const data = await fn();
        return { success: true, data };
    } catch (error) {
        return { success: false, error: error as Error };
    }
}

// Event emitter with type safety
type EventMap = {
    userCreated: { userId: number; name: string };
    userDeleted: { userId: number };
    error: { message: string; code: number };
};

class TypedEventEmitter<T extends Record<string, any>> {
    private listeners: Map<keyof T, Set<(data: any) => void>> = new Map();

    on<K extends keyof T>(event: K, listener: (data: T[K]) => void): void {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }
        this.listeners.get(event)!.add(listener);
    }

    emit<K extends keyof T>(event: K, data: T[K]): void {
        const eventListeners = this.listeners.get(event);
        if (eventListeners) {
            for (const listener of eventListeners) {
                listener(data);
            }
        }
    }

    off<K extends keyof T>(event: K, listener: (data: T[K]) => void): void {
        const eventListeners = this.listeners.get(event);
        if (eventListeners) {
            eventListeners.delete(listener);
        }
    }
}

export {
    Repository,
    InMemoryRepository,
    Pet,
    Dog,
    Cat,
    isDog,
    isCat,
    handlePet,
    Calculator,
    SortedList,
    TreeNode,
    traverseTree,
    tryCatch,
    AsyncResult,
    TypedEventEmitter,
    EventMap,
};
