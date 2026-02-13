import type { Entity } from "../models/base";

export class Repository<T extends Entity> {
    private items: Map<string, T> = new Map();

    async find(id: string): Promise<T | undefined> {
        return this.items.get(id);
    }

    async findAll(): Promise<T[]> {
        return Array.from(this.items.values());
    }

    async save(item: T): Promise<void> {
        this.items.set(item.id, item);
    }

    async delete(id: string): Promise<boolean> {
        return this.items.delete(id);
    }
}
