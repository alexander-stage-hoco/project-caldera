import { fetchUser, fetchAllUsers } from "../services/api";
import { Cache } from "../services/cache";

const userCache = new Cache(60000);

export async function getUser(id) {
    const cached = userCache.get(id);
    if (cached) return cached;

    const user = await fetchUser(id);
    userCache.set(id, user);
    return user;
}

export async function listUsers() {
    return fetchAllUsers();
}
