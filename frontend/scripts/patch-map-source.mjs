import fs from 'node:fs';
for (const file of ['/home/ubuntu/ner-logiai/client/src/pages/Dashboard.tsx','/home/ubuntu/ner-logiai/client/src/pages/RouteAnalysis.tsx']) {
  let text = fs.readFileSync(file, 'utf8');
  text = text.replace('<MapPanel routes=', '<MapPanel source={source} routes=');
  fs.writeFileSync(file, text);
}
