#!/usr/bin/env bash
# usage: assemble.sh VIDEO VOICE.wav CAPTIONS.srt OUTPREFIX [MUSIC.wav]
# -> OUTPREFIX.mp4 (1080p), OUTPREFIX_vertical.mp4 (1080x1920 center crop), OUTPREFIX.jpg (thumbnail)
# Voice normalized to -14 LUFS; music (optional) ducked under voice. Captions burned via PNG overlays
# because this Homebrew ffmpeg has no libass/freetype (no subtitles/drawtext filters). Needs python3 + Pillow.
set -euo pipefail
V=$1 A=$2 SRT=$3 OUT=$4 M=${5:-}
FONT=${FONT:-/System/Library/Fonts/Helvetica.ttc}
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT

# --- audio: normalize voice, duck music, final loudness pass ---
if [ -n "$M" ]; then
  ffmpeg -v error -y -i "$A" -i "$M" -filter_complex "
   [0:a]loudnorm=I=-14:TP=-1.5:LRA=11,asplit=2[vo][sc];
   [1:a]volume=0.25[bed];
   [bed][sc]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[duck];
   [vo][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
   -map "[a]" -ar 48000 "$T/a.wav"
else
  ffmpeg -v error -y -i "$A" -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 "$T/a.wav"
fi

# --- captions: one transparent PNG per SRT cue, sized W x H ---
caps() { python3 - "$SRT" "$FONT" "$1" "$2" "$T" <<'PY'
import sys,re
from PIL import Image,ImageDraw,ImageFont
srt,font,W,H,d=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
f=ImageFont.truetype(font,int(W*0.045))
ts=lambda s:sum(float(x)*m for x,m in zip(re.split('[:,]',s),(3600,60,1,.001)))
for i,b in enumerate(re.split(r'\n\s*\n',open(srt).read().strip())):
    l=b.splitlines(); a,z=l[1].split(' --> '); txt='\n'.join(l[2:])
    im=Image.new('RGBA',(W,H),(0,0,0,0)); dr=ImageDraw.Draw(im)
    bb=dr.multiline_textbbox((0,0),txt,font=f,align='center'); w,h=bb[2]-bb[0],bb[3]-bb[1]
    x,y=(W-w)//2,int(H*0.82)-h//2
    dr.rounded_rectangle((x-24,y-14,x+w+24,y+h+22),12,fill=(0,0,0,170))
    dr.multiline_text((x,y),txt,font=f,fill='white',align='center',stroke_width=2,stroke_fill='black')
    im.save(f'{d}/c{i}.png'); print(i,ts(a),ts(z))
PY
}

# --- render one format: $1=suffix $2=W $3=H $4=pre-filter ---
render() {
  local lines n=0 in=() chain="[0:v]$4,setsar=1[b0]"
  lines=$(caps "$2" "$3")
  while read -r i a z; do
    in+=(-i "$T/c$i.png")
    chain+=";[b$n][$((n+2)):v]overlay=enable='between(t,$a,$z)'[b$((n+1))]"; n=$((n+1))
  done <<<"$lines"
  ffmpeg -v error -y -stream_loop -1 -i "$V" -i "$T/a.wav" "${in[@]}" -filter_complex "$chain" \
    -map "[b$n]" -map 1:a -shortest -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 \
    -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT$1.mp4"
}
render ""          1920 1080 "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"
render _vertical   1080 1920 "scale=-2:1920,crop=1080:1920"
ffmpeg -v error -y -ss 4 -i "$OUT.mp4" -frames:v 1 -q:v 2 "$OUT.jpg"
