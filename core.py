"""Offline spatial-carrier fringe tracking; signed cycles, with explicit ambiguity.

One full 2*pi phase cycle is one fringe, not one bright/dark transition.
The branch convention chooses a carrier in the positive-y half-plane. It is
an image-coordinate sign and must not be called thermal expansion until calibrated.
"""
from __future__ import annotations

import csv
import io
import json
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

VERSION = "1.1.0"
TWO_PI = 2 * np.pi
COLORS = ["#007f8b", "#e88727", "#6e61b6", "#cd5168", "#538742", "#9b704e", "#377ab5", "#9b548c", "#8b8b32"]


def binary(name):
    found = shutil.which(name)
    if not found:
        for p in (f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"):
            if Path(p).is_file():
                return p
        raise RuntimeError(f"找不到 {name}。请安装 FFmpeg 后再运行。")
    return found


def probe(path, timestamps=False):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ValueError("视频文件不存在，请检查路径或选择文件。")
    cmd = [binary("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_streams", "-show_format", "-of", "json", str(path)]
    p = subprocess.run(cmd, capture_output=True, check=False)
    if p.returncode:
        raise ValueError("无法读取视频：" + p.stderr.decode(errors="replace")[-500:])
    info = json.loads(p.stdout)
    streams = info.get("streams", [])
    if not streams:
        raise ValueError("文件没有视频轨道。")
    s = streams[0]
    a, b = map(float, s.get("avg_frame_rate", "0/1").split("/"))
    fps = a / b if b else 0
    if fps <= 0:
        a, b = map(float, s.get("r_frame_rate", "30/1").split("/"))
        fps = a / b if b else 30
    try:
        duration = float(s.get("duration", info.get("format", {}).get("duration", "0")))
    except (TypeError, ValueError):
        duration = 0.
    try:
        n = int(s.get("nb_frames", round(duration * fps)))
    except (TypeError, ValueError):
        n = round(duration * fps)
    result = dict(path=str(path), width=int(s["width"]), height=int(s["height"]), fps=fps,
                  duration_s=duration, declared_frames=n, timestamp_source="container frame timestamps")
    if timestamps:
        p = subprocess.run([binary("ffprobe"), "-v", "error", "-select_streams", "v:0",
                            "-show_frames", "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(path)], capture_output=True)
        frames = json.loads(p.stdout).get("frames", []) if not p.returncode else []
        pts = [float(f["best_effort_timestamp_time"]) for f in frames if "best_effort_timestamp_time" in f]
        if pts and len(pts) == len(frames) and np.all(np.diff(pts) > 0):
            result["timestamps"] = np.asarray(pts) - pts[0]
        else:
            # ffprobe may count decoded frames even when an AVI has no PTS.
            result["timestamps"] = np.arange(len(frames) or n) / fps
            result["timestamp_source"] = "nominal fps fallback; not verified acquisition timing"
        if duration <= 0 and len(result["timestamps"]):
            result["duration_s"] = float(result["timestamps"][-1] + 1/fps)
    return result


def get_frame(path, seconds, max_width=None):
    cmd = [binary("ffmpeg"), "-v", "error", "-ss", str(max(0, seconds)), "-i", str(path), "-frames:v", "1"]
    if max_width:
        cmd += ["-vf", f"scale='min({max_width},iw)':-1"]
    p = subprocess.run(cmd + ["-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    if p.returncode or not p.stdout:
        raise ValueError("该时间点没有可读视频帧，请选择更早的时间。")
    return Image.open(io.BytesIO(p.stdout)).convert("L")


def review_pair(path, frame_index, roi):
    """Decode exact frame indices; use original grayscale pixels, without phase filtering."""
    i = max(1, int(frame_index))
    x, y, w, h = (int(roi[k]) for k in ("x", "y", "w", "h"))
    vf = f"format=gray,crop={w}:{h}:{x}:{y},select=between(n\\,{i-1}\\,{i})"
    p = subprocess.run([binary("ffmpeg"), "-v", "error", "-i", str(path),
                        "-vf", vf, "-frames:v", "2", "-fps_mode", "passthrough",
                        "-f", "rawvideo", "-"], capture_output=True)
    if p.returncode or len(p.stdout) != 2*w*h:
        raise ValueError("无法读取这两帧；请检查原视频路径是否仍然存在。")
    a = np.frombuffer(p.stdout, np.uint8).reshape(2, h, w)
    size = 340
    out = Image.new("RGB", (size*2+36, size+48), "#f2f6f7")
    d = ImageDraw.Draw(out)
    for k in range(2):
        image = Image.fromarray(a[k]).resize((size, size), Image.Resampling.NEAREST)
        out.paste(image, (12+k*(size+12), 36))
        d.text((12+k*(size+12), 10), f"Frame {i-1+k}", fill="#153847", font=font(18))
    return out


class CarrierTracker:
    """Gaussian sideband extraction followed by pixelwise complex phase ratios."""
    def __init__(self, carriers, n=96, bandwidth=2.5):
        self.n = n
        self.carriers = np.asarray(carriers, float)
        self.window = np.outer(np.hanning(n), np.hanning(n))
        f = np.fft.fftfreq(n) * n
        fx, fy = f[None, :], f[:, None]
        self.filters = np.stack([np.exp(-((fx-kx)**2+(fy-ky)**2)/(2*bandwidth**2)) for kx, ky in carriers])
        # Restrict to the central part to exclude Hann attenuation / FFT edges.
        self.edge = max(8, int(n * .21))
        self.previous = None
        self.previous_amplitude = None
        self.previous_contrast = None

    def push(self, patches):
        p = np.asarray(patches, float)
        centered = p - p.mean(axis=(1, 2), keepdims=True)
        z = np.fft.ifft2(np.fft.fft2(centered * self.window) * self.filters)
        e = self.edge
        z = z[:, e:-e, e:-e]
        amplitude = np.abs(z)
        contrast = 2 * np.median(amplitude, axis=(1, 2)) / np.maximum(p.mean(axis=(1, 2)), 1)
        clipped = np.mean(p >= 254, axis=(1, 2))
        dark = p.mean(axis=(1, 2)) < 8
        if self.previous is None:
            delta, coherence, pixel_scatter = np.zeros(len(p)), np.ones(len(p)), np.zeros(len(p))
            pair_contrast = contrast.copy()
        else:
            w = np.minimum(amplitude, self.previous_amplitude)
            unit = z * np.conj(self.previous) / np.maximum(amplitude * self.previous_amplitude, 1e-12)
            value = (w * unit).sum(axis=(1, 2)) / np.maximum(w.sum(axis=(1, 2)), 1e-12)
            delta, coherence = np.angle(value) / TWO_PI, np.abs(value)
            residual = np.angle(unit * np.exp(-1j * np.angle(value))[:, None, None]) / TWO_PI
            pixel_scatter = np.sqrt((w * residual**2).sum(axis=(1, 2)) / np.maximum(w.sum(axis=(1, 2)), 1e-12))
            pair_contrast = np.minimum(contrast, self.previous_contrast)
        self.previous, self.previous_amplitude, self.previous_contrast = z, amplitude, contrast
        return delta, coherence, pair_contrast, clipped, pixel_scatter, dark


def carrier_candidates(frames, n=96, max_rois=7, selection=None):
    """Find repeated coherent spatial carriers and choose separated clear patches."""
    h, w = frames[0].shape
    bounds = selection or (0, 0, w, h)
    x0, y0, bw, bh = map(int, bounds)
    if bw < n or bh < n:
        raise ValueError("框选区域太小。请框选至少约 192 × 192 原始像素。")
    win = np.outer(np.hanning(n), np.hanning(n))
    f = np.fft.fftfreq(n) * n
    fx, fy = f[None, :], f[:, None]
    rr = fx**2 + fy**2
    half = (fy > 0) | ((fy == 0) & (fx > 0))
    allowed = half & (rr >= 5**2) & (rr <= (n * .33)**2)
    rows = []
    step = max(32, int(n * .75))
    xs = sorted(set(list(range(x0, x0 + bw-n+1, step)) + [x0+bw-n]))
    ys = sorted(set(list(range(y0, y0 + bh-n+1, step)) + [y0+bh-n]))
    for y in ys:
        for x in xs:
            arr = np.stack([a[y:y+n, x:x+n] for a in frames]).astype(float)
            if arr.shape[1:] != (n, n) or np.median(arr.mean((1, 2))) < 12:
                continue
            fft = np.fft.fft2((arr-arr.mean((1, 2), keepdims=True)) * win)
            energy = abs(fft)**2
            median = np.median(energy, axis=0)
            median[~allowed] = 0
            iy, ix = np.unravel_index(median.argmax(), median.shape)
            kx, ky = float(f[ix]), float(f[iy])
            filt = np.exp(-((fx-kx)**2+(fy-ky)**2)/(2*2.5**2))
            z = np.fft.ifft2(fft * filt)
            e = int(n * .21)
            contrast = 2 * np.median(abs(z[:, e:-e, e:-e]), (1, 2)) / np.maximum(arr.mean((1, 2)), 1)
            concentration = (energy*filt).sum((1, 2))/np.maximum(energy.sum((1, 2)), 1)
            clipping = np.mean(arr >= 254, (1, 2))
            score = float(np.percentile(contrast, 25) * np.sqrt(np.median(concentration)) * (1-np.median(clipping)))
            if score > .008:
                rows.append(dict(x=x, y=y, w=n, h=n, kx=kx, ky=ky, score=score))
    if not rows:
        raise ValueError("没有找到可分离的清晰条纹。请换预览时间或框选条纹清楚的区域。")
    # Weight the prevailing orientation instead of interpreting every speckle / ring as a carrier.
    for row in rows:
        v = np.array([row["kx"], row["ky"]]); v /= np.linalg.norm(v)
        row["orientation_support"] = sum(r["score"] for r in rows if abs(np.dot(v, np.array([r["kx"], r["ky"]]) / np.hypot(r["kx"], r["ky"]))) > .92)
    dominant = max(rows, key=lambda r: r["orientation_support"])
    v = np.array([dominant["kx"], dominant["ky"]]); norm = np.linalg.norm(v); v /= norm
    rows = [r for r in rows if np.dot(v, np.array([r["kx"], r["ky"]])/np.hypot(r["kx"], r["ky"])) > .88 and .55*norm < np.hypot(r["kx"], r["ky"]) < 1.65*norm]
    rows.sort(key=lambda r: r["score"], reverse=True)
    selected = []
    for row in rows:
        if all(np.hypot(row["x"]-r["x"], row["y"]-r["y"]) > n*.9 for r in selected):
            selected.append(row)
        if len(selected) >= max_rois:
            break
    return selected


def weighted_median(x, w):
    order = np.argsort(x)
    x, w = np.asarray(x)[order], np.asarray(w)[order]
    return float(x[min(len(x)-1, np.searchsorted(np.cumsum(w), w.sum()/2))])


def fuse_steps(delta, coherence, contrast, clipping, scatter, dark, rois, times, reference_point=None):
    """Fuse per-frame increments at one fixed image point; flag every unsafe step.

    Local fringe curvature / tilt makes different ROI endpoints legitimately differ.
    A robust local plane for the increments defines a common reference point.
    This does NOT stabilize images (which would remove real fringe movement).
    """
    total, r = delta.shape
    centers = np.array([[z["x"]+z["w"]/2, z["y"]+z["h"]/2] for z in rois], float)
    center = np.array(reference_point, float) if reference_point is not None else centers.mean(axis=0)
    xy = (centers-center)/max(1, np.ptp(centers, axis=0).max())
    design = np.column_stack([np.ones(r), xy])
    provisional = np.full(total, np.nan)
    dispersion = np.full(total, np.nan)
    votes = np.zeros(total, int)
    reason = np.zeros(total, np.uint16)
    # Bits: 1 poor signal; 2 fewer than 3 agreeing ROIs; 4 ROI disagreement;
    # 8 near temporal half-cycle ambiguity; 16 PTS gap; 32 poor phase coherence.
    typical_dt = np.median(np.diff(times)) if total > 1 else 1
    for i in range(total):
        valid = (contrast[i] >= .035) & (coherence[i] >= .9) & (clipping[i] < .10) & (~dark[i]) & (scatter[i] < .10)
        weights = np.maximum(contrast[i], .001) * coherence[i]**4 / np.maximum(scatter[i], .006)
        if not np.any(valid):
            reason[i] |= 1
            valid = (~dark[i]) & (coherence[i] > .7)
        if not np.any(valid):
            reason[i] |= 32
            continue
        seed = weighted_median(delta[i, valid], weights[valid])
        # Lift local phases close to a common branch, retaining the ambiguity flag.
        adjusted = seed + ((delta[i]-seed+.5) % 1 - .5)
        inliers = valid & (np.abs(adjusted-seed) <= .10)
        if not np.any(inliers):
            inliers = valid
        votes[i] = int(inliers.sum())
        if votes[i] < 3:
            reason[i] |= 2
        if votes[i] >= 4 and np.linalg.matrix_rank(design[inliers]) == 3:
            ww = np.sqrt(weights[inliers])
            beta = np.linalg.lstsq(design[inliers]*ww[:, None], adjusted[inliers]*ww, rcond=None)[0]
            value = float(beta[0])
            residual = adjusted[inliers]-design[inliers]@beta
        else:
            value = weighted_median(adjusted[inliers], weights[inliers])
            residual = adjusted[inliers]-value
        provisional[i] = value
        dispersion[i] = float(np.sqrt(np.average(residual**2, weights=weights[inliers])))
        if dispersion[i] > .025:
            reason[i] |= 4
        if (np.max(np.abs(delta[i, inliers])) > .40 or abs(value) > .40
                or np.any(np.abs(adjusted[inliers]-delta[i, inliers]) > .5)):
            reason[i] |= 8
        if i and times[i]-times[i-1] > typical_dt*1.8:
            reason[i] |= 16
    if total:
        provisional[0], reason[0], dispersion[0] = 0., 0, 0.
    return dict(delta=provisional, dispersion=dispersion, votes=votes, reason=reason, reference_point=center.tolist())


def groups(mask):
    mask = np.asarray(mask, bool)
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def intervals(times, reason):
    spans = []
    for a, b in groups(reason > 0):
        bits = int(np.bitwise_or.reduce(reason[a:b]))
        spans.append(dict(start_s=float(times[max(0, a-1)]), end_s=float(times[b-1]),
                          first_frame=int(a), last_frame=int(b-1), reason_bits=bits))
    return spans


def range_summary(times, delta, reason, start=0, end=None, sign=1):
    end = float(times[-1]) if end is None else end
    if sign not in (-1, 1) or not np.isfinite(start) or not np.isfinite(end):
        raise ValueError("时间需要是有限数值，符号只能取 +1 或 -1。")
    # Six-decimal export / browser inputs can differ from repeating frame times
    # by less than a microsecond. Do not drop an endpoint frame for that rounding.
    a = int(np.searchsorted(times, start-1e-6, side="left"))
    b = int(np.searchsorted(times, end+1e-6, side="right"))-1
    a, b = max(0, min(a, len(times)-1)), max(0, min(b, len(times)-1))
    if b <= a:
        raise ValueError("所选区间至少需要两个视频帧。")
    d = delta[a+1:b+1]*sign
    flags = reason[a+1:b+1]
    finite = np.isfinite(d)
    safe = finite & (flags == 0)
    conditional = float(np.sum(d[finite])) if np.any(finite) else None
    # Never bridge an invalid interval, nor silently treat its displacement as zero.
    safe_segments = []
    for i, j in groups(safe):
        steps = d[i:j]
        safe_segments.append(dict(start_s=float(times[a+i]), end_s=float(times[a+j]),
                                  net_cycles=float(steps.sum()),
                                  positive_cycles=float(steps[steps > 0].sum()),
                                  negative_cycles=float(steps[steps < 0].sum())))
    return dict(start_s=float(times[a]), end_s=float(times[b]), sign=int(sign),
                conditional_net_cycles=conditional,
                conditional_positive_cycles=float(d[finite & (d > 0)].sum()),
                conditional_negative_cycles=float(d[finite & (d < 0)].sum()),
                accepted_net_cycles=conditional if np.all(safe) else None,
                observed_safe_step_sum_cycles=float(d[safe].sum()),
                unsafe_steps=int((~safe).sum()), missing_steps=int((~finite).sum()),
                total_steps=int(len(d)), safe_fraction=float(safe.mean()),
                status="continuous_track_under_sampling_assumption" if np.all(safe) else "ambiguous_total",
                safe_segments=safe_segments,
                note="All video counts assume less than half a fringe between adjacent usable frames; temporal aliasing above that limit cannot always be detected. Conditional sums may miss integer cycles and are not certified displacement.")


def detect_drift(times, delta, reason):
    """Suggest sustained drift on a coarsened curve, never certify heating onset."""
    if len(times) < 60 or times[-1] < 15:
        return dict(candidate_start_s=None, note="录像太短，无法判断持续漂移。", windows=[])
    # Retain conditional increments for trend assessment; avoid pretending an
    # invalid-step-excluded curve is an unbiased displacement trajectory.
    cumulative = np.cumsum(np.nan_to_num(delta))
    seconds = np.arange(0, times[-1], 1.)
    values = np.array([np.median(cumulative[(times>=s)&(times<s+1)]) if np.any((times>=s)&(times<s+1)) else np.nan for s in seconds])
    candidates, windows = [], []
    for s in range(0, max(0, len(seconds)-10)):
        y = values[s:s+11]
        if not np.all(np.isfinite(y)):
            continue
        motion = np.diff(y)
        slope = float(np.polyfit(np.arange(len(y)), y, 1)[0])
        efficiency = float(abs(y[-1]-y[0])/max(np.abs(motion).sum(), 1e-9))
        same = float(np.mean(motion*np.sign(slope) > -.05))
        good = (times>=s)&(times<=s+10)
        quality = float(np.mean(reason[good] == 0))
        windows.append(dict(start_s=s, end_s=s+10, slope_cycles_s=slope,
                            direction_efficiency=efficiency, same_direction_fraction=same, safe_fraction=quality))
        if abs(slope)>.20 and efficiency>.72 and same>.75 and quality>.85:
            candidates.append(s)
    onset = None
    for s in candidates:
        if s+3 in candidates and s+6 in candidates:
            onset = float(s)
            break
    if onset is None:
        note = "未找到足够稳定且持续的单向漂移起点。请手动选段；不把条纹变清楚当作加热开始。"
    else:
        pre = [v for v in windows if v["end_s"] <= onset]
        baseline = bool(pre) and np.median([abs(v["slope_cycles_s"]) for v in pre]) < .15
        note = ("检测到持续单向漂移候选；前段存在较弱漂移基线。" if baseline else "检测到持续单向漂移候选，但没有充分静止基线。") + "这只是图像运动起点候选，不能证明加热在此时开始。"
    return dict(candidate_start_s=onset, note=note, windows=windows)


def font(size=18):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def plot_png(path, times, delta, reasons, roi_curves=None):
    im = Image.new("RGB", (1440, 780), "#f7f8fa")
    d = ImageDraw.Draw(im)
    d.text((66, 24), "Signed fringe phase - conditional trajectory", fill="#183548", font=font(28))
    curve = np.cumsum(np.nan_to_num(delta))
    top, left, width, height = 90, 85, 1280, 500
    lo, hi = float(curve.min()), float(curve.max())
    pad = max(1., (hi-lo)*.08); lo -= pad; hi += pad
    def xp(t): return left + width * t/max(times[-1], 1e-9)
    def yp(v): return top+height*(hi-v)/(hi-lo)
    for a, b in groups(reasons > 0):
        d.rectangle((xp(times[max(0,a-1)]),top,max(xp(times[b-1]),xp(times[max(0,a-1)])+1),top+height),fill="#ffdadd")
    for v in np.linspace(lo,hi,6):
        d.line((left,yp(v),left+width,yp(v)),fill="#dce2e7")
        d.text((10,yp(v)-8),f"{v:.1f}",fill="#526170",font=font(15))
    for t in np.linspace(0,times[-1],7):
        d.text((xp(t)-18,top+height+12),f"{t:.0f}",fill="#526170",font=font(16))
    if roi_curves is not None:
        for k in range(roi_curves.shape[1]):
            pts=[(xp(times[i]),yp(roi_curves[i,k])) for i in range(0,len(times),max(1,len(times)//2500))]
            if len(pts)>1:d.line(pts,fill=COLORS[k%len(COLORS)],width=1)
    pts=[(xp(times[i]),yp(curve[i])) for i in range(len(times))]
    d.line(pts,fill="#12364a",width=3)
    d.text((left+width//2-30,top+height+48),"Time (s)",fill="#526170",font=font(18))
    d.text((85,688),"Red = ambiguous steps. Colored = individual ROIs; black = fused phase at a fixed image point.",fill="#8b3b48",font=font(18))
    d.text((85,720),"A finite endpoint difference is conditional: rejected / aliased steps may contain unknown integer fringes.",fill="#526170",font=font(17))
    im.save(path)


def analyze(video, output, selection=None, max_rois=7, preview_s=30, progress=None):
    progress = progress or (lambda pct, message: None)
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    info = probe(video, timestamps=True)
    timestamps = info.pop("timestamps")
    if len(timestamps)<2:
        raise ValueError("视频没有足够帧，或无法确定帧数。")
    if max_rois not in (5, 7, 9):
        raise ValueError("校验区域数量请选择 5、7 或 9。")
    scale = min(.5, 1280/info["width"])
    sw = int(info["width"]*scale)//2*2; sh = int(info["height"]*scale)//2*2
    sx, sy = sw/info["width"], sh/info["height"]
    duration = info["duration_s"] or len(timestamps)/info["fps"]
    fractions = [.17, .30, .45, .65, .85]
    sample_times = [min(duration-.1, max(0, duration*v)) for v in fractions]
    if preview_s is not None:
        sample_times[0] = max(0, min(preview_s, duration-.1))
    progress(2, "寻找条纹清楚的区域")
    samples = [np.asarray(get_frame(video,t).resize((sw,sh),Image.Resampling.BOX)) for t in sample_times]
    bounds = None
    if selection is not None:
        if len(selection)!=4 or not np.all(np.isfinite(selection)):
            raise ValueError("搜索框必须是 x、y、宽、高四个数值。")
        x,y,w,h = selection
        x,y = max(0,int(x*sx)), max(0,int(y*sy))
        w,h = min(sw-x,int(w*sx)), min(sh-y,int(h*sy))
        bounds = (x,y,w,h)
    rois = carrier_candidates(samples, max_rois=max_rois, selection=bounds)
    ref_time = sample_times[0]
    ref = get_frame(video,ref_time).convert("RGB")
    dr = ImageDraw.Draw(ref)
    full_rois=[]
    for k,r in enumerate(rois):
        x,y,w,h = r["x"]/sx,r["y"]/sy,r["w"]/sx,r["h"]/sy
        full_rois.append(dict(x=round(x),y=round(y),w=round(w),h=round(h),carrier_x=r["kx"],carrier_y=r["ky"],score=r["score"]))
        dr.rectangle((x,y,x+w,y+h),outline=COLORS[k%len(COLORS)],width=5)
        dr.text((x+6,y+6),f"ROI {k+1}",fill=COLORS[k%len(COLORS)],font=font(28))
    ref.save(out/"selected_regions.png")
    tracker = CarrierTracker([(r["kx"],r["ky"]) for r in rois])
    x0,y0=min(r["x"] for r in rois),min(r["y"] for r in rois)
    cw=max(r["x"]+r["w"] for r in rois)-x0;ch=max(r["y"]+r["h"] for r in rois)-y0
    cmd=[binary("ffmpeg"),"-v","error","-i",str(video),"-vf",f"scale={sw}:{sh}:flags=area,format=gray,crop={cw}:{ch}:{x0}:{y0}","-fps_mode","passthrough","-f","rawvideo","-"]
    # stderr is read after stdout; FFmpeg error-only output remains very small.
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    measurements=[];frame_bytes=cw*ch
    try:
        while True:
            raw=proc.stdout.read(frame_bytes)
            if not raw:break
            if len(raw)!=frame_bytes:raise RuntimeError("视频解码得到不完整帧。")
            image=np.frombuffer(raw,np.uint8).reshape(ch,cw)
            patches=np.stack([image[r["y"]-y0:r["y"]-y0+r["h"],r["x"]-x0:r["x"]-x0+r["w"]] for r in rois])
            measurements.append(tracker.push(patches))
            if len(measurements)%200==0:
                progress(min(88,8+80*len(measurements)/max(info["declared_frames"],1)),f"已处理 {len(measurements)} 帧")
        code=proc.wait()
        error=proc.stderr.read().decode(errors="replace")
        if code:raise RuntimeError("视频解码失败："+error[-600:])
    finally:
        if proc.poll() is None:proc.kill()
        proc.stdout.close();proc.stderr.close()
    if len(measurements)<2:raise ValueError("视频没有足够帧。")
    n=len(measurements)
    if len(timestamps)!=n:
        # Do not silently discard frames or claim correct timing after mismatch.
        raise RuntimeError(f"帧时间戳数 {len(timestamps)} 与实际解码帧数 {n} 不一致，无法可靠计时。")
    delta,coherence,contrast,clipping,scatter,dark=[np.stack([m[k] for m in measurements]) for k in range(6)]
    progress(90,"校验区域一致性与疑似丢条纹区间")
    fused=fuse_steps(delta,coherence,contrast,clipping,scatter,dark,rois,timestamps)
    summary=range_summary(timestamps,fused["delta"],fused["reason"])
    onset=detect_drift(timestamps,fused["delta"],fused["reason"])
    good_segments=sorted((s for s in summary["safe_segments"] if s["end_s"]-s["start_s"]>=2),key=lambda s:s["end_s"]-s["start_s"],reverse=True)
    result=dict(version=VERSION,video=info,frames_decoded=n,
                settings=dict(selection_original_px=selection,max_rois=max_rois,preview_s=preview_s,
                              patch_px_processed=96,sideband_width_bins=2.5,processed_size_px=[sw,sh]),
                rois=full_rois,reference_frame_s=ref_time,
                reference_point_px=[fused["reference_point"][0]/sx,fused["reference_point"][1]/sy],
                sign_convention="positive-y Fourier sideband; phase advance is positive; not calibrated expansion sign",
                whole_video=summary,drift_detection=onset,
                best_continuous_segments=good_segments[:8],unsafe_intervals=intervals(timestamps,fused["reason"]),
                reason_bits={"1":"信号弱/饱和/暗区域","2":"少于三个可用区域","4":"区域相位变化不一致","8":"接近每帧半条或跨分支：整数条纹可能不明","16":"时间戳间隙","32":"相位相干性不足"},
                precision_note="Display resolution is not metrological accuracy. Synthetic tests validate the algorithm only; real thermal jitter, optical changes, sample temperature and integer-cycle ambiguity require separate validation.",
                interpretation="Net apparent optical phase motion. Not isolated aluminium expansion; no heater-motion or air-path correction.")
    (out/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    np.savez_compressed(out/"tracks.npz",time=timestamps,delta=fused["delta"],reason=fused["reason"],
                        dispersion=fused["dispersion"],votes=fused["votes"],roi_delta=delta,
                        coherence=coherence,contrast=contrast,clipping=clipping,pixel_scatter=scatter)
    curve=np.cumsum(np.nan_to_num(fused["delta"]));roi_curves=np.cumsum(delta,axis=0)
    with (out/"fringe_counts.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.writer(f)
        writer.writerow(["frame","time_s","signed_increment_cycles","conditional_cumulative_cycles","step_valid","reason_bits","agreeing_rois","spatial_residual_cycles"]+[f"roi{k+1}_conditional_cycles" for k in range(delta.shape[1])])
        for i in range(n):
            writer.writerow([i,timestamps[i],fused["delta"][i] if np.isfinite(fused["delta"][i]) else "",curve[i],int(fused["reason"][i]==0),int(fused["reason"][i]),int(fused["votes"][i]),fused["dispersion"][i],*roi_curves[i]])
    with (out/"unsafe_intervals.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=["start_s","end_s","first_frame","last_frame","reason_bits"]);writer.writeheader();writer.writerows(result["unsafe_intervals"])
    plot_png(out/"phase_over_time.png",timestamps,fused["delta"],fused["reason"],roi_curves)
    progress(100,"完成：结果、曲线及不可靠区间已保存")
    return result
