import { greet, capitalize } from "./utils";
import { add, multiply } from "./math";

function main() {
    const name = capitalize("world");
    console.log(greet(name));
    console.log(add(2, 3));
    console.log(multiply(4, 5));
}

main();
