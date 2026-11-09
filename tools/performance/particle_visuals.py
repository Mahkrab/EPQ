"""Compare matched particle images and encode labelled four-way motion evidence.

Requires the existing ffmpeg executable. Videos use recorded 30 Hz observations;
their cadence is not an interactive viewer FPS measurement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

MODES = ("indexed", "low", "impostor", "adaptive")


def decode(path: Path) -> bytes:
    """Decode exact RGBA bytes with a bounded, local codec process."""
    return subprocess.run(["ffmpeg","-v","error","-i",str(path),"-f","rawvideo",
                           "-pix_fmt","rgba","-threads","1","pipe:1"],
                          capture_output=True,check=True,timeout=30).stdout


def compare(before: bytes, after: bytes) -> dict:
    if len(before) != len(after) or not before or len(before)%4:
        raise ValueError("matched images require equal non-empty RGBA dimensions")
    background = bytes((16,24,32))
    changed = active = squared = maximum = 0
    for offset in range(0,len(before),4):
        a,b=before[offset:offset+3],after[offset:offset+3]
        active += a!=background or b!=background
        changed += a!=b
        for x,y in zip(a,b):
            delta=abs(x-y);squared+=delta*delta;maximum=max(maximum,delta)
    pixels=len(before)//4
    mse=squared/(3*pixels)
    return dict(changed_pixels=changed,pixels=pixels,changed_percent=100*changed/pixels,
                active_union_pixels=active,changed_active_percent=100*changed/max(1,active),
                rgb_rmse=math.sqrt(mse),active_rgb_rmse=math.sqrt(squared/(3*max(1,active))),
                max_channel_delta=maximum,psnr_db=10*math.log10(255*255/mse) if mse else None)


def gallery(output: Path, comparisons: list[dict]) -> None:
    """A local slider keeps matched stills and their measured errors together."""
    data=json.dumps(comparisons).replace("<","\\u003c")
    page='''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Maelstrom particle rendering comparison</title>
<style>body{margin:24px auto;max-width:1280px;background:#101820;color:#eef;font:16px system-ui}select,input{margin:8px} .stage{position:relative;aspect-ratio:16/9}.stage img{position:absolute;width:100%;height:100%;object-fit:contain}video{width:100%}p{line-height:1.5}</style>
<h1>Matched particle rendering</h1>
<p>Identical accepted particles and camera in each comparison. Move the divider: candidate on the left, indexed spheres on the right. The videos sample all completed 240 Hz simulation work at 30 observations/s; they are not viewer FPS measurements.</p>
<label>Particles <select id="count"><option>8000</option><option>32000</option><option selected>110592</option></select></label>
<label>Accepted step <select id="step"><option>0</option><option selected>240</option><option>720</option><option>1200</option></select></label>
<label>Camera <select id="view"><option value="0">scene / motion</option><option value="1">orbit</option><option value="2" selected>close view</option></select></label>
<label>Candidate <select id="mode"><option value="impostor">analytic sphere impostor</option><option value="low">96-triangle sphere</option><option value="adaptive">adaptive mesh LOD</option></select></label>
<p id="stats"></p><input id="divider" type="range" min="0" max="100" value="50" aria-label="Comparison divider">
<div class="stage"><img id="control" alt="Indexed reference"><img id="candidate" alt="Selected candidate"></div>
<h2>Motion: indexed and low above; impostor and adaptive below</h2>
<video id="motion" controls loop muted preload="metadata"></video>
<script>const data=__DATA__;const controls=['count','step','view','mode'].map(x=>document.getElementById(x));
const [count,step,view,mode]=controls,divider=document.getElementById('divider'),candidate=document.getElementById('candidate');let lastCount='';
function update(){const prefix=`stills/${count.value}-${step.value}-${view.value}-`;document.getElementById('control').src=prefix+'indexed.png';candidate.src=prefix+mode.value+'.png';const r=data.find(r=>r.count==count.value&&r.step==step.value&&r.view==view.value&&r.renderer==mode.value);document.getElementById('stats').textContent=r?`${r.changed_percent.toFixed(2)}% of image pixels changed; foreground RGB RMSE ${r.active_rgb_rmse.toFixed(2)}/255; maximum channel change ${r.max_channel_delta}/255. Changes include silhouettes and occlusion at their edges.`:'';if(lastCount!==count.value){document.getElementById('motion').src=count.value+'-comparison.mp4';lastCount=count.value;}}
divider.oninput=()=>candidate.style.clipPath=`inset(0 ${100-divider.value}% 0 0)`;controls.forEach(c=>c.onchange=update);divider.oninput();update();</script></html>'''
    (output/"index.html").write_text(page.replace("__DATA__",data),encoding="utf-8")


def build(source: Path, output: Path) -> None:
    if shutil.which("ffmpeg") is None:
        raise ValueError("ffmpeg is required to decode images and encode visual evidence")
    records=json.loads((source/"images.json").read_text(encoding="utf-8"))
    source=source.resolve()
    groups={}
    for record in records:
        if (record["count"] not in (8000,32000,110592) or type(record["step"]) is not int
                or not 0<=record["step"]<=1200 or record["view"] not in (0,1,2)
                or record["renderer"] not in MODES):
            raise ValueError("visual manifest contains an unsupported observation")
        path=(source/record["file"]).resolve()
        if not path.is_relative_to(source) or not path.is_file():
            raise ValueError("visual manifest contains an unavailable or external image")
        key=(record["count"],record["step"],record["view"])
        groups.setdefault(key,{})[record["renderer"]]=record
    if any(set(group)!=set(MODES) or len({x["state_sha256"] for x in group.values()})!=1 for group in groups.values()):
        raise ValueError("representations do not share exactly the same accepted states")
    output.mkdir(parents=True,exist_ok=False)
    (output/"stills").mkdir()
    comparisons=[]
    for (count,step,view),group in sorted(groups.items()):
        if step not in (0,240,720,1200):
            continue
        pixels={}
        for mode,record in group.items():
            path=source/record["file"];raw=decode(path)
            if hashlib.sha256(raw).hexdigest()!=record["rgba_sha256"]:
                raise ValueError("decoded visual witness disagrees with its RGBA digest")
            pixels[mode]=raw
            shutil.copy2(path,output/"stills"/f"{count}-{step}-{view}-{mode}.png")
        for mode in MODES[1:]:
            comparisons.append(dict(count=count,step=step,view=view,renderer=mode,
                                    **compare(pixels["indexed"],pixels[mode])))
    (output/"comparison.json").write_text(json.dumps(comparisons,indent=2)+"\n",encoding="utf-8")
    for count in (8000,32000,110592):
        command=["ffmpeg","-v","warning","-n"]
        for mode in MODES:
            command.extend(["-framerate","30","-i",str(source/f"{count}-{mode}/frame-%03d.png")])
        filters=[]
        for i,label in enumerate(("Indexed: 384 triangles","Low: 96 triangles","Analytic sphere impostor","Adaptive mesh LOD")):
            filters.append(f"[{i}:v]drawtext=text='{label}':x=18:y=18:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.7[v{i}]")
        filters.extend(["[v0][v1]hstack=inputs=2[top]","[v2][v3]hstack=inputs=2[bottom]","[top][bottom]vstack=inputs=2[out]"])
        command.extend(["-filter_complex",";".join(filters),"-map","[out]","-frames:v","91",
                        "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",
                        "-threads","4","-movflags","+faststart",str(output/f"{count}-comparison.mp4")])
        subprocess.run(command,capture_output=True,check=True,timeout=180)
    shutil.copy2(source/"images.json",output/"images.json")
    gallery(output,comparisons)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path);parser.add_argument("output",type=Path)
    args=parser.parse_args()
    try:
        build(args.source,args.output)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        parser.exit(1,f"particle visual evidence: {error}\n")


if __name__=="__main__":
    main()
