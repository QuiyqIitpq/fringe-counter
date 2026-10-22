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
  Object.assign(en, {
    '条纹计数 1.2.1 · 可编辑多框': 'Fringe Counter 1.2.1 · Editable regions',
    '离线条纹计数': 'Offline Fringe Counter',
    '多框编辑 · 可撤销处理 · 原始数据始终保留': 'Editable regions · Undoable processing · Raw data retained',
    '选择视频或打开历史任务': 'Select a video or open a saved analysis',
    '1 · 视频与历史任务': '1 · Video and saved analyses',
    '选择文件': 'Choose file',
    '历史任务': 'Saved analyses',
    '选择历史分析…': 'Select a saved analysis…',
    '打开任务': 'Open analysis',
    '2 · 计数框': '2 · Counting regions',
    '操作模式': 'Editing mode',
    '选择 / 移动 / 缩放计数框': 'Select / move / resize regions',
    '添加计数框（可连续添加）': 'Add regions (repeat to add more)',
    '画自动搜索范围': 'Draw automatic search area',
    '自动选区上限': 'Maximum automatic regions',
    '生成候选框': 'Find candidate regions',
    '清除搜索范围': 'Clear search area',
    '撤销框编辑': 'Undo region edit',
    '搜索范围是虚线框；实线框才参与计数。选中实线框后可拖动中心，拖右下角缩放。切换预览不改变框的位置。': 'Dashed boxes define the search area; solid boxes are counting regions. Select a solid box, drag its center to move it, or drag its bottom-right corner to resize it. Changing the preview keeps region positions.',
    '宽': 'Width',
    '高': 'Height',
    '应用尺寸': 'Apply geometry',
    '删除此框': 'Delete region',
    '分析 / 复算修改的框': 'Analyze / update edited regions',
    '质量与解释': 'Quality and interpretation',
    '一个完整明暗周期为一条。正负是画面相位方向。没有质量报警不等于准确度已验证；每帧超过半条可能发生无法识别的漏计。暂不将本程序结果直接当作材料热膨胀量。': 'One full bright–dark cycle is one fringe. Signs describe image-phase directions. No quality warning does not establish accuracy: motion above half a fringe per frame can cause undetectable missed counts. These results should not be used directly as material thermal expansion.',
    '画面与实际计数框': 'Video and counting regions',
    '读取视频后添加多个计数框，或生成自动候选框。': 'Load a video, then add counting regions or find automatic candidates.',
    '逐框开关与结果': 'Region controls and results',
    '区域 / 定位': 'Region / locate',
    '参与统计': 'Include in statistics',
    '显示曲线': 'Show curve',
    '净变化*': 'Net change*',
    '正向 / 反向*': 'Forward / reverse*',
    '有效率 / 状态': 'Valid fraction / status',
    '*含断点时是条件和，不是完整总数。关闭“显示”不改变统计；关闭“参与”仍可保留曲线查看。灰色表示未参与有效融合。': '*With gaps, values are conditional sums, not complete totals. Hiding a curve does not change statistics; excluded regions can still be plotted. Gray indicates exclusion from effective fusion.',
    '区间与统计': 'Interval and statistics',
    '相位方向': 'Phase direction',
    '更新区间': 'Update interval',
    '整段': 'Full interval',
    '稳健融合 · 条件净变化': 'Robust fusion · Conditional net change',
    '算术平均 · 条件净变化': 'Arithmetic mean · Conditional net change',
    '固定参考位置': 'Fixed reference position',
    '更新参考点并重新统计': 'Update reference and recalculate',
    '参考位置固定，不随某框失效移动。参考点缺少有效区域包围时不外推；更改参考点会形成新的处理版本。': 'The reference position stays fixed when a region becomes invalid. No extrapolation is made when valid regions do not surround it. Changing the reference creates a new processing revision.',
    '原始对照': 'Raw comparison',
    '算术平均': 'Arithmetic mean',
    '条件连接线（未确认）': 'Conditional connections (unconfirmed)',
    '仅平滑显示': 'Smooth display only',
    '实线仅画连续可读段，各段从局部零点显示；红底是待核对区间，橙底/虚线是估计修复。条件连接线只帮助定位长期偏移，不代表恢复了丢失条数。点击曲线可以定位原始帧。': 'Solid lines show continuous readable segments, each starting at a local zero. Red shading marks intervals to review; orange shading / dashed lines mark estimated repairs. Conditional connections help locate long-term offsets and do not recover missed fringes. Click a curve to locate the original frame.',
    '排除建议与清洗': 'Exclusion suggestions and cleaning',
    '异常区域处理': 'Outlier-region handling',
    '关闭趋势排除': 'Trend exclusion off',
    '仅建议（默认）': 'Suggest only (default)',
    '自动应用高置信度建议': 'Auto-apply high-confidence suggestions',
    '应用高置信度建议': 'Apply high-confidence suggestions',
    '撤销处理': 'Undo processing',
    '恢复原始配置': 'Reset configuration',
    '开启保守清洗（分析完成后）': 'Enable conservative cleaning (after analysis)',
    '无法恢复的区间保留断点，不自动归零。': 'Unrecoverable intervals remain gaps; they are not automatically set to zero.',
    '处理版本': 'Processing revision',
    '恢复选中版本': 'Restore selected revision',
    '区域建议': 'Region suggestions',
    '抖动 / 失锁事件与趋势拼接': 'Jitter / lock-loss events and trend stitching',
    '事件开始': 'Event start',
    '事件结束': 'Event end',
    '前窗口（秒）': 'Window before (s)',
    '后窗口（秒）': 'Window after (s)',
    '预览此事件的拼接估计': 'Preview stitching estimate',
    '应用本次预览': 'Apply this preview',
    '取消预览': 'Cancel preview',
    '趋势拼接估计：假设扰动区间内延续邻近缓慢趋势。它可能移除真实的永久光程变化，不能称为恢复丢失条纹。每个事件必须单独预览和应用。': 'Trend stitching assumes that the neighboring slow trend continues through the disturbance. It may remove a real permanent optical-path change and cannot be described as recovering missed fringes. Preview and apply each event separately.',
    '已应用的修复 / 拼接记录': 'Applied repairs / stitching records',
    '相邻原始帧检查': 'Inspect adjacent original frames',
    '右图帧号（0 起算）': 'Right-hand frame number (from 0)',
    '区域': 'Region',
    '读取两帧': 'Load two frames',
    '相邻原始帧': 'Adjacent original frames',
    '保存与导出': 'Save and export',
    '保存当前配置和全部结果': 'Save configuration and all results',
    '每次统计都形成新版本；保留原始追踪、开关、排除与修复记录。导出的 HTML 是当前版本快照，重新统计与框编辑请在本机程序中打开历史任务。': 'Each recalculation creates a revision, retaining raw tracks, switches, exclusions and repair records. Exported HTML is a snapshot of that revision. Open the saved analysis in the local application to recalculate or edit regions.',
    'Fringe Counter 1.2.1 · 本机离线处理 · 原始视频不修改': 'Fringe Counter 1.2.1 · Local offline processing · Original videos remain unchanged',
    '操作失败': 'Operation failed',
    '计数框已修改。请复算后查看与这些框对应的结果。': 'Counting regions have changed. Recalculate to see results for these regions.',
    '预览时间超出视频范围': 'Preview time is outside the video range',
    '无法加载预览': 'Could not load the preview',
    '最多 20 个计数框': 'Up to 20 counting regions are allowed',
    '框宽高至少为 64 原始像素': 'Region width and height must be at least 64 original pixels',
    '框必须在画面内且宽高至少为64像素': 'Regions must be inside the frame and at least 64 pixels wide and high',
    '视频已读取，添加多个框或生成候选框': 'Video loaded. Add regions or generate candidates.',
    '复制视频到本机程序目录…': 'Copying the video to the local application folder…',
    '请先读取视频': 'Load a video first',
    '在多个时刻检查候选框…': 'Checking candidate regions at several times…',
    '先添加计数框或自动生成候选框': 'Add counting regions or generate candidates first',
    '开始追踪…': 'Starting tracking…',
    '待分析': 'Not analyzed',
    '需要追踪': 'Tracking required',
    '没有参与统计的区域': 'No regions included in statistics',
    '单框结果': 'Single-region result',
    '稳健融合主结果': 'Main robust-fusion result',
    '此文件是结果快照，请在本机程序打开历史任务重新统计': 'This is a result snapshot. Open the saved analysis in the local application to recalculate.',
    '计数框已修改，请先复算': 'Counting regions have changed; recalculate them first',
    '请先应用或取消拼接预览': 'Apply or cancel the stitching preview first',
    '重新统计（不解码视频）…': 'Recalculating statistics (without decoding video)…',
    '统计已更新，原始数据未改动': 'Statistics updated; raw data retained',
    '撤销排除': 'Undo exclusion',
    '应用': 'Apply',
    '预览影响': 'Preview effect',
    '定位': 'Locate',
    '选择事件': 'Select event',
    '可调整事件边界，前后窗口须稳定。': 'Adjust event boundaries as needed. The windows before and after must be stable.',
    '带符号累计条纹变化折线图': 'Signed cumulative fringe-change plot',
    '先复算已修改的框': 'Recalculate edited regions first',
    '预览趋势拼接估计…': 'Previewing the trend-stitching estimate…',
    '拼接预览：请核对假设与调整量': 'Stitching preview: check the assumptions and adjustment',
    '已保存拼接估计，可撤销。': 'Stitching estimate saved. It can be undone.',
    '预览已取消，未写入处理记录。': 'Preview canceled. No processing record was saved.',
    '已恢复预览前结果': 'Restored the results from before the preview',
    '请选择任务': 'Select a saved analysis',
    '旧版任务已打开；新指标缺失，请复算计数框': 'Legacy analysis opened. New quality metrics are missing; recalculate the regions.',
    '历史任务已恢复': 'Saved analysis restored',
    '先取消拼接预览': 'Cancel the stitching preview first',
    '已恢复历史处理配置，原始追踪未变': 'Previous processing configuration restored; raw tracks retained',
    '先复算改动的框': 'Recalculate edited regions first',
    'HTML 快照': 'HTML snapshot',
    '原始逐帧数据': 'Raw frame data',
    '原始框与质量元数据': 'Raw region and quality metadata',
    '逐帧 CSV': 'Frame-by-frame CSV',
    '全部结果': 'All results',
    '框与处理配置': 'Region and processing configuration',
    '操作记录': 'Operation log',
    '曲线 SVG': 'Plot SVG',
    '当前配置、数据和图像已保存': 'Current configuration, data and plot saved',
    '结果快照：统计已冻结。重新编辑/计算请在本机程序打开历史任务。': 'Result snapshot: statistics are fixed. Open the saved analysis in the local application to edit or recalculate.',
    '离线结果快照 · 数据与处理设置保留': 'Offline result snapshot · Data and processing settings retained',
    '请从历史任务列表选择。': 'Choose from the saved-analysis list.',
    '文件不在导出列表。': 'The file is not in the export list.',
    '导出版本无效。': 'Invalid export revision.',
    '不存在': 'Not found',
    '只允许本机页面': 'Only the local application page is allowed',
    '请刷新页面': 'Refresh the page',
    '文件需小于 4 GB': 'The file must be smaller than 4 GB',
    '不支持此视频格式': 'This video format is not supported',
    '文件传输未完成': 'File transfer did not complete',
    '请求过大': 'The request is too large',
    '已有视频正在分析。': 'A video is already being analyzed.',
    '分析完成': 'Analysis complete',
    '版本无效': 'Invalid revision',
    '导出图像包含不允许的内容。': 'The exported image contains unsupported content.',
    '未知请求': 'Unknown request',
    '请选择 1–20 个计数框。': 'Select 1–20 counting regions.',
    '计数框必须在画面内，宽高至少 64 原始像素。': 'Counting regions must be inside the frame and at least 64 original pixels wide and high.',
    '计数框长宽比超过 8，窄边不足以验证周期条纹；请扩大窄边。': 'The region aspect ratio exceeds 8. The narrow side is insufficient to verify periodic fringes; make it wider.',
    '计数框 ID 重复。': 'Duplicate counting-region IDs.',
    '搜索范围无效。': 'Invalid search area.',
    '检查实际计数框和缓存': 'Checking counting regions and cached tracks',
    '视频帧不完整。': 'An incomplete video frame was decoded.',
    '视频帧数与时间戳不一致。': 'Video frame count and timestamps do not match.',
    '原始追踪已保存，生成可撤销的统计结果': 'Raw tracks saved; generating undoable statistics',
    '区域开关包含不存在或重复的 ID。': 'Region switches contain unknown or duplicate IDs.',
    '处理设置无效。': 'Invalid processing settings.',
    '参考点无效。': 'Invalid reference point.',
    '时间范围无效。': 'Invalid time range.',
    '拼接事件过多。': 'Too many stitching events.',
    '时间区间至少包含两个视频帧。': 'The interval must contain at least two video frames.',
    '拼接区间或稳定窗口无效。': 'Invalid stitching interval or stable window.',
    '前后窗口不足或不稳定，不能生成拼接估计。请检查边界/窗口；不能强行拉齐。': 'The surrounding windows are insufficient or unstable. A stitching estimate cannot be generated. Check boundaries and windows; alignment cannot be forced.',
    '拼接区间不可重叠。': 'Stitching intervals must not overlap.',
    '过暗/调制信号不足': 'Too dark / insufficient modulation',
    '过曝': 'Overexposed',
    '周期结构不清': 'Unclear periodic structure',
    '相位失锁': 'Phase lock lost',
    '每帧半条风险': 'Half-fringe-per-frame risk',
    '条纹结构改变/重新捕获': 'Fringe structure changed / reacquired',
    '时间戳异常': 'Timestamp anomaly',
    '缺少新质量指标，旧版待复算': 'New quality metrics missing; recalculate legacy tracks',
    '超过 65% 帧过暗、过曝或周期结构不清': 'More than 65% of frames are too dark, overexposed or lack clear periodic structure',
    '此段原始相位质量未通过；恢复后需重新连接': 'Raw phase quality fails in this interval; reconnection is needed after recovery',
    '多个时间窗与主要趋势分离；需检查空间倾斜，不能仅凭变化少删除': 'Several windows depart from the main trend. Check spatial tilt; low motion alone is not a reason for exclusion',
    '局部时间窗趋势分歧': 'Trend disagreement in a local time window',
    '相位失锁/速度风险/结构变化；不等于已证实桌面抖动': 'Phase lock loss / speed risk / structure change; this does not prove table vibration',
    '无可用测量': 'No usable measurement',
    '单框结果，未经多框校验': 'Single-region result, without multi-region validation',
    '少于三个有效区域': 'Fewer than three valid regions',
    '参考位置缺少有效区域包围': 'Valid regions do not surround the reference position',
    '空间拟合残差过大': 'Spatial-fit residual is too large',
    '稳健空间融合': 'Robust spatial fusion',
    '几何不足且区域变化分歧': 'Insufficient geometry and disagreeing region changes',
    '一致增量融合（近似共同相位）': 'Consistent-increment fusion (approximately common phase)',
    '融合步长接近半条': 'Fused step approaches half a fringe',
    '起点': 'Start',
    '短失锁的冗余通道估计；采样及稳定映射假设仍适用，不视作原始观测。': 'Redundant-channel estimate for a brief lock loss. Sampling and stable-mapping assumptions still apply; this is not a raw observation.',
    '假设扰动区间内延续邻近缓慢趋势；调整量相对于原始条件和，不是恢复丢失条数。': 'Assumes continuation of the neighboring slow trend through the disturbance. Adjustment is relative to the raw conditional sum; it does not recover missed fringes.',
    '显示开关': 'Curve visibility',
    '参与统计开关': 'Region inclusion',
    '重新统计': 'Recalculate statistics',
    '单项排除建议': 'Individual exclusion suggestion',
    '撤销指定事件拼接': 'Undo selected stitching event',
    '时间区间/符号': 'Time interval / sign',
    '固定参考点更改': 'Reference-point change',
    '排除模式': 'Exclusion mode',
    '清洗开关': 'Cleaning toggle',
    '应用单个趋势拼接事件': 'Apply one trend-stitching event',
    '导出': 'Export',
    '处理': 'Processing'
  });
  const v12Patterns = [
    [/^(\d+) × (\d+) · ([\d.]+) fps · ([\d.]+) 秒$/, (_,w,h,f,s)=>`${w} × ${h} · ${f} fps · ${s} s`],
    [/^(\d+) 个实际计数框(；已限制自动搜索范围)?。(青色十字是固定融合参考位置。)?$/, (_,n,search,ref)=>`${n} counting regions${search?'; automatic search area restricted':''}.${ref?' The cyan cross marks the fixed fusion reference position.':''}`],
    [/^找到 (\d+) 个合格候选框（上限 (\d+)）。不足时不补入暗区。(；保留已有手动框)?$/, (_,n,max,keep)=>`Found ${n} suitable candidates (maximum ${max}). Dark areas are not added to fill the quota.${keep?' Existing manual regions retained.':''}`],
    [/^已解码 (\d+)\/(\d+) 帧；复算 (\d+) 框，复用 (\d+) 框$/, (_,n,total,updated,cached)=>`Decoded ${n}/${total} frames; recalculating ${updated} regions, reusing ${cached}`],
    [/^(.+)(参与统计|显示曲线)$/, (_,label,action)=>`${label}: ${en[action]}`],
    [/^([\d.]+)%( · 有断点| · 依赖采样条件)( · 含估计)?(?: · (.+))?$/, (_,rate,quality,estimated,reasons)=>`${rate}% · ${quality.includes('有断点')?'Contains gaps':'Sampling assumption applies'}${estimated?' · Includes estimates':''}${reasons?' · '+reasons.split(' / ').map(english).join(' / '):''}`],
    [/^(当前包含估计修复\/趋势拼接，不是原始测量总数。 )?(区间有 (\d+) 个未解决步长，显示数值是算法条件和，不能视为完整可靠总数。|区间通过当前检查；仍不代表准确度已验证。)( 旧版数据缺少新指标，请重新分析。)?$/, (_,estimate,body,n,legacy)=>`${estimate?'Includes estimated repairs / trend stitching; this is not a raw measured total. ':''}${n?`The interval has ${n} unresolved steps. Values are conditional algorithmic sums, not complete reliable totals.`:'The interval passes current checks; accuracy is still unverified.'}${legacy?' Legacy data lacks new metrics. Analyze it again.':''}`],
    [/^同一框集合的原始对照：净 ([+\-\d.—]+)，正向 ([+\-\d.—]+)，反向 ([+\-\d.—]+) 条。$/, (_,net,pos,neg)=>`Raw comparison for the same regions: net ${net}, forward ${pos}, reverse ${neg} fringes.`],
    [/^区域建议（(\d+) 项）$/, (_,n)=>`Region suggestions (${n})`],
    [/^(.+) · (整段|[\d.]+–[\d.]+s) · (高置信度|需核对) · (.+)$/, (_,label,range,confidence,reason)=>`${label} · ${range==='整段'?'Full interval':range} · ${confidence==='高置信度'?'High confidence':'Review required'} · ${english(reason)}`],
    [/^净变化 ([+\-\d.—]+) → ([+\-\d.—]+)（未应用）$/, (_,a,b)=>`Net change ${a} → ${b} (not applied)`],
    [/^([\d.]+–[\d.]+) s · (.+)$/, (_,range,reason)=>`${range} s · ${english(reason)}`],
    [/^已应用 (\d+) 项排除；(\d+) 项修复\/拼接；相同框集合的总条件和调整 ([+\-\d.—]+) 条。仅建议模式不会自动删除趋势异常框。$/, (_,n,m,change)=>`${n} exclusions applied; ${m} repairs / stitches; conditional-sum adjustment for the same regions: ${change} fringes. Suggest-only mode does not automatically remove trend outliers.`],
    [/^撤销 ([\d.]+–[\d.]+)s 拼接$/, (_,range)=>`Undo stitching at ${range} s`],
    [/^(.*?) · ([\d.]+–[\d.]+) s · (.+?)(?: 条件和调整 ([+\-\d.—]+) 条)?$/, (_,label,range,note,change)=>`${label} · ${range} s · ${english(note)}${change!==undefined?' Conditional-sum adjustment '+change+' fringes':''}`],
    [/^([\d.]+) 秒 · (.+) · (估计值|通过当前检查，准确性仍待验证|存在断点)$/, (_,time,reason,quality)=>`${time} s · ${english(reason)} · ${quality==='估计值'?'Estimate':quality==='存在断点'?'Contains a gap':'Passes current checks; accuracy remains unverified'}`],
    [/^仅预览，尚未保存。(\d+) 项处理；原始条件总数 ([+\-\d.—]+) → 估计条件总数 ([+\-\d.—]+) 条。$/, (_,n,a,b)=>`Preview only, not saved. ${n} processing changes; raw conditional total ${a} → estimated conditional total ${b} fringes.`],
    [/^([\d.]+) → ([\d.]+) s · 原始增量 ([+\-\d.—]+) · 当前 ([+\-\d.—]+) 条 · (当前可读|原始质量\/排除限制)$/, (_,a,b,raw,current,quality)=>`${a} → ${b} s · Raw increment ${raw} · Current ${current} fringes · ${quality==='当前可读'?'Currently readable':'Raw-quality / exclusion restriction'}`],
    [/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) · (.+)$/, (_,date,action)=>`${date} · ${english(action)}`],
    [/^恢复版本 ([\da-f_]+)$/, (_,revision)=>`Restore revision ${revision}`]
  ];
  patterns.unshift(...v12Patterns);

  Object.assign(en, {
    '条纹计数 1.3.0 · 可编辑多框':'Fringe Counter 1.3.0 · Editable regions',
    'Fringe Counter 1.3.0 · 本机离线处理 · 原始视频不修改':'Fringe Counter 1.3.0 · Local offline processing · Source videos remain unchanged',
    '稳健融合 · 完整净变化':'Robust fusion · Complete net change',
    '条件正向累计':'Conditional forward total','条件反向累计':'Conditional reverse total',
    '无法确定':'Undetermined','断点诊断与连续可读区间':'Gap diagnostics and continuously readable intervals',
    '允许参考点直接测量（多框支持不足时）':'Allow direct reference measurement when multi-region support is insufficient',
    '仅当固定参考点与一个有效计数框中心重合时使用该框观测，不外推、不补数。关闭可比较严格多框融合。':'Uses an observed region only when its center coincides with the fixed reference point. No extrapolation or gap filling. Disable to compare strict multi-region fusion.',
    '近似重复画面可能来自静止、重编码或重复采样，不能据此确定相机原始帧率。每个可读区间仍依赖有效图像之间真实变化小于半条的条件；不能把分段相加当作跨断点总数。':'Nearly repeated images can result from static scenes, re-encoding or repeated sampling; they do not establish the original camera rate. Each readable interval assumes true motion below half a fringe between useful images. Segment sums do not determine a total across gaps.',
    '最长的连续可读区间':'Longest continuously readable intervals','未解决区间与原因':'Unresolved intervals and reasons',
    '旧结果没有断点诊断，请重新分析。':'This older result has no gap diagnostics. Reanalyze the video.',
    '当前仍为旧引擎原始追踪；点击“分析 / 复算修改的框”才能使用新相位提取。':'Tracking was computed by the old engine. Reanalyze to use the new phase extraction.',
    '整段净变化尚无法确定。下方仅列可读部分及诊断条件和。':'The full net change is undetermined. Readable partial sums and diagnostic conditional sums are listed below.',
    '所选区间连续可读，仍依赖采样条件。':'The selected interval is continuously readable under the sampling assumption.',
    '参考点直接测量步长':'Direct reference measurement steps','至少一框接近半条':'At least one region near half a fringe','至少一框信号不良':'At least one region with poor signal','至少一框失锁或重捕获':'At least one region lost lock or reacquired','近似重复画面步长':'Nearly repeated image steps','旧结果未检测':'Not measured in this older result',
    '查看此区间':'Inspect this interval','查看原始帧':'Inspect source frames','诊断数据':'Diagnostics data','断点清单 CSV':'Unresolved intervals CSV','连续区间 CSV':'Continuous intervals CSV','查看连续区间':'Inspect continuous interval','参考点直接测量开关':'Direct reference measurement toggle','参考点直接测量；多框支持不足':'Direct reference observation; insufficient multi-region support'
  });
  patterns.unshift(
    [/^有效步长部分和 ([+\-\d.—]+) 条；诊断条件和 ([+\-\d.—]+) 条；条件和含 (\d+) 个未通过检查的有限数值。$/,(_,a,b,n)=>`Qualified partial sum ${a} fringes; diagnostic conditional sum ${b} fringes; includes ${n} finite increments that failed checks.`],
    [/^(参考点直接测量步长|至少一框接近半条|至少一框信号不良|至少一框失锁或重捕获|近似重复画面步长)：(.+)$/,(_,label,n)=>english(label)+': '+english(n)],
    [/^([\d.]+–[\d.]+) s · (\d+) 步 · (.+)$/,(_,range,n,tail)=>`${range} s · ${n} steps · `+(tail.endsWith(' 条')?tail.replace(' 条',' fringes'):tail.split(' / ').map(english).join(' / '))]
  );

  function english(source) {
    const trimmed = source.trim();
    if (trimmed !== source) return source.slice(0, source.indexOf(trimmed)) + english(trimmed) + source.slice(source.indexOf(trimmed) + trimmed.length);
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
