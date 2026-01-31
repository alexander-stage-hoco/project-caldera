/**
 * TypeScript file with dead code patterns for testing I3_UNREACHABLE_CODE detection.
 */

// I3_UNREACHABLE_CODE: Code after return
function unreachableAfterReturn(x: number): number {
    if (x > 0) {
        return x * 2;
        console.log("This never runs");  // Unreachable
    }
    return 0;
}

// I3_UNREACHABLE_CODE: Code after throw
function unreachableAfterThrow(value: string | null): string {
    if (!value) {
        throw new Error("Value is required");
        console.log("Error thrown");  // Unreachable
    }
    return value;
}

// Multiple unreachable statements
function multipleUnreachable(type: string): string {
    switch (type) {
        case 'a':
            return 'option a';
            break;  // Unreachable after return
        case 'b':
            throw new Error('invalid');
            return 'never';  // Unreachable after throw
        default:
            return 'default';
    }
}

// GOOD: No unreachable code
function properFlow(x: number): number {
    if (x > 0) {
        console.log("Positive");
        return x;
    }
    console.log("Non-positive");
    return 0;
}

// GOOD: Proper error handling with types
function properErrorHandling(value: string | null): string {
    if (!value) {
        throw new Error("Value required");
    }
    return process(value);
}

function process(val: string): string {
    return val.toString();
}

export {
    unreachableAfterReturn,
    unreachableAfterThrow,
    multipleUnreachable,
    properFlow,
    properErrorHandling,
};
