// DOM tests only: no browser process, external resources or real video required.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('jsdom');
const root = path.resolve(__dirname, '..');
const template = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const localization = fs.readFileSync(path.join(root, 'i18n.js'), 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));
const fixture = () => ({
  rois: [{}, {}, {}], frames_decoded: 4,
  track: {time:[0,1,2,3], delta:[0,.1,-.2,.3], reason:[0,0,4,0], roi_curves:[[0,.1,-.1,.2],[0,.1,-.1,.2],[0,.1,-.1,.2]]},
  drift_detection:{candidate_start_s:null,note:'录像太短，无法判断持续漂移。'},
  best_continuous_segments:[{start_s:0,end_s:1,net_cycles:.1}],
  unsafe_intervals:[{start_s:1,end_s:2,reason_bits:4}],
  reason_bits:{4:'区域相位变化不一致'},
  folder:'/tmp/实验秒条/结果', video:{timestamp_source:'file'},
  reference_frame_s:1, preview_url:'selected_regions.png',
  whole_video:{note:'Sampling assumption applies.'}
});
async function page({report=null,language=null,blockedStorage=false}={}) {
  const errors=[];
  const vc = new VirtualConsole();
  vc.on('jsdomError', e=>errors.push(e));
  let html=template.replace('<script src="i18n.js"></script>',()=>'<script>'+localization+'</script>');
  html=html.replace('<!--BOOTSTRAP-->',report?'<script>window.FIXED_REPORT='+JSON.stringify(report)+'</script>':'<script>window.APP_TOKEN="test"</script>');
  const dom=new JSDOM(html, {
    url:report?'file:///tmp/report.html':'http://127.0.0.1:8769/',runScripts:'dangerously',virtualConsole:vc,
    beforeParse(w) {
      if (blockedStorage) Object.defineProperty(w,'localStorage',{get(){throw Error('Storage unavailable');}});
      else if(language) w.localStorage.setItem('fringe-counter-language',language);
      w.fetch=async()=>({ok:true,json:async()=>({default_video:'',example_available:false})});
      w.HTMLCanvasElement.prototype.getContext=()=>new Proxy({},{get:(_,key)=>key==='measureText'?()=>({width:10}):()=>{}});
      w.HTMLCanvasElement.prototype.getBoundingClientRect=()=>({width:800,height:330,left:0,top:0});
      w.Image=class {constructor(){this.naturalWidth=768;this.naturalHeight=576;}set src(value){this._src=value;queueMicrotask(()=>this.onload?.());}get src(){return this._src;}};
    }
  });
  await flush(); await flush();
  assert.deepEqual(errors,[], 'page initializes without JavaScript errors');
  return dom;
}
function visibleTexts(w) {
  const walker=w.document.createTreeWalker(w.document.body,w.NodeFilter.SHOW_TEXT);
  const texts=[];
  while(walker.nextNode()) {
    const n=walker.currentNode;
    if(!n.parentElement.closest('script,style,textarea,[data-no-translate],.hidden,#folder')) texts.push(n.nodeValue);
  }
  return texts.join('\n');
}
test('default Chinese, one-click English, attributes and Chinese round trip',async()=>{
  const dom=await page();const w=dom.window,d=w.document;
  try {
    assert.equal(d.documentElement.lang,'zh-CN');
    assert.equal(d.querySelector('h1').textContent,'干涉条纹计数');
    d.getElementById('languageToggle').click();await flush();
    assert.equal(d.documentElement.lang,'en');
    assert.equal(d.querySelector('h1').textContent,'Fringe Counter');
    assert.equal(d.title,'Fringe Counter · v1.1.1');
    assert.equal(d.getElementById('path').placeholder,'Paste an AVI / MP4 / MOV path');
    assert.equal(d.getElementById('reviewImage').alt,'Adjacent frames of the same fringe region');
    assert.doesNotMatch(visibleTexts(w),/\p{Script=Han}/u);
    assert.equal(w.localStorage.getItem('fringe-counter-language'),'en');
    d.getElementById('languageToggle').click();await flush();
    assert.equal(d.querySelector('h1').textContent,'干涉条纹计数');
    assert.equal(d.getElementById('path').placeholder,'粘贴 AVI / MP4 / MOV 路径');
  } finally {w.close();}
});
test('saved choice loads, and switching still works when storage is blocked',async()=>{
  const saved=await page({language:'en'});
  assert.equal(saved.window.document.querySelector('h1').textContent,'Fringe Counter');saved.window.close();
  const blocked=await page({blockedStorage:true});
  blocked.window.document.getElementById('languageToggle').click();await flush();
  assert.equal(blocked.window.document.documentElement.lang,'en');blocked.window.close();
});
test('progress and errors arriving after switching use the current language',async()=>{
  const dom=await page({language:'en'}),w=dom.window,d=w.document;
  try {
    const s=d.getElementById('status');
    s.textContent='已处理 123 帧';await flush();assert.equal(s.textContent,'Processed 123 frames');
    s.textContent='视频文件不存在，请检查路径或选择文件。';await flush();
    assert.match(s.textContent,/video file does not exist/);
    s.firstChild.nodeValue='已处理 456 帧';await flush();assert.equal(s.textContent,'Processed 456 frames');
    d.getElementById('languageToggle').click();await flush();assert.equal(s.textContent,'已处理 456 帧');
  } finally {w.close();}
});
test('offline report switches results and preserves selected range, sign and values',async()=>{
  const data=fixture(),before=JSON.stringify(data),dom=await page({report:data}),w=dom.window,d=w.document;
  try {
    const start=d.getElementById('start'),end=d.getElementById('end'),sign=d.getElementById('sign');
    start.value='1';end.value='3';sign.value='-1';sign.dispatchEvent(new w.Event('change'));
    d.getElementById('reviewFrame').value='2';
    d.getElementById('exportText').value='{"path":"/tmp/实验秒条"}';
    const values=['net','positive','negative','quality'].map(id=>d.getElementById(id).textContent);
    const raw=JSON.stringify(w.FIXED_REPORT);
    d.getElementById('languageToggle').click();await flush();
    assert.equal(start.value,'1');assert.equal(end.value,'3');assert.equal(sign.value,'-1');
    assert.equal(d.getElementById('reviewFrame').value,'2');
    assert.deepEqual(['net','positive','negative','quality'].map(id=>d.getElementById(id).textContent),values);
    assert.match(d.getElementById('warning').textContent,/conditional estimates/);
    assert.equal(d.getElementById('folder').textContent,'Results folder: /tmp/实验秒条/结果 · Timing: file timestamps');
    assert.doesNotMatch(visibleTexts(w),/\p{Script=Han}/u);
    assert.equal(d.getElementById('exportText').value,'{"path":"/tmp/实验秒条"}');
    assert.equal(JSON.stringify(w.FIXED_REPORT),raw);assert.equal(JSON.stringify(data),before);
    d.getElementById('languageToggle').click();await flush();
    assert.match(d.getElementById('warning').textContent,/条件估计/);
    assert.deepEqual(['net','positive','negative','quality'].map(id=>d.getElementById(id).textContent),values);
  } finally {w.close();}
});
test('switching does not clear an in-progress job, input, search box or focus',async()=>{
  const dom=await page(),w=dom.window,d=w.document;
  try {
    d.getElementById('path').value='/tmp/实验秒条.avi';
    w.eval('selection=[10,20,300,400]; jobId="running-job"; setBusy(true)');
    d.getElementById('roiInfo').textContent='搜索框：10, 20, 300, 400（原始像素）';
    d.getElementById('languageToggle').focus();
    w.FringeI18n.setLanguage('en');await flush();
    assert.equal(d.getElementById('path').value,'/tmp/实验秒条.avi');
    assert.equal(w.eval('jobId'),'running-job');
    assert.equal(w.eval('JSON.stringify(selection)'),'[10,20,300,400]');
    assert.equal(d.getElementById('run').disabled,true);
    assert.equal(d.activeElement.id,'languageToggle');
    assert.match(d.getElementById('roiInfo').textContent,/Search box: 10, 20, 300, 400/);
  } finally {w.close();}
});
test('dynamic drift, warnings, timing and technical errors keep numbers and paths',async()=>{
  const dom=await page(),w=dom.window,t=w.FringeI18n.english;
  try {
    const examples=[
      '1920 × 1080 · 29.97 帧/秒 · 12.50 秒',
      '此区间有 7 个待核对步长，其中 2 个缺少可读相位。当前数值是条件估计，可能漏计整数条纹，不能视作已确认的真实总变化量。切换到连续区间，或检查红色时间段。',
      '持续单向漂移候选起点：约 12.3 秒。检测到持续单向漂移候选，但没有充分静止基线。这只是图像运动起点候选，不能证明加热在此时开始。',
      '信号弱/饱和/暗区域；区域相位变化不一致',
      '1.000 → 2.000 秒 · 本步融合变化 -0.20 条 · 本区域 +0.10 条 · 待核对',
      '1.000 秒 · 条件累计 +0.10 条 · 通过当前检查',
      '帧时间戳数 10 与实际解码帧数 9 不一致，无法可靠计时。'
    ];
    for(const text of examples) assert.doesNotMatch(t(text),/\p{Script=Han}/u,text);
    assert.equal(t('无法读取视频：/tmp/实验秒条.avi'),'Could not read the video: /tmp/实验秒条.avi');
  } finally {w.close();}
});
