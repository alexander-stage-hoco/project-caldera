import { getUser, listUsers } from "./handlers/user";

async function main() {
    const users = await listUsers();
    console.log("All users:", users);

    const user = await getUser("123");
    console.log("User:", user);
}

main();
