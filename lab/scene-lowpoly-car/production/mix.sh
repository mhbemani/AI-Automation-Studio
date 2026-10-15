#!/bin/bash
# mix.sh — work/voice_all.wav (placed by build.py) + FFmpeg-synthesised ambience -> out/audio_mix.wav, out/audio_voices_only.wav
# 48 kHz mono 24-bit, length = timeline totalFrames exactly, two-pass loudnorm to -14 LUFS / -1.5 dBTP target.
set -euo pipefail
cd "$(dirname "$0")"
FF=/opt/homebrew/bin/ffmpeg
PY=.venv/bin/python
mkdir -p out
# timeline numbers: total samples at 48 kHz, ambience event times (s); frame f starts at (f-1)/24
read -r N D SWELL ENG < <($PY -c "import json;t=json.load(open('timeline.json'));c=t['motionCues'];n=t['meta']['totalFrames']
print(n*2000, n/24, (c['car_arrive_start']-1)/24, (c['drive_start']-1)/24)")
ENGD=$($PY -c "print($D-$ENG)")
SWELL_MS=$($PY -c "print(round($SWELL*1000))"); ENG_MS=$($PY -c "print(round($ENG*1000))")

# premix: city noise (whole video), car-arrival swell (4 s from car_arrive_start, peaks at car_stopped), engine hum (interior);
# the ambience bus is ducked under the voices (sidechaincompress ratio 3.5), voices pass untouched.
$FF -v error -y -i work/voice_all.wav -filter_complex "
[0:a]aresample=48000,asplit=2[v][vsc];
anoisesrc=d=$D:c=brown:r=48000:a=0.5:seed=1,highpass=f=60,lowpass=f=900,volume=-30dB[city];
anoisesrc=d=4:c=pink:r=48000:a=0.5:seed=2,bandpass=f=400:width_type=o:w=2,afade=t=in:d=3:curve=qsin,afade=t=out:st=3:d=1,volume=-21dB,adelay=$SWELL_MS:all=1[swell];
aevalsrc='(0.5*sin(2*PI*55*t)+0.25*sin(2*PI*110*t+0.4*sin(2*PI*0.7*t))+0.12*sin(2*PI*165*t)+0.06*sin(2*PI*220*t))*(1+0.08*sin(2*PI*0.9*t))':s=48000:d=$ENGD,lowpass=f=240,afade=t=in:d=1.5,volume=-33dB,adelay=$ENG_MS:all=1[eng];
[city][swell][eng]amix=inputs=3:normalize=0:duration=first[amb];
[amb][vsc]sidechaincompress=threshold=0.02:ratio=3.5:attack=15:release=350[duck];
[v][duck]amix=inputs=2:normalize=0:duration=first,apad=whole_len=$N,atrim=end_sample=$N[mix]" \
  -map "[mix]" -c:a pcm_f32le work/premix.wav
$FF -v error -y -i work/voice_all.wav -af "aresample=48000,apad=whole_len=$N,atrim=end_sample=$N" -c:a pcm_f32le work/prevoices.wav

# loudness: speech peaks sit ~13 dB over its loudness, so plain linear loudnorm cannot reach -14 under -1.5 dBTP.
# Stage 0 gains to about -12 LUFS and limits sample peaks at -3.1 dBFS (alimiter, 5 ms lookahead); then two-pass loudnorm
# (pass 1 measures, pass 2 applies in linear mode, i.e. a small clean turn-down).
measure() { $FF -hide_banner -nostats -i "$1" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p'; }
norm() { # in out
  local g args
  g=$(measure "$1" | $PY -c "import json,sys;print(round(-12-float(json.load(sys.stdin)['input_i']),2))")
  $FF -v error -y -i "$1" -af "volume=${g}dB,alimiter=limit=0.7:attack=5:release=60:level=false" -c:a pcm_f32le work/limited.wav
  args=$(measure work/limited.wav | $PY -c "import json,sys;m=json.load(sys.stdin);print(f\"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}\")")
  $FF -hide_banner -nostats -y -i work/limited.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:$args:linear=true:print_format=summary,aresample=48000,apad=whole_len=$N,atrim=end_sample=$N" \
    -ar 48000 -c:a pcm_s24le "$2" 2>&1 | grep -E "Normalization Type" | sed "s|^|$2: stage-0 gain ${g} dB, |"
}
norm work/premix.wav out/audio_mix.wav
norm work/prevoices.wav out/audio_voices_only.wav

# verify: integrated loudness and true peak
for f in out/audio_mix.wav out/audio_voices_only.wav; do
  echo "$f: $($FF -hide_banner -nostats -i $f -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | tr -s ' ' | tr '\n' ' ')"
done | tee work/loudness.txt
