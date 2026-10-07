/* Presentation-only localization. Source labels stay Chinese; numeric data,
 * paths, input values and exported machine-readable records are never changed.
 * app.py embeds this file in both the live page and standalone HTML reports. */
(() => {
  'use strict';
  const en = {
    '干涉条纹计数 · v1.1.1': 'Fringe Counter · v1.1.1',
    '干涉条纹计数': 'Fringe Counter',
    '录制视频 · 局部相位追踪 · 正负运动累计': 'Recorded video · Local phase tracking · Signed motion',
    '本机处理 · v1.1.1': 'Local processing · v1.1.1',
    '切换到英文': 'Switch to Chinese',
    '1 · 选择视频': '1 · Select a video',
    '本机视频路径': 'Local video path',
    '粘贴 AVI / MP4 / MOV 路径': 'Paste an AVI / MP4 / MOV path',
    '读取视频': 'Load video',
    '选择文件…': 'Choose file…',
    '选择文件时，视频仅复制到本机程序目录，不上传到网络。': 'Choosing a file copies it to the local application folder. It is not uploaded to the internet.',
    '打开已分析的铝样品范例': 'Open the analyzed aluminium example',
    '2 · 选择清晰区域': '2 · Select clear regions',
    '默认自动寻找多个清晰区域。也可以在右侧画面拖动框选，程序只在框内寻找条纹。': 'Clear regions are detected automatically. You can also drag a search box on the preview to restrict fringe detection to that area.',
    '预览时刻（秒）': 'Preview time (s)',
    '预览': 'Preview',
    '全画面自动选择': 'Automatic selection across the full frame',
    '清除框选': 'Clear selection',
    '校验区域数量': 'Number of validation regions',
    '7 个（推荐）': '7 (recommended)',
    '5 个': '5',
    '9 个': '9',
    '3 · 分析与检查': '3 · Analyze and inspect',
    '开始分析': 'Start analysis',
    '选择视频后即可开始。': 'Select a video to begin.',
    '逐帧处理，不通过跳帧加速。正负是画面相位方向，可在结果中翻转；还未校准为样品上升或下降。': 'Every frame is processed. Positive and negative denote image-phase directions and can be reversed in the results; they are not calibrated to upward or downward sample motion.',
    '怎样理解精度': 'Understanding accuracy',
    '输出保留小数条纹。显示 0.01 条不等于准确到 0.01 条。清晰且连续的条纹可检验 0.1 条目标；红色区间存在信号丢失、区域不一致或整数条纹歧义，不能用增加小数位解决。': 'Fractional fringe counts are displayed. A 0.01-fringe display does not establish 0.01-fringe accuracy. Clear, continuous fringes can be used to test a 0.1-fringe target. Red intervals indicate signal loss, regional disagreement or integer-fringe ambiguity; extra decimal places cannot resolve these.',
    '画面与分析区域': 'Video frame and analysis regions',
    '读取视频，查看条纹清晰的位置': 'Load a video to find clear fringes',
    '拖动框选；分析完成后显示实际采用的区域。': 'Drag to select a search area. The regions used for analysis appear after processing.',
    '净变化量': 'Net change',
    '开始（秒）': 'Start (s)',
    '结束（秒）': 'End (s)',
    '符号方向': 'Sign convention',
    '原始方向': 'Original direction',
    '翻转正负': 'Reverse sign',
    '整段视频': 'Full video',
    '采用漂移候选起点': 'Use candidate drift onset',
    '导出所选区间': 'Export selected interval',
    '已生成所选区间 JSON。若浏览器未下载，可复制下方内容保存为 selected_interval.json。': 'The selected interval JSON is ready. If the browser did not download it, copy the text below and save it as selected_interval.json.',
    '所选区间 JSON': 'Selected interval JSON',
    '条件估计净变化': 'Conditional net estimate',
    '连续追踪净变化': 'Continuously tracked net change',
    '条': 'fringes',
    '正向累计': 'Forward total',
    '反向累计': 'Reverse total',
    '条（负值）': 'fringes (negative)',
    '通过检查的帧间步长': 'Frame steps passing checks',
    '带符号的累计条纹变化': 'Signed cumulative fringe change',
    '深色线：固定画面参考点的融合相位。彩色线：各区域的条件轨迹。浅红：待核对区间。红色区间两侧的曲线连接只表示条件展开，可能漏掉整数条纹。': 'Dark line: fused phase at a fixed image reference point. Colored lines: conditional regional tracks. Pale red: intervals to review. Connections across red intervals represent conditional unwrapping and may miss whole fringes.',
    '相邻帧核对': 'Inspect adjacent frames',
    '并排查看同一区域的原始灰度图。可以点击上方曲线定位，再用前后帧按钮检查反向运动。帧号从 0 开始。': 'Compare raw grayscale images of the same region side by side. Click the plot to select a time, then step through frames to inspect reversals. Frame numbers start at 0.',
    '右图帧号': 'Right-hand frame number',
    '查看区域': 'Region to inspect',
    '查看相邻帧': 'Step through frames',
    '−1 帧': '−1 frame',
    '+1 帧': '+1 frame',
    '读取这两帧': 'Load these two frames',
    '同一条纹区域的相邻两帧': 'Adjacent frames of the same fringe region',
    '可单独检查的连续区间': 'Continuous intervals for inspection',
    '这些区间内部通过当前检查；仍依赖相邻帧真实相位变化小于半条的采样条件。选择一行查看。': 'These intervals pass the current checks. They still assume that the true phase change between adjacent frames is less than half a fringe. Select a row to inspect it.',
    '区间（秒）': 'Interval (s)',
    '净变化（条）': 'Net change (fringes)',
    '时长': 'Duration',
    '待核对区间': 'Intervals to review',
    '标记的是计数风险，不代表此时没有加热。短促抖动如果可连续追踪，会保留并正负相加。': 'Flags indicate counting risks; they do not indicate that heating was absent. Brief jitter is retained and added with its sign when it can be tracked continuously.',
    '查看区间': 'View intervals',
    '原因': 'Reason',
    '保存结果': 'Save results',
    'CSV 中保留每帧时间、带符号增量、条件累计、可靠性标记及各区域结果。时间优先采用文件时间戳；缺失时按名义帧率估算，未验证相机实际采集时钟。条纹运动包含装置与空气光路影响，尚未分离材料自身膨胀。': 'CSV files retain frame times, signed increments, conditional totals, quality flags and regional results. File timestamps are preferred; nominal frame rate is used when unavailable. The camera acquisition clock has not been verified. Fringe motion includes apparatus and air-path effects and does not isolate material expansion.',
    'Fringe Counter 1.1.1 · 基于空间载频相位提取 · 一个完整 2π 周期计为一条': 'Fringe Counter 1.1.1 · Spatial-carrier phase extraction · One full 2π cycle is one fringe',
    '操作未完成': 'The operation could not be completed.',
    '请选择视频或填写路径。': 'Choose a video or enter its path.',
    '读取视频信息…': 'Reading video information…',
    '视频已读取。可直接分析，或框选清晰区域。': 'Video loaded. Start analysis or select a clear search area.',
    '预览时间必须在视频范围内。': 'The preview time must be within the video.',
    '无法显示预览画面。': 'The preview image could not be displayed.',
    '框选太小，请选至少约 192 × 192 像素。': 'The selection is too small. Select at least approximately 192 × 192 pixels.',
    '将视频传入本机程序…': 'Copying the video to the local application…',
    '开始分析…': 'Starting analysis…',
    '请选择至少两个视频帧的区间。': 'Select an interval containing at least two video frames.',
    '所选区间内部通过当前信号与一致性检查。小数结果仍依赖每帧真实运动小于半条的条件；这不等于已验证 0.01 条实验准确度。': 'The selected interval passes the current signal and consistency checks. Fractional results still assume true motion below half a fringe per frame; this does not establish 0.01-fringe experimental accuracy.',
    '查看': 'View',
    '离线交互报告': 'Offline interactive report',
    '逐帧计数 CSV': 'Frame counts CSV',
    '待核对区间 CSV': 'Review intervals CSV',
    '完整结果 JSON': 'Full results JSON',
    '相位曲线 PNG': 'Phase plot PNG',
    '读取原视频相邻帧…': 'Reading adjacent frames from the original video…',
    '两图使用相同亮度尺度，没有进行相位滤波。': 'Both images use the same brightness scale. No phase filtering is applied.',
    '所选区间结果已保存：selected_interval.json': 'Selected interval saved: selected_interval.json',
    '已打开范例。可以调整时间区间并导出。': 'Example opened. Adjust the time interval and export it as needed.',
    '待核对': 'Review required',
    '通过当前检查': 'Passes current checks',
    '录像太短，无法判断持续漂移。': 'The recording is too short to assess sustained drift.',
    '未找到足够稳定且持续的单向漂移起点。请手动选段；不把条纹变清楚当作加热开始。': 'No sufficiently stable, sustained one-way drift onset was found. Select an interval manually; clearer fringes do not establish heating onset.',
    '检测到持续单向漂移候选；前段存在较弱漂移基线。': 'A sustained one-way drift candidate was detected, preceded by a weaker drift baseline. ',
    '检测到持续单向漂移候选，但没有充分静止基线。': 'A sustained one-way drift candidate was detected without a sufficient stationary baseline. ',
    '这只是图像运动起点候选，不能证明加热在此时开始。': 'This is only a candidate onset of image motion; it does not establish when heating began.',
    '信号弱/饱和/暗区域': 'Weak signal / saturation / dark region',
    '少于三个可用区域': 'Fewer than three usable regions',
    '区域相位变化不一致': 'Inconsistent phase changes across regions',
    '接近每帧半条或跨分支：整数条纹可能不明': 'Near half a fringe per frame or a branch crossing: whole-fringe count may be ambiguous',
    '时间戳间隙': 'Timestamp gap',
    '相位相干性不足': 'Insufficient phase coherence',
    '请选择有效帧号和区域。': 'Select a valid frame number and region.',
    '页面不存在': 'Page not found',
    '不允许访问此文件。': 'Access to this file is not allowed.',
    '仅允许本机页面发起操作。': 'Only requests from the local application page are allowed.',
    '请刷新本机程序页面后重试。': 'Refresh the local application page and try again.',
    '请选择小于 4 GB 的视频。': 'Choose a video smaller than 4 GB.',
    '请选择视频文件。': 'Choose a video file.',
    '视频传入未完成。': 'The video transfer did not complete.',
    '请求过大。': 'The request is too large.',
    '已有视频正在分析，请等待完成。': 'A video is already being analyzed. Wait for it to finish.',
    '准备分析': 'Preparing analysis',
    '未知操作': 'Unknown operation',
    '视频文件不存在，请检查路径或选择文件。': 'The video file does not exist. Check its path or choose a file.',
    '文件没有视频轨道。': 'The file has no video track.',
    '该时间点没有可读视频帧，请选择更早的时间。': 'No readable frame is available at this time. Choose an earlier time.',
    '无法读取这两帧；请检查原视频路径是否仍然存在。': 'These frames could not be read. Check that the original video path still exists.',
    '框选区域太小。请框选至少约 192 × 192 原始像素。': 'The search area is too small. Select at least approximately 192 × 192 original pixels.',
    '没有找到可分离的清晰条纹。请换预览时间或框选条纹清楚的区域。': 'No clear, separable fringes were found. Try another preview time or select an area with clearer fringes.',
    '时间需要是有限数值，符号只能取 +1 或 -1。': 'Times must be finite numbers, and the sign must be +1 or −1.',
    '所选区间至少需要两个视频帧。': 'The selected interval must contain at least two video frames.',
    '视频没有足够帧，或无法确定帧数。': 'The video has too few frames, or its frame count cannot be determined.',
    '校验区域数量请选择 5、7 或 9。': 'Choose 5, 7 or 9 validation regions.',
    '寻找条纹清楚的区域': 'Finding regions with clear fringes',
    '搜索框必须是 x、y、宽、高四个数值。': 'The search box must contain four numbers: x, y, width and height.',
    '视频解码得到不完整帧。': 'Video decoding returned an incomplete frame.',
    '视频没有足够帧。': 'The video has too few frames.',
    '校验区域一致性与疑似丢条纹区间': 'Checking regional consistency and possible missed-fringe intervals',
    '完成：结果、曲线及不可靠区间已保存': 'Complete: results, plots and flagged intervals have been saved'
  };
  // Match whole application messages, preserving interpolated paths and numbers.
  const patterns = [
    [/^(\d+) × (\d+) · ([\d.]+) 帧\/秒 · ([\d.]+) 秒$/, (_,w,h,f,s)=>`${w} × ${h} · ${f} fps · ${s} s`],
    [/^搜索框：(.+)（原始像素）$/, (_,box)=>`Search box: ${box} (original pixels)`],
    [/^([\d.]+(?:–[\d.]+)?) 秒$/, (_,s)=>`${s} s`],
    [/^已处理 (\d+) 帧$/, (_,n)=>`Processed ${n} frames`],
    [/^共有 (\d+) 个待核对区间$/, (_,n)=>`${n} intervals to review`],
    [/^ROI 参考帧 ([\d.]+) 秒$/, (_,s)=>`ROI reference frame ${s} s`],
    [/^彩色框为实际采用的 (\d+) 个校验区域。融合参考点固定在这些区域中心。(重新框选前，请先点击“预览”。)?$/, (_,n,reselect)=>`The colored boxes show the ${n} validation regions used. The fusion reference point is fixed at their central location.${reselect?' Click “Preview” before selecting a new search area.':''}`],
    [/^结果目录：(.+) · 时间：(按名义帧率估算|使用文件时间戳)$/, (_,path,clock)=>`Results folder: ${path} · Timing: ${clock==='按名义帧率估算'?'estimated from nominal frame rate':'file timestamps'}`],
    [/^此区间有 (\d+) 个待核对步长(?:，其中 (\d+) 个缺少可读相位)?。当前数值是条件估计，可能漏计整数条纹，不能视作已确认的真实总变化量。切换到连续区间，或检查红色时间段。$/, (_,n,m)=>`This interval has ${n} steps to review${m?`, including ${m} with unreadable phase`:''}. The displayed values are conditional estimates and may miss whole fringes; they are not confirmed true totals. Select a continuous interval or inspect the red time spans.`],
    [/^([\d.]+) 秒 · 条件累计 ([+\-\d.—]+) 条 · (待核对|通过当前检查)$/, (_,s,n,quality)=>`${s} s · Conditional total ${n} fringes · ${en[quality]}`],
    [/^([\d.]+) → ([\d.]+) 秒 · 本步融合变化 ([+\-\d.—]+) 条 · 本区域 ([+\-\d.—]+) 条 · (待核对|通过当前检查)$/, (_,a,b,n,local,quality)=>`${a} → ${b} s · Fused change ${n} fringes · This region ${local} fringes · ${en[quality]}`],
    [/^找不到 (.+)。请安装 FFmpeg 后再运行。$/, (_,name)=>`${name} was not found. Install FFmpeg and try again.`],
    [/^无法读取视频：([\s\S]*)$/, (_,detail)=>`Could not read the video: ${detail}`],
    [/^视频解码失败：([\s\S]*)$/, (_,detail)=>`Video decoding failed: ${detail}`],
    [/^帧时间戳数 (\d+) 与实际解码帧数 (\d+) 不一致，无法可靠计时。$/, (_,a,b)=>`There are ${a} frame timestamps but ${b} decoded frames. Reliable timing is not possible.`],
    [/^漂移起点：未可靠确定。([\s\S]*)$/, (_,note)=>`Drift onset: not reliably determined. ${translateNote(note)}`],
    [/^持续单向漂移候选起点：约 ([\d.]+) 秒。([\s\S]*)$/, (_,s,note)=>`Candidate sustained one-way drift onset: approximately ${s} s. ${translateNote(note)}`]
  ];
  function translateNote(note) {
    if (en[note]) return en[note];
    return note.split(/(?<=。)/).map(part => en[part] || part).join('');
  }
  function english(source) {
    if (Object.hasOwn(en, source)) return en[source];
    if (source.includes('；')) {
      const parts = source.split('；');
      if (parts.every(part => Object.hasOwn(en, part))) return parts.map(part=>en[part]).join('; ');
    }
    for (const [pattern, render] of patterns) {
      const match = source.match(pattern);
      if (match) return render(...match);
    }
    return source;
  }
  const storageKey = 'fringe-counter-language';
  let language = 'zh-CN';
  try { if (localStorage.getItem(storageKey) === 'en') language = 'en'; } catch (_) { /* Private/offline storage may be unavailable. */ }
  const originalText = new WeakMap();
  const originalAttributes = new WeakMap();
  const attributes = ['placeholder', 'alt', 'aria-label', 'title'];
  function localized(value) { return language === 'en' ? english(value) : value; }
  function skip(element) { return !element || !!element.closest('script,style,textarea,code,pre,[data-no-translate]'); }
  function renderText(node) {
    if (skip(node.parentElement)) return;
    let record = originalText.get(node);
    if (!record || node.nodeValue !== record.rendered) record = {source:node.nodeValue};
    record.rendered = localized(record.source);
    originalText.set(node, record);
    if (node.nodeValue !== record.rendered) node.nodeValue = record.rendered;
  }
  function renderAttributes(element) {
    if (skip(element)) return;
    let records = originalAttributes.get(element) || {};
    for (const name of attributes) {
      if (!element.hasAttribute(name)) continue;
      const current = element.getAttribute(name);
      let record = records[name];
      if (!record || current !== record.rendered) record = {source:current};
      record.rendered = localized(record.source);
      records[name] = record;
      if (current !== record.rendered) element.setAttribute(name, record.rendered);
    }
    originalAttributes.set(element, records);
  }
  function renderTree(root) {
    if (root.nodeType === 3) { renderText(root); return; }
    if (root.nodeType !== 1) return;
    renderAttributes(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (node.nodeType === 3) renderText(node); else renderAttributes(node);
    }
  }
  function setLanguage(next) {
    language = next === 'en' ? 'en' : 'zh-CN';
    document.documentElement.lang = language;
    try { localStorage.setItem(storageKey, language); } catch (_) { /* Switching still works without persistence. */ }
    renderTree(document.documentElement);
    const button = document.getElementById('languageToggle');
    button.textContent = language === 'en' ? '中文' : 'English';
    button.setAttribute('aria-label', language === 'en' ? '切换到中文' : 'Switch to English');
    button.lang = language === 'en' ? 'zh-CN' : 'en';
  }
  document.getElementById('languageToggle').onclick = () => setLanguage(language === 'en' ? 'zh-CN' : 'en');
  // Translate newly produced progress, results and errors without rerunning the
  // analysis or rebuilding controls (which would discard selections/focus).
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'characterData') renderText(record.target);
      else if (record.type === 'attributes') renderAttributes(record.target);
      else for (const node of record.addedNodes) renderTree(node);
    }
  });
  setLanguage(language);
  observer.observe(document.documentElement, {subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:attributes});
  window.FringeI18n = Object.freeze({setLanguage, english, get language() { return language; }});
})();
