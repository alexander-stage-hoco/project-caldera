/**
 * JavaScript file with heavy duplication - multiple large duplicated blocks.
 */

function generateUserReport(users) {
    const lines = [];
    lines.push("=".repeat(60));
    lines.push("USER REPORT");
    lines.push("=".repeat(60));
    lines.push("");

    for (const item of users) {
        lines.push(`ID: ${item.id || "N/A"}`);
        lines.push(`Name: ${item.name || "Unknown"}`);
        lines.push(`Email: ${item.email || "N/A"}`);
        lines.push(`Status: ${item.status || "active"}`);
        lines.push(`Created: ${item.createdAt || "Unknown"}`);
        lines.push("-".repeat(40));
    }

    lines.push("");
    lines.push(`Total records: ${users.length}`);
    lines.push("=".repeat(60));
    return lines.join("\n");
}

function generateAdminReport(admins) {
    const lines = [];
    lines.push("=".repeat(60));
    lines.push("ADMIN REPORT");
    lines.push("=".repeat(60));
    lines.push("");

    for (const item of admins) {
        lines.push(`ID: ${item.id || "N/A"}`);
        lines.push(`Name: ${item.name || "Unknown"}`);
        lines.push(`Email: ${item.email || "N/A"}`);
        lines.push(`Status: ${item.status || "active"}`);
        lines.push(`Created: ${item.createdAt || "Unknown"}`);
        lines.push("-".repeat(40));
    }

    lines.push("");
    lines.push(`Total records: ${admins.length}`);
    lines.push("=".repeat(60));
    return lines.join("\n");
}

function generateGuestReport(guests) {
    const lines = [];
    lines.push("=".repeat(60));
    lines.push("GUEST REPORT");
    lines.push("=".repeat(60));
    lines.push("");

    for (const item of guests) {
        lines.push(`ID: ${item.id || "N/A"}`);
        lines.push(`Name: ${item.name || "Unknown"}`);
        lines.push(`Email: ${item.email || "N/A"}`);
        lines.push(`Status: ${item.status || "active"}`);
        lines.push(`Created: ${item.createdAt || "Unknown"}`);
        lines.push("-".repeat(40));
    }

    lines.push("");
    lines.push(`Total records: ${guests.length}`);
    lines.push("=".repeat(60));
    return lines.join("\n");
}

function validateUserInput(data) {
    const errors = [];
    if (!data.name) errors.push("Name is required");
    if (!data.email) errors.push("Email is required");
    if (!data.email?.includes("@")) errors.push("Invalid email format");
    if (!data.password) errors.push("Password is required");
    if ((data.password || "").length < 8) errors.push("Password must be at least 8 characters");
    if (!data.age) errors.push("Age is required");
    if ((data.age || 0) < 18) errors.push("Must be at least 18 years old");
    return errors;
}

function validateAdminInput(data) {
    const errors = [];
    if (!data.name) errors.push("Name is required");
    if (!data.email) errors.push("Email is required");
    if (!data.email?.includes("@")) errors.push("Invalid email format");
    if (!data.password) errors.push("Password is required");
    if ((data.password || "").length < 8) errors.push("Password must be at least 8 characters");
    if (!data.age) errors.push("Age is required");
    if ((data.age || 0) < 18) errors.push("Must be at least 18 years old");
    return errors;
}

module.exports = { generateUserReport, generateAdminReport, generateGuestReport, validateUserInput, validateAdminInput };
