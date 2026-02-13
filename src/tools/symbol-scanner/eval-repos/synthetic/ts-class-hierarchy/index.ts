import { User, Status } from "./models/user";
import { Repository } from "./services/repo";

async function main(): Promise<void> {
    const repo = new Repository<User>();

    const user = new User("1", "Alice", "alice@example.com");
    console.log("Valid:", user.validate());

    await repo.save(user);
    const found = await repo.find("1");
    console.log("Found:", found?.toJSON());
}

main();
