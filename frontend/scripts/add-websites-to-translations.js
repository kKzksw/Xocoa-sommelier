const fs = require('fs');
const path = require('path');

console.log('🔗 Adding maker_website to translated databases...');

// Load EN with websites (source)
const enPath = path.join(__dirname, '../data/chocolates_en.json');
const chocolatesEN = JSON.parse(fs.readFileSync(enPath, 'utf8'));
console.log(`✅ Loaded ${chocolatesEN.length} EN chocolates`);

// Create lookup map by ID
const websiteMap = {};
chocolatesEN.forEach(c => {
  if (c.id && c.maker_website) {
    websiteMap[c.id] = c.maker_website;
  }
});
console.log(`📍 Found ${Object.keys(websiteMap).length} websites to copy`);

// Update FR
const frPath = path.join(__dirname, '../data/chocolates_fr.json');
const chocolatesFR = JSON.parse(fs.readFileSync(frPath, 'utf8'));
let frUpdated = 0;
chocolatesFR.forEach(c => {
  if (c.id && websiteMap[c.id]) {
    c.maker_website = websiteMap[c.id];
    frUpdated++;
  }
});
fs.writeFileSync(frPath, JSON.stringify(chocolatesFR, null, 2));
console.log(`✅ FR: Added ${frUpdated} websites`);

// Update ES
const esPath = path.join(__dirname, '../data/chocolates_es.json');
const chocolatesES = JSON.parse(fs.readFileSync(esPath, 'utf8'));
let esUpdated = 0;
chocolatesES.forEach(c => {
  if (c.id && websiteMap[c.id]) {
    c.maker_website = websiteMap[c.id];
    esUpdated++;
  }
});
fs.writeFileSync(esPath, JSON.stringify(chocolatesES, null, 2));
console.log(`✅ ES: Added ${esUpdated} websites`);

console.log('🎉 Done! Websites added to all languages.');
