// DOMの最小テストダブルで、教材データと画面ロジックをネットワークなしで検証する。
// 実ブラウザの描画テストの代用ではない。
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const path=require('node:path');
const elements=new Map(),storage=new Map();
let selectors={},registered;
function element(key){if(!elements.has(key))elements.set(key,{innerHTML:'',textContent:'',style:{},dataset:{},value:'',classList:{toggle(){}},querySelectorAll:s=>selectors[s]||[],insertAdjacentHTML(_,s){this.innerHTML+=s},focus(){},scrollIntoView(){}});return elements.get(key)}
const document={querySelector:element,querySelectorAll:s=>selectors[s]||[],modelContext:{registerTool(t){registered=t}},createElement:()=>({click(){}})};
const context={document,location:{hash:'#home'},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},console,setTimeout:()=>{},AbortController,Blob,URL};
context.window=context;context.addEventListener=()=>{};context.scrollTo=()=>{};
vm.createContext(context);
for(const f of ['data.js','quizzes.js','app.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,f),'utf8'),context,{filename:f});
const run=s=>vm.runInContext(s,context);
assert.equal(context.COURSE.days.length,70);
assert.deepEqual(context.COURSE.days.map(d=>d.day).join(','),Array.from({length:70},(_,i)=>i+31).join(','));
assert.equal(context.COURSE.days.filter(d=>d.note).length,32);
assert.equal(context.COURSE.days.filter(d=>d.status==='[x]').length,41);
assert.equal(context.QUIZZES.length,33);
assert.equal(new Set(context.QUIZZES.map(q=>q.id)).size,33);
for(const q of context.QUIZZES){assert.ok(q.options[q.answer]);assert.ok(q.explanation.length>20)}
assert.ok(!run("markdown('<script>alert(1)</script>')").includes('<script>'));
element('#phase-filter').value='all';element('#status-filter').value='all';element('#search').value='';
run('filterCatalog()');assert.equal((element('#catalog').innerHTML.match(/class="card"/g)||[]).length,70);
element('#search').value='Checkpoint';run('filterCatalog()');assert.match(element('#catalog').innerHTML,/Checkpoint/);
element('#search').value='nonexistent-topic';run('filterCatalog()');assert.match(element('#catalog').innerHTML,/条件に一致/);
for(const q of context.QUIZZES){run(`startQuiz(QUIZZES.filter(q=>q.id===${JSON.stringify(q.id)}));answerQuestion(-1)`);assert.match(element('#feedback').innerHTML,/解説を確認/);run(`renderQuestion();answerQuestion(${q.answer})`);assert.match(element('#feedback').innerHTML,/正解です/)}
const record=JSON.parse(storage.get('llm-studio-v1'));
assert.equal(Object.keys(record.answers).length,33);assert.ok(Object.values(record.answers).every(a=>a.first===false&&a.last===true&&a.attempts===2));
run('lesson(62);showLessonTab("reflect")');element('#reflection').value='上限と使用量は別。';element('#save-note').onclick();assert.equal(JSON.parse(storage.get('llm-studio-v1')).notes[62],'上限と使用量は別。');
element('#k').value='60';element('#vector-first').value='doc_2';run('initLab("rrf")');assert.match(element('#rrf-bars').innerHTML,/0.03279/);assert.equal((element('#rrf-bars').innerHTML.match(/0.03200/g)||[]).length,2);
selectors['input:checked']=[{value:'doc_1'},{value:'doc_2'}];run('initLab("citation")');assert.match(element('#citation-result').innerHTML,/0.50/);assert.match(element('#citation-result').innerHTML,/1.00/);assert.match(element('#citation-result').innerHTML,/False/);
selectors['input:checked']=[{value:'doc_9'}];run('initLab("citation")');assert.match(element('#citation-result').innerHTML,/Context外の引用：doc_9/);
for(const [key,value] of Object.entries({n:3,c:3,t:1}))element('#'+key).value=String(value);
run('initLab("async")');assert.match(element('#async-bars').innerHTML,/3秒/);assert.match(element('#async-bars').innerHTML,/1秒/);
element('#c').value='1';run('initLab("async")');assert.equal((element('#async-bars').innerHTML.match(/3秒/g)||[]).length,2);
element('#max-turns').value='3';element('#max-tools').value='2';run('initLab("budget")');element('#plan').onclick();element('#tool').onclick();element('#tool').onclick();element('#tool').onclick();assert.match(element('#budget-result').innerHTML,/停止：Tool上限/);assert.match(element('#budget-result').innerHTML,/<strong>1<\/strong>/);assert.match(element('#budget-result').innerHTML,/<strong>2<\/strong>/);
assert.equal(registered.name,'open_learning_day');assert.throws(()=>registered.execute({day:0}));assert.equal(registered.execute({day:62}).day,62);assert.match(element('#main').innerHTML,/停止条件/);
for(const day of context.COURSE.days){const note=path.join(__dirname,'..','notes',`day-${String(day.day).padStart(3,'0')}.md`);if(fs.existsSync(note))assert.equal(day.note,fs.readFileSync(note,'utf8'))}
console.log('PASS: 70 lessons, source fidelity, 33 quiz/retry cases, persistence, filters, four labs, navigation contract.');
