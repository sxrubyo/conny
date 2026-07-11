const fs = require('fs');
const js = fs.readFileSync('/home/ubuntu/bublee/src/interfaces/web/static/app.js', 'utf8');

// A quick and dirty script to find variable declarations and check if they are used for .addEventListener
const matches = [...js.matchAll(/(\w+)\.addEventListener/g)];
const addEventListeners = [...new Set(matches.map(m => m[1]))];

let missing = [];
for (const v of addEventListeners) {
    if (v === 'document' || v === 'window' || v === 'item' || v === 'cell' || v === 'card' || v === 'div' || v === 'btn' || v === 'newDelBtn') continue;
    // does "const v" exist?
    if (!js.includes(`const ${v} `) && !js.includes(`let ${v} `)) {
        missing.push(v);
    }
}
console.log("Missing declarations:", missing);
