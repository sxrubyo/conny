const { JSDOM } = require('jsdom');
const fs = require('fs');

const html = fs.readFileSync('/home/ubuntu/bublee/src/interfaces/web/static/index.html', 'utf8');
const js = fs.readFileSync('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'utf8');

const dom = new JSDOM(html, { runScripts: "outside-only" });
const window = dom.window;
const document = window.document;
const localStorage = { getItem: () => null, setItem: () => {} };

// Mock history
window.history = { pushState: () => {} };
window.fetch = async () => {};
window.console.log = console.log;
window.console.error = console.error;

try {
    eval(js);
    console.log("SUCCESS! Script evaluated without ReferenceErrors.");
} catch (e) {
    console.log("EVAL ERROR:", e.toString());
}
