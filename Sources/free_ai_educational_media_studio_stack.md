# Free / Near-$0 AI Educational Media Studio Stack

## Goal

Build the first version of the AI-assisted educational media studio with essentially **no additional subscriptions beyond the existing $20/month Claude Pro plan**.

The core idea is:

> **Claude = intelligence/creative reasoning**  
> **n8n = orchestration/automation**  
> **Local/open-source tools = production infrastructure**  
> **You = creative director and final quality gate**

Do not optimize for maximum automation immediately. Optimize for **high-quality, repeatable production at near-zero marginal cost**.

---

# 1. n8n vs Claude

They should be treated as complementary, not competing.

| Component | Main role |
|---|---|
| Claude Pro | Ideas, research, scripts, storyboards, critique, creative reasoning |
| n8n | Automation, orchestration, scheduling, APIs, file movement, state |
| PostgreSQL | Content database and production state |
| Remotion | Programmatic animation/video |
| FFmpeg | Video/audio processing and final assembly |
| Blender | Optional advanced 3D animation |
| Pexels | Free stock images/video |
| Local TTS | Optional free voice generation |
| Canva Free | Optional thumbnail/design assistance |
| Kdenlive | Optional manual editing |
| YouTube | Primary publishing platform |
| Instagram | Secondary distribution |

---

# 2. Recommended $0-extra stack

| Stage/component | Recommended tool | Extra cost | Verdict |
|---|---|---:|---|
| Brain | Claude Pro | Already paid | ⭐⭐⭐⭐⭐ |
| Automation | n8n self-hosted | $0 | ⭐⭐⭐⭐⭐ |
| Database | PostgreSQL | $0 | ⭐⭐⭐⭐⭐ |
| Storage | Local disk initially | $0 | ⭐⭐⭐⭐⭐ |
| Programmatic video | Remotion | $0 for the relevant small-team/individual use case | ⭐⭐⭐⭐⭐ |
| Video processing | FFmpeg | $0 | ⭐⭐⭐⭐⭐ |
| 3D | Blender | $0 | ⭐⭐⭐⭐ |
| Stock media | Pexels API | $0 | ⭐⭐⭐⭐ |
| TTS | Local TTS such as Kokoro/Piper variants | $0 | ⭐⭐⭐⭐ |
| Thumbnails | Canva Free / own system | $0 | ⭐⭐⭐⭐ |
| Manual editor | Kdenlive | $0 | ⭐⭐⭐⭐ |
| Distribution | YouTube / Instagram | $0 to publish | ⭐⭐⭐⭐⭐ |

The exact licensing and usage terms should be rechecked before commercial deployment, especially for individual model/voice licenses.

---

# 3. Important Claude Pro limitation

A **Claude Pro subscription does not include unlimited Anthropic API usage**.

Claude Pro and the Anthropic API/Console are separate products.

Therefore, do **not** design the first version around:

```text
n8n
 ↓
Claude API
 ↓
Claude API
 ↓
Claude API
 ↓
Claude API
```

That would introduce another usage bill.

Instead, initially use:

```text
                 YOU
                  ↓
             Claude Pro
        (Claude / Cowork / Claude Code)
                  ↓
          creative decisions
                  ↓
                 n8n
                  ↓
        free/local automation
```

Claude can produce the intellectual/creative output, while deterministic production tasks are handled locally.

---

# 4. Run n8n locally

Use Docker for the infrastructure.

Initial architecture:

```text
Docker
 ├── n8n
 └── PostgreSQL
```

Use n8n for:

- scheduling
- moving files
- triggering scripts
- tracking production status
- calling free APIs
- collecting analytics
- preparing publishing metadata
- orchestrating deterministic steps

Do not use an LLM for tasks that can be handled by ordinary code.

---

# 5. PostgreSQL

Use a local PostgreSQL database to store the content pipeline.

Suggested entities:

```text
ideas
scripts
storyboards
assets
videos
publishing
analytics
```

For every video, keep enough information to reproduce the process.

Example:

```text
idea
topic
format
hook
script
storyboard
asset paths
render status
video path
thumbnail path
YouTube URL
Instagram status
views
CTR
retention
subscribers gained
result/score
```

This eventually gives the system memory.

---

# 6. Video creation: prioritize controllable animation

Do **not** make AI video generation the center of the MVP.

