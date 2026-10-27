// Сжатая копия сборщика для вызова из Claude: skills/lidy-fb/sbor.js → sbor.min.js (без комментариев и отступов).
// Claude передаёт её в каждом вызове javascript_tool, поэтому чем короче — тем меньше нагрузка. Запуск: node tools/build.js
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..', 'skills', 'lidy-fb');
const src = fs.readFileSync(path.join(dir, 'sbor.js'), 'utf8');
const out = src.split(/\r?\n/)
  .filter((l) => !/^\s*\/\//.test(l))           // строки-комментарии (в регулярках и строках «//» не в начале строки)
  .map((l) => l.replace(/\s+\/\/ [^'"`/]*$/, '').trim()) // хвостовые комментарии без кавычек и слэшей
  .filter(Boolean).join('\n');
new Function(out); // синтаксис цел
fs.writeFileSync(path.join(dir, 'sbor.min.js'), out + '\n');
console.log(`sbor.min.js: ${out.length} символов (исходник ${src.length})`);
