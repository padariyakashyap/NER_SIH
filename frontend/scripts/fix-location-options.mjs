import fs from 'node:fs';
for (const file of ['/home/ubuntu/ner-logiai/client/src/pages/Dashboard.tsx','/home/ubuntu/ner-logiai/client/src/pages/RouteAnalysis.tsx']) {
  let text = fs.readFileSync(file, 'utf8');
  text = text.replace('key={loc}>{loc}</option>', 'key={loc.name}>{loc.name}</option>');
  text = text.replace('key={item}>{item}</option>', 'key={item.name}>{item.name}</option>');
  fs.writeFileSync(file, text);
}
