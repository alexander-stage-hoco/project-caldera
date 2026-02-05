/**
 * Test file for DOM-based XSS vulnerability detection.
 * Contains patterns detected by p/javascript ruleset.
 */

// XSS_VULNERABILITY: document.write with user input
function unsafeDocumentWrite(userInput) {
    document.write("<div>" + userInput + "</div>");
}

// XSS_VULNERABILITY: innerHTML assignment
function unsafeInnerHTML(element, content) {
    element.innerHTML = content;
}

// XSS_VULNERABILITY: outerHTML assignment
function unsafeOuterHTML(element, content) {
    element.outerHTML = "<span>" + content + "</span>";
}

// CODE_INJECTION: eval with user input
function unsafeEval(code) {
    return eval(code);
}

// CODE_INJECTION: Function constructor
function unsafeFunctionConstructor(body) {
    return new Function(body);
}

// CODE_INJECTION: setTimeout with string
function unsafeSetTimeout(code) {
    setTimeout(code, 1000);
}

// CODE_INJECTION: setInterval with string
function unsafeSetInterval(code) {
    setInterval(code, 1000);
}

// COMMAND_INJECTION: child_process exec
const { exec } = require('child_process');

function unsafeExec(userCommand) {
    exec(userCommand, (error, stdout, stderr) => {
        console.log(stdout);
    });
}

// COMMAND_INJECTION: spawn with shell
const { spawn } = require('child_process');

function unsafeSpawn(command) {
    spawn(command, { shell: true });
}

// SAFE: Using textContent
function safeTextContent(element, content) {
    element.textContent = content;
}

// SAFE: Using createElement
function safeCreateElement(tagName, text) {
    const el = document.createElement(tagName);
    el.textContent = text;
    return el;
}

// SAFE: Using DOMPurify
function safeDOMPurify(html) {
    return DOMPurify.sanitize(html);
}

module.exports = {
    unsafeDocumentWrite,
    unsafeInnerHTML,
    unsafeOuterHTML,
    unsafeEval,
    unsafeFunctionConstructor,
    unsafeSetTimeout,
    unsafeSetInterval,
    unsafeExec,
    unsafeSpawn,
    safeTextContent,
    safeCreateElement,
    safeDOMPurify,
};
