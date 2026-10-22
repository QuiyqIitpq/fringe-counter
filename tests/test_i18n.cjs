// DOM-only checks. Install jsdom 26 for these developer tests; no browser is launched.
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),{execFileSync}=require('node:child_process');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'..');
const python=process.env.PYTHON || (fs.existsSync(path.join(root,'.venv/bin/python3'))?path.join(root,'.venv/bin/python3'):'python3');
const fixture=JSON.parse(execFileSync(python,['-B','-c',`
import sys,json,numpy as np
sys.path[:0]=['.', 'tests']
from test_v12 import fixture
from processing import derive,default_config
m,a=fixture(600)
m['video']['path']='/tmp/中文视频.avi'
a['delta'][:]=.002;a['delta'][0]=0;a['delta'][200:220]=np.nan;a['reason'][200:220]=8
c=default_config(m);c['cleaning']=True;c['stitches']=[dict(start_s=6.5,end_s=7.5,pre_window_s=3,post_window_s=3)]
print(json.dumps(derive(m,a,c),ensure_ascii=False))
`],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024}));
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function page({offline=false,saved=null,blockedStorage=false}={}) {
  let html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  for(const file of ['i18n.js','ui.js']) html=html.replace(`<script src="/${file}"></script>`,()=>'<script>'+fs.readFileSync(path.join(root,file),'utf8')+'</script>');
  html=html.replace('<!--BOOT-->',offline?'<script>window.FIXED_REPORT='+JSON.stringify(fixture).replaceAll('<','\\u003c')+'</script>':'<script>window.TOKEN="test"</script>');
  const errors=[],requests=[];const console=new VirtualConsole();console.on('jsdomError',e=>errors.push(e));
  const dom=new JSDOM(html,{url:offline?'file:///tmp/fringe-report.html':'http://127.0.0.1:8781',runScripts:'dangerously',virtualConsole:console,beforeParse(w){
    if(blockedStorage)Object.defineProperty(w,'localStorage',{get(){throw Error('blocked');}});
    else if(saved)w.localStorage.setItem('fringe-counter-language',saved);
    w.fetch=async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>url==='/api/init'?{default_video:''}:[]};};
    w.HTMLCanvasElement.prototype.getContext=()=>new Proxy({},{get:()=>()=>{}});
    w.Image=class{constructor(){this.naturalWidth=400;this.naturalHeight=400;}set src(v){this._src=v;queueMicrotask(()=>this.onload?.());}get src(){return this._src;}};
  }});
  await flush();await flush();assert.deepEqual(errors,[]);dom.requests=requests;return dom;
}
function textNodes(w){
  const walker=w.document.createTreeWalker(w.document.body,w.NodeFilter.SHOW_TEXT),out=[];
  while(walker.nextNode()){const n=walker.currentNode;if(!n.parentElement.closest('script,style,textarea,[data-no-translate]'))out.push(n.nodeValue);}
  return out.join('\n');
}
test('all initial controls and accessibility labels switch and round-trip',async()=>{
  const dom=await page(),w=dom.window,d=w.document;
  try{
    assert.equal(d.documentElement.lang,'zh-CN');
    d.getElementById('languageToggle').click();await flush();
    assert.equal(d.documentElement.lang,'en');assert.match(d.title,/1\.2\.1/);
    assert.doesNotMatch(textNodes(w),/\p{Script=Han}/u);
    assert.equal(d.getElementById('pairImage').alt,'Adjacent original frames');
    assert.equal(d.getElementById('revisions').getAttribute('aria-label'),'Processing revision');
    d.getElementById('languageToggle').click();await flush();
    assert.match(d.getElementById('run').textContent,/复算修改/);
    assert.equal(d.getElementById('pairImage').alt,'相邻原始帧');
  }finally{w.close();}
});
test('offline results, suggestions, repair warnings and SVG descriptions translate',async()=>{
  const dom=await page({offline:true}),w=dom.window,d=w.document;
  try{
    const before=w.eval('JSON.stringify({report,config,boxes})');
    const paths=[...d.querySelectorAll('#chart path')].map(x=>x.getAttribute('d'));
    d.getElementById('languageToggle').click();await flush();
    assert.doesNotMatch(textNodes(w),/\p{Script=Han}/u);
    assert.match(d.getElementById('resultNotice').textContent,/estimated repairs/);
    assert.match(d.getElementById('changes').textContent,/does not recover missed fringes/);
    assert.equal(d.querySelector('#chart svg').getAttribute('aria-label'),'Signed cumulative fringe-change plot');
    assert.equal(w.eval('JSON.stringify({report,config,boxes})'),before);
    assert.deepEqual([...d.querySelectorAll('#chart path')].map(x=>x.getAttribute('d')),paths);
    d.getElementById('languageToggle').click();await flush();
    assert.match(d.getElementById('changes').textContent,/不是恢复丢失条数/);
    assert.equal(w.eval('JSON.stringify({report,config,boxes})'),before);
  }finally{w.close();}
});
test('language switch preserves box edits, pending stitch, undo stacks and in-progress state',async()=>{
  const dom=await page({offline:true}),w=dom.window,d=w.document;
  try{
    w.eval('dirty=true; selected=boxes[0].id; boxes[0].x=23; search=[0,0,200,200]; pending={before:clone(config),config:clone(config),result:report}; boxUndo=[clone(boxes)]; processUndo=[clone(config)]; setBusy(true); job="working"');
    d.getElementById('start').value='2.5';d.getElementById('end').value='8.5';d.getElementById('sign').value='-1';d.getElementById('path').value='/tmp/中文视频.avi';
    const state=w.eval('JSON.stringify({config,boxes,search,pending,boxUndo,processUndo,dirty,busy,selected,job})');
    const requests=dom.requests.length;d.getElementById('languageToggle').focus();w.FringeI18n.setLanguage('en');await flush();
    assert.equal(w.eval('JSON.stringify({config,boxes,search,pending,boxUndo,processUndo,dirty,busy,selected,job})'),state);
    assert.equal(d.getElementById('start').value,'2.5');assert.equal(d.getElementById('end').value,'8.5');assert.equal(d.getElementById('sign').value,'-1');
    assert.equal(d.getElementById('path').value,'/tmp/中文视频.avi');assert.equal(d.activeElement.id,'languageToggle');
    assert.equal(dom.requests.length,requests,'switching must not send recomputation requests');
    assert.equal(d.getElementById('run').disabled,true);
  }finally{w.close();}
});
test('new progress and validation errors track the selected language',async()=>{
  const dom=await page({saved:'en'}),w=dom.window,d=w.document;
  try{
    const status=d.getElementById('status');status.textContent='已解码 150/600 帧；复算 3 框，复用 2 框';await flush();
    assert.equal(status.textContent,'Decoded 150/600 frames; recalculating 3 regions, reusing 2');
    status.textContent='前后窗口不足或不稳定，不能生成拼接估计。请检查边界/窗口；不能强行拉齐。';await flush();assert.match(status.textContent,/alignment cannot be forced/);
    d.getElementById('languageToggle').click();await flush();assert.match(status.textContent,/不能强行拉齐/);
  }finally{w.close();}
});
test('saved language loads and private/offline storage failure does not block switching',async()=>{
  let dom=await page({saved:'en'});assert.equal(dom.window.document.documentElement.lang,'en');dom.window.close();
  dom=await page({blockedStorage:true});dom.window.document.getElementById('languageToggle').click();await flush();assert.equal(dom.window.document.documentElement.lang,'en');dom.window.close();
});
test('processing revisions, tooltips and previews preserve their numbers',async()=>{
  const dom=await page(),w=dom.window,t=w.FringeI18n.english;
  try{
    const samples=[
      '2026-10-07 13:00:00 · 时间区间/符号',
      '找到 5 个合格候选框（上限 7）。不足时不补入暗区。；保留已有手动框',
      '仅预览，尚未保存。5 项处理；原始条件总数 +1.000 → 估计条件总数 +2.000 条。',
      '12.345 秒 · 稳健空间融合 · 通过当前检查，准确性仍待验证',
      '90.0% · 有断点 · 含估计 · 相位失锁 / 过曝',
      '1.0000 → 1.0333 s · 原始增量 +0.020 · 当前 +0.010 条 · 原始质量/排除限制'
    ];
    for(const s of samples)assert.doesNotMatch(t(s),/\p{Script=Han}/u,s);
    assert.match(t(samples[2]),/\+1\.000 → estimated conditional total \+2\.000/);
    assert.equal(t('/tmp/中文文件.avi'),'/tmp/中文文件.avi');
  }finally{w.close();}
});