Use:

- Remotion
- FFmpeg
- SVG
- typography
- diagrams
- simple motion graphics
- screenshots
- screen recordings
- stock footage

For technical education, this can actually look better and more intentional than a sequence of unrelated AI-generated video clips.

Example:

```text
Browser
   ↓
HTTP request
   ↓
API
   ↓
Database
   ↓
Response
```

Animate the request moving through the system.

This is ideal for Remotion.

---

# 7. Remotion

Remotion should be a major part of the MVP.

Use it for:

- architecture diagrams
- data flow
- UI-like animations
- graphs
- timelines
- typography
- scene transitions
- explanatory animations

A useful direction is to make the animation data-driven.

Example concept:

```json
{
  "scene": "database_query",
  "duration": 4,
  "elements": [
    "user",
    "api",
    "database",
    "query",
    "response"
  ]
}
```

Then the renderer turns that scene description into a video scene.

This turns video creation into a reusable **content engine**.

---

# 8. FFmpeg

Use FFmpeg for deterministic video/audio operations:

- concatenate clips
- trim media
- normalize/convert audio
- add audio tracks
- convert formats
- extract frames
- create final deliverables

Example:

```text
Remotion
   ↓
rendered video
   ↓
FFmpeg
   ↓
final.mp4
```

No AI API is required for these operations.

---

# 9. Blender

Use Blender only when the subject actually benefits from 3D.

Good use cases:

- CPU architecture
- computer components
- network packets
- server rooms
- 3D system visualizations
- physical simulations
- complex conceptual scenes

Do not make Blender the center of the workflow.

For ordinary technical diagrams and motion graphics, Remotion will generally be faster to iterate.

---

# 10. Stock visuals

Use Pexels when real-world imagery or footage is useful.

Example:

```text
How the Internet Works

Pexels:
 ├── server room
 ├── fiber optic
 ├── city
 └── smartphone
```

Combine stock footage with your own diagrams and animations.

This is more controllable and usually more coherent than relying entirely on generated video.

---

# 11. Voice / TTS

For the free MVP, experiment with local TTS.

Possible directions:

- Kokoro-based local TTS
- Piper-based TTS variants
- other open local speech models

Pipeline:

```text
script.txt
    ↓
local TTS model
    ↓
voice.wav
```

No API bill.

However, verify the **specific model/voice license** before commercial use.

For the earliest videos, recording your own voice is also a very strong option because it costs nothing and gives the channel a human identity.

---

# 12. Thumbnails

Do not pay for a dedicated thumbnail service initially.

Use:

- Canva Free
- your own design system
- programmatically generated thumbnails

Example:

```text
WHY
DOES
REDIS
FEEL SO FAST?

       [simple visual]
```

The goal is a recognizable thumbnail language rather than a different random AI image every time.

---

# 13. Manual editor

You may not need one at all if the pipeline becomes:

```text
Remotion
   ↓
MP4
   ↓
FFmpeg
   ↓
final.mp4
```

For occasional manual cleanup, Kdenlive is a reasonable free option.

---

# 14. Publishing

YouTube should be the primary home.

Initially:

```text
n8n
 ↓
prepare everything
 ↓
YOU
 ↓
YouTube Studio
 ↓
Publish
```

Later, YouTube's Data API can automate uploads and metadata, subject to Google's current API/project requirements and restrictions.

Do the same for Instagram:

**automate preparation first; automate publishing later.**

---

# 15. What NOT to chase yet: AI video generation

Avoid making this the core workflow:

```text
prompt
 ↓
AI video
 ↓
prompt
 ↓
AI video
 ↓
prompt
 ↓
AI video
```

This is where a supposedly free project tends to acquire:

- limited credits
- quality inconsistency
- watermarks
- API costs
- slow generation
- style/character inconsistency
- lots of manual prompting

And educational technical content often does not need this much generative video.

---

# 16. Better MVP architecture

Recommended version:

```text
                    CLAUDE PRO
                       │
             ideas / research / script
                       │
                       ▼
                    n8n
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   PostgreSQL       Pexels       Local assets
        │
        └──────────────┬──────────────┘
                       ▼
                  Remotion
                       │
                       ├── SVG
                       ├── diagrams
                       ├── typography
                       ├── animations
                       └── screenshots
                       │
                       ▼
                    FFmpeg
                       │
                       ▼
                    MP4
                       │
                 ┌─────┴─────┐
                 ▼           ▼
              YouTube    Instagram
```

