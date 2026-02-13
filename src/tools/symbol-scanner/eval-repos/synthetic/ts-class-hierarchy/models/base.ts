/**
 * Base entity interface.
 */
export interface Entity {
    id: string;
    createdAt: Date;
}

/**
 * Serializable interface.
 */
export interface Serializable {
    toJSON(): object;
}

/**
 * Abstract base model.
 */
export abstract class BaseModel implements Entity, Serializable {
    id: string;
    createdAt: Date;

    constructor(id: string) {
        this.id = id;
        this.createdAt = new Date();
    }

    abstract validate(): boolean;

    toJSON(): object {
        return { id: this.id, createdAt: this.createdAt };
    }
}
