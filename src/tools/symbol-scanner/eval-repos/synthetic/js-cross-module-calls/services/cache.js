export class Cache {
    constructor(ttl) {
        this.store = new Map();
        this.ttl = ttl;
    }

    get(key) {
        const entry = this.store.get(key);
        if (!entry) return null;
        if (Date.now() - entry.time > this.ttl) {
            this.store.delete(key);
            return null;
        }
        return entry.value;
    }

    set(key, value) {
        this.store.set(key, { value, time: Date.now() });
    }

    clear() {
        this.store.clear();
    }
}