Optional:

```text
                         Blender
                            ↑
                  use only when needed
```

---

# 17. Separate creative AI work from deterministic work

Do not ask Claude to perform tasks that ordinary scripts can do.

### Claude

```text
What should we make?
        ↓
Why is it valuable?
        ↓
Research
        ↓
Script
        ↓
Storyboard
        ↓
Review
```

### n8n / local scripts

```text
Create directories
Save JSON
Move files
Render scenes
Generate subtitles
Convert audio
Render MP4
Create metadata files
Calculate file sizes
Archive assets
Track production status
```

This keeps the system cheaper, faster, and more reliable.

---

# 18. Recommended 3-phase budget strategy

## Phase 1 — $20/month total

Use:

- Claude Pro
- n8n self-hosted
- PostgreSQL
- Remotion
- FFmpeg
- local TTS
- Pexels
- Blender
- Canva Free
- YouTube
- Instagram

Do not buy anything else.

---

## Phase 2 — still approximately $20/month

Create around 10–20 videos first.

Measure what is actually limiting quality:

- voice
- images
- research
- animation
- rendering
- workflow speed

Then pay for **exactly one bottleneck**.

Do not subscribe to five AI services at once.

---

## Phase 3 — reinvest revenue

Once content starts producing revenue:

```text
revenue
   ↓
better voice
   ↓
better images
   ↓
AI video
   ↓
cloud rendering
   ↓
more automation
```

The business should earn the right to become expensive.

---

# 19. Recommended content-production philosophy

For educational videos, choose the visual medium based on the concept.

### Generated illustrations

Good for:

- conceptual scenes
- metaphors
- environments
- characters
- abstract ideas

### Programmatic animation

Good for:

- diagrams
- systems
- graphs
- data movement
- timelines
- technical concepts

### Screen recordings

Good for:

- software
- coding
- AI tools
- websites
- live demonstrations

### Generated video

Reserve for:

- visual metaphors
- atmospheric shots
- simulations
- selected transitions

### Typography

Good for:

- key concepts
- definitions
- equations
- conclusions
- punchlines

The best result is likely to come from **combining these**, not from generating everything with AI.

---

# 20. Human approval remains important

Recommended pipeline:

```text
AI creates
      ↓
AI checks
      ↓
YOU approve
      ↓
publish
```

Not:

```text
AI creates
↓
AI creates
↓
AI creates
↓
internet
```

Especially for the first few hundred pieces.

The human layer protects:

- factual quality
- visual consistency
- originality
- brand identity
- taste

---

# 21. The biggest recommendation

Instead of the original Stage 13 concept:

> AI image generation + AI video generation + TTS + Remotion

use:

> **Remotion + FFmpeg + stock footage + screen recordings + diagrams + typography + optional local TTS**

This is:

- free or nearly free
- highly controllable
- automation-friendly
- technically achievable
- well suited to educational content

And it may actually produce **more distinctive work**.

---

# 22. Final recommended stack

```text
YOU
│
├── Creative direction
├── Design taste
└── Final approval
│
▼
CLAUDE PRO
│
├── Idea generation
├── Research
├── Scripts
├── Storyboards
├── Criticism
└── Quality review
│
▼
n8n
│
├── Orchestration
├── Scheduling
├── File management
├── API calls
├── Workflow state
└── Analytics
│
├─────────────┬──────────────┐
▼             ▼              ▼
PostgreSQL    Pexels         Local assets
│
└─────────────┬──────────────┘
              ▼
           Remotion
              │
              ├── SVG
              ├── diagrams
              ├── typography
              └── animation
              │
              ▼
           FFmpeg
              │
              ▼
            MP4
              │
        ┌─────┴─────┐
        ▼           ▼
     YouTube    Instagram
```

## Bottom line

**Start with Claude Pro + self-hosted n8n + free/open-source production tools.**

Do not spend money on AI video generation yet.

Your first goal is not to build the ultimate autonomous content factory. It is to prove that you can repeatedly make **useful, visually distinctive educational content at very low cost**.

Once you know the content works, spend money only on the specific component that is demonstrably holding quality or throughput back.
