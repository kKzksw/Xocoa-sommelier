const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');

// Read Excel file with websites
const excelPath = path.join(__dirname, '../data/chocolates_database.xlsx');
console.log('📖 Reading Excel file:', excelPath);

const workbook = XLSX.readFile(excelPath);
const sheetName = workbook.SheetNames[0];
const worksheet = workbook.Sheets[sheetName];

// Convert to JSON keeping ALL fields
const chocolates = XLSX.utils.sheet_to_json(worksheet);

console.log(`✅ Loaded ${chocolates.length} chocolates`);
console.log(`📊 Fields per chocolate: ${Object.keys(chocolates[0]).length}`);

// Check for maker_website
const withWebsite = chocolates.filter(c => c.maker_website).length;
console.log(`🔗 Chocolates with maker_website: ${withWebsite}`);

// Save as chocolates_en.json (base English version)
const outputPath = path.join(__dirname, '../data/chocolates_en.json');
fs.writeFileSync(outputPath, JSON.stringify(chocolates, null, 2));
console.log(`✅ Saved to: ${outputPath}`);
console.log(`📦 File size: ${(fs.statSync(outputPath).size / 1024 / 1024).toFixed(2)} MB`);
