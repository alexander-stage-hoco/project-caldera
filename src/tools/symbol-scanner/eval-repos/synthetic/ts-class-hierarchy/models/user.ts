import type { Entity } from "./base";
import { BaseModel } from "./base";

export type UserRole = "admin" | "user" | "guest";

export enum Status {
    Active,
    Inactive,
    Banned,
}

export class User extends BaseModel {
    name: string;
    email: string;
    role: UserRole;
    status: Status;

    constructor(id: string, name: string, email: string) {
        super(id);
        this.name = name;
        this.email = email;
        this.role = "user";
        this.status = Status.Active;
    }

    validate(): boolean {
        return this.name.length > 0 && this.email.includes("@");
    }

    toJSON(): object {
        return {
            ...super.toJSON(),
            name: this.name,
            email: this.email,
            role: this.role,
            status: this.status,
        };
    }
}
