/**
 * Fetch user data from API.
 */
export async function fetchUser(id) {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

/**
 * Fetch all users.
 */
export async function fetchAllUsers() {
    const response = await fetch("/api/users");
    return response.json();
}
