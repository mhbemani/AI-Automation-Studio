# AI Educational Media Studio — Project Brief & Execution Plan

**Prepared:** 2026-10-05  
**Purpose:** Hand this document to Claude as the working brief for designing and implementing the system.

---

## 1. Vision

Build a small **AI-assisted educational media studio** that can repeatedly produce genuinely useful, visually distinctive educational videos and distribute them across social platforms.

The goal is not to create a fully autonomous "AI content farm." The goal is to create a **high-quality content production system** in which:

- **Human = creative director / final editor / taste**
- **Claude = reasoning, research, writing, planning, critique, agentic assistance**
- **n8n = automation, orchestration, integrations, scheduling, state transitions**
- **Programmatic video tools = deterministic technical animation and assembly**
- **AI generation tools = images, video clips, voice, and other assets where useful**
- **Analytics = feedback loop that improves future content**

The broader business hypothesis is:

> Can a person with design taste, technical knowledge, AI knowledge, and automation skills build a sustainable audience and eventually make money from the resulting content + services + products?

---

## 2. Core Strategic Decision: n8n and Claude Are Complementary

Do NOT treat n8n and Claude as direct competitors.

### n8n
Use n8n as the **automation backbone**:

- scheduled workflows
- webhooks
- API integrations
- database state
- moving files/assets through the pipeline
- triggering research/generation/rendering jobs
- publishing
- collecting analytics
- notifications and approval gates

### Claude
Use Claude as the **reasoning and creative layer**:

- idea generation
- topic evaluation
- research synthesis
- script writing
- story structure
- storyboard creation
- visual direction
- critique
- quality assurance
- iteration
- analyzing performance and proposing improvements
- agentic desktop/file work when useful (including Cowork / Claude Code where appropriate)

### Human
The human remains responsible for:

- choosing/defining the brand
- final creative direction
- approving content before publishing
- preserving originality and quality
- deciding what the system should optimize for

---

## 3. High-Level System

```text
                 ┌──────────────────┐
                 │  Idea Discovery  │
                 │ questions/trends │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │   Idea Scoring   │
                 │ useful? original?│
                 │ visually strong? │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Research + Facts │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Script + Story   │
                 │ + storyboard     │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Visual Planning  │
                 │ diagrams/shots   │
                 │ animation/B-roll │
                 └────────┬─────────┘
                          ↓
       ┌──────────────────┴──────────────────┐
       ↓                                     ↓
┌──────────────┐                      ┌──────────────┐
│ AI images    │                      │ AI video     │
│ illustrations│                      │ clips        │
└──────┬───────┘                      └──────┬───────┘
       └──────────────────┬──────────────────┘
                          ↓
                 ┌──────────────────┐
                 │ Voice / Captions │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Video Assembly   │
                 │ Remotion / FFmpeg│
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ HUMAN REVIEW     │
                 │      YOU         │
                 └────────┬─────────┘
                          ↓
         ┌────────────────┼─────────────────┐
         ↓                ↓                 ↓
      YouTube         Instagram           TikTok
         ↓                ↓                 ↓
                  Analytics / Feedback
                          ↓
                 back into Idea Engine
```

---

## 4. Content Strategy

Do not start by asking:

> What can AI generate?

Start by asking:

> What can I explain beautifully that people actually want to understand?

The recommended starting niche is:

# Visual explanations of software, AI, backend systems, and the internet

This niche fits the creator's likely strengths particularly well because it combines:

- technical knowledge
- visual design
- animation
- AI
- automation
- educational value

### Potential umbrella brand

**How Software Actually Works**

Possible future series:

- How Software Actually Works
- How AI Actually Works
- How the Internet Actually Works
- How Backend Systems Actually Work
- How Modern Apps Actually Work

---

## 5. Example Topics

### Software / Backend

1. What happens when you type a URL?
2. What happens when you click Login?
3. How does a database find a row?
4. Why do indexes make databases faster?
5. What actually happens inside a cache?
6. How does JWT authentication work?
7. What happens inside an HTTP request?
8. What does a load balancer do?
9. What does an API gateway do?
10. What happens when a server crashes?
11. What does Redis actually do?
12. Why do distributed systems fail?
13. How does HTTPS actually work?
14. What does Docker actually do?
15. Sessions vs JWT: what is really happening?

### AI

1. What actually happens when an LLM answers you?
2. Tokens vs words
3. Why LLMs hallucinate
4. What is RAG?
5. What is an AI agent?
6. What is MCP?
7. What is a vector database?
8. Why context windows matter
9. Why AI models sometimes appear to "forget"
10. AI agent vs automation

### Story / Thought Experiment Format

Use "What would happen if...?" as a repeatable narrative format:

- What if DNS disappeared?
- What if databases had no indexes?
- What if passwords disappeared?
- What if CPUs had no cache?
- What if HTTP did not exist?
- What if all internet clocks disagreed?

This format encourages story-driven visuals instead of listicles.

---

## 6. Content Quality Principles

The system must optimize for **usefulness + originality + visual clarity**, not output volume.

Avoid:

- generic AI narration over generic stock footage
- repetitive slideshow videos
- shallow "10 facts" content
- mass-produced videos with minimal human differentiation
- visual noise that does not teach anything
- hallucinated facts

Target:

- clear mental models
- strong visual metaphors
- accurate explanations
- elegant diagrams
- intentional pacing
- distinctive visual identity
- memorable hooks
- real educational payoff

The underlying principle:

> **AI should accelerate production, not replace editorial judgment.**

---

## 7. Visual Production Philosophy

Do NOT use AI-generated video for everything.

Choose the visual medium based on the concept.

### Programmatic animation
Best for:

- architecture diagrams
- API flows
- databases
- networking
- graphs
- timelines
- state transitions
- UI flows
- technical systems

Recommended technologies to investigate:

- **Remotion**
- **FFmpeg**

### AI-generated illustrations
Best for:

- conceptual scenes
- metaphors
- environments
- characters
- abstract concepts

### AI-generated video
Best for:

- atmosphere
- visual metaphors
- transitions
- simulations
- moments where motion itself adds value

### Screen recordings
Best for:

- actual software behavior
- coding
- tools
- websites
- demos

### Typography / UI-style motion
Best for:

- key statements
- definitions
- equations
- punchlines
- highlighting terminology

The intended result is a **designed educational experience**, not obvious AI output.

---

## 8. Recommended Initial Tech Stack

Keep version 1 small.

### Reasoning / agent
- Claude
- Claude Code / Cowork when useful for interactive work

### Automation
- n8n

### Database
- PostgreSQL

### Storage
- local filesystem initially, then S3-compatible object storage such as Cloudflare R2/S3 when needed

### Rendering
- Remotion
- FFmpeg

### Images
- one high-quality image generation provider

### Video generation
- one suitable provider initially

### Voice
- one high-quality TTS provider such as ElevenLabs or equivalent

### Distribution
- YouTube first
- Instagram second
- TikTok as an additional discovery channel

Do not start by integrating a huge collection of tools.

---

## 9. Content Database

Create a persistent content database from the beginning.

Suggested entity: `ContentItem`

```text
id
series
topic
format
status
idea_score
hook
short_summary
research_notes
sources
script
storyboard
visual_plan
asset_locations
voice_location
render_location
thumbnail_location
title_options
description
publish_targets
scheduled_at
published_at
youtube_url
instagram_url
tiktok_url
views
watch_time
retention
ctr
likes
comments
shares
subscribers_gained
email_signups
revenue
performance_notes
created_at
updated_at
```

Useful statuses:

```text
IDEA
RESEARCHING
RESEARCHED
SCRIPTING
STORYBOARDING
ASSET_GENERATION
RENDERING
QA
AWAITING_APPROVAL
APPROVED
PUBLISHED
ANALYZING
ARCHIVED
```

---

## 10. Claude Agent Roles

Claude can act as several specialized roles.

### A. Idea Agent

Responsibilities:

- discover possible topics
- expand existing concepts
- identify series opportunities
- score topics

Suggested score dimensions:

```text
Educational value
Novelty
Audience demand
Visual potential
Clarity
Series potential
Production difficulty
Commercial potential
```

### B. Research Agent

Responsibilities:

- gather authoritative information
- identify reliable sources
- separate facts from speculation
- produce source-backed notes
- flag uncertainty

### C. Script Agent

Output structure:

```text
Hook
Problem / question
Context
Core explanation
Visual metaphor
Concrete example
Payoff / insight
Conclusion
```

### D. Storyboard Agent

For every segment, specify:

```text
Narration
Visual
Animation
On-screen text
Camera movement
Duration
Sound cue
Asset needed
```

### E. Visual Director Agent

Responsibilities:

- maintain visual consistency
- choose between diagram / illustration / video / screen recording
- write image/video generation prompts
- enforce the visual language

### F. QA Agent

Check:

- factual errors
- unsupported claims
- repetition
- weak hook
- unnecessary sentences
- unclear explanation
- poor visual correspondence
- copyright/IP concerns
- title/thumbnail mismatch

### G. Analytics Agent

Input:

- views
- CTR
- retention
- watch time
- engagement
- subscriber growth
- comments
- conversions

Output:

- what worked
- what failed
- patterns
- suggested experiments
- next topics
- next hooks

---

## 11. n8n Workflow Architecture

### Workflow 1 — Idea ingestion

```text
Schedule
 ↓
Collect candidate questions/topics
 ↓
Claude idea scoring
 ↓
Deduplicate
 ↓
Store in PostgreSQL
```

### Workflow 2 — Research

```text
Select high-scoring idea
 ↓
Claude research task
 ↓
Collect sources
 ↓
Generate research package
 ↓
Store
 ↓
Set status = RESEARCHED
```

### Workflow 3 — Script + storyboard

```text
Research package
 ↓
Claude script
 ↓
Claude critique
 ↓
Claude revision
 ↓
Claude storyboard
 ↓
Store outputs
 ↓
Set status = STORYBOARDING
```

### Workflow 4 — Asset generation

```text
Storyboard
 ↓
Determine asset types
 ├─ diagram
 ├─ screen recording
 ├─ image
 ├─ AI video
 ├─ typography
 └─ audio
 ↓
Generate / collect assets
 ↓
QA assets
 ↓
Store asset manifest
```

### Workflow 5 — Rendering

```text
Storyboard + assets + audio
 ↓
Generate Remotion project/data
 ↓
Render
 ↓
FFmpeg post-processing
 ↓
Generate final MP4
 ↓
Generate captions
```

### Workflow 6 — Approval

```text
Final render
 ↓
Notify creator
 ↓
Creator reviews
 ↓
APPROVE / REJECT / REQUEST CHANGES
```

### Workflow 7 — Publishing

```text
Approved
 ↓
Generate platform-specific metadata
 ↓
Publish / schedule
 ├─ YouTube
 ├─ Instagram
 └─ TikTok
 ↓
Store URLs + publication times
```

### Workflow 8 — Analytics

```text
Scheduled daily/weekly job
 ↓
Fetch metrics
 ↓
Store results
 ↓
Compare against previous videos
 ↓
Claude analysis
 ↓
Update strategy / idea scores
```

---

## 12. Human-in-the-Loop Rule

Do NOT fully automate publishing initially.

Use:

```text
AI creates
 ↓
AI checks
 ↓
HUMAN APPROVAL
 ↓
publish
```

The approval step should be explicit and easy to perform.

Possible approval UI later:

```text
[ Preview Video ]

Title:
Thumbnail:
Description:

Research confidence: 92%
Visual quality: 88%

[ APPROVE ]
[ REQUEST CHANGES ]
[ REJECT ]
```

Automate more only after the quality process is stable.

---

## 13. Production Strategy: Do Not Automate the Unknown

The first 10–20 videos should be **semi-manual**.

Purpose:

- discover visual identity
- discover pacing
- discover narration style
- discover hook style
- discover ideal duration
- discover thumbnail language
- discover which concepts are easiest/hardest to produce
- discover audience response

Only after that should those rules be encoded into automation.

Important principle:

> **First discover the creative system, then automate the system.**

---

## 14. Initial Video Format

Recommended initial format:

### Short visual explainer

Approximate duration:

**30–120 seconds**

Example:

### Topic: What happens when you click Login?

```text
Hook
↓
Browser sends POST /login
↓
API receives credentials
↓
Password is verified against a hash
↓
Server creates session/token
↓
Browser receives authentication state
↓
Future requests carry proof of authentication
```

The visual experience should animate the actual flow.

Then expand successful topics into longer YouTube videos.

---

## 15. Long-Form Expansion

When a short explainer performs well, expand it into:

**4–10 minute YouTube video**

Example:

Short:

> JWT explained in 60 seconds

Long-form:

> JWT Authentication: What Actually Happens Inside Your App

This creates a natural content tree:

```text
One topic
 ├─ Short
 ├─ Long YouTube video
 ├─ Instagram Reel
 ├─ TikTok
 ├─ Carousel
 ├─ Visual cheat sheet
 └─ Newsletter/article
```

One research effort can therefore produce a complete **content package**.

---

## 16. Distribution Strategy

### Primary

**YouTube**

Use it for:

- long-form educational content
- Shorts
- searchable evergreen topics
- building the main content library

### Secondary

**Instagram**

Use for:

- Reels
- carousels
- short visual explainers
- discovery

### Additional

**TikTok**

Use when the format fits.

### Owned channel

Build a simple website/newsletter over time.

Example funnel:

```text
YouTube / Instagram
       ↓
     Website
       ↓
Free visual cheat sheet
       ↓
   Email signup
       ↓
Digital products / services
```

Do not depend completely on platform algorithms.

---

## 17. Monetization Model

Do NOT make the business model simply:

> YouTube ads

Use multiple revenue layers.

### Revenue layer 1 — Platform advertising

Useful eventually, but not the only objective.

### Revenue layer 2 — Sponsorships

Potentially valuable because technical/AI audiences can be commercially relevant.

### Revenue layer 3 — Affiliate revenue

Potentially relevant for:

- AI tools
- developer tools
- SaaS
- hosting
- learning resources

### Revenue layer 4 — Digital products

Potential products:

- visual technical handbooks
- cheat sheets
- architecture templates
- AI workflow templates
- automation blueprints
- educational packs

### Revenue layer 5 — Automation / AI services

This is potentially the most strategically interesting.

The content becomes proof of capability:

```text
Educational content
      ↓
Audience discovers creator
      ↓
Audience trusts creator
      ↓
Companies see automation expertise
      ↓
Paid automation / AI work
```

The business can therefore become:

> **Educational media + AI automation studio**

rather than merely a creator channel.

---

## 18. Metrics

Track two categories.

### Production metrics

```text
Time per video
Cost per video
Manual minutes per video
AI/API cost
Render time
Revision count
Failure rate
```

### Audience/business metrics

```text
Views
Impressions
CTR
Average view duration
Retention
Likes
Comments
Shares
Subscribers gained
Returning viewers
Email signups
Affiliate clicks
Product sales
Client leads
Revenue
```

The most important KPI in early stages is not raw views.

A more meaningful question is:

> **Are high-quality videos getting better over time while production cost/time falls?**

---

## 19. The Learning Loop

The system should eventually become self-improving.

Example:

```text
Publish 30 videos
 ↓
Collect analytics
 ↓
Claude analyzes patterns
 ↓
Finds:
"authentication topics outperform"
 ↓
Increase score for related topics
 ↓
Generate new ideas
 ↓
Publish
 ↓
Measure again
```

The system should learn about:

- topic performance
- hook performance
- length
- visual styles
- pacing
- title patterns
- thumbnail patterns
- audience segments
- conversion patterns

Do not blindly optimize for views. Optimize for the business objective chosen by the creator.

---

## 20. Quality / Platform Guardrails

The objective is original, genuinely useful educational content.

Avoid designing a pipeline whose main purpose is mass production with minimal transformation.

For platform compliance, verify current rules before automating publishing, especially around:

- reused or repetitive content
- synthetic/altered media disclosure
- music/visual licensing
- API quotas and publishing restrictions
- monetization eligibility

Important operating rule:

> **Use AI to create and transform original educational work, not to manufacture interchangeable filler.**

---

## 21. MVP — Phase 1

Build the smallest useful system.

### Goal
Produce one complete video through a partially automated pipeline.

### MVP components

1. PostgreSQL content database
2. n8n
3. Claude
4. one image generation provider
5. one TTS provider
6. Remotion
7. FFmpeg
8. local asset storage
9. manual approval
10. YouTube upload workflow

### MVP workflow

```text
Idea
 ↓
Claude
 ↓
Research
 ↓
Script
 ↓
Storyboard
 ↓
Assets
 ↓
Voice
 ↓
Remotion/FFmpeg
 ↓
Preview
 ↓
Human approval
 ↓
YouTube
```

Do not add Instagram automation, analytics feedback, dashboards, distributed rendering, or multiple AI providers until this works.

---

## 22. Phase 2 — Repeatability

Target: **10–20 videos**.

Build:

- reusable visual templates
- reusable scene components
- standardized storyboard schema
- asset naming conventions
- prompt templates
- content state machine
- failure/retry handling
- approval workflow
- basic analytics collection

Goal:

> Reduce production time without reducing quality.

---

## 23. Phase 3 — Multi-Platform Distribution

Add:

- Instagram
- TikTok
- platform-specific aspect ratios
- platform-specific captions/descriptions
- scheduled publishing
- content repurposing

Example:

```text
One research package
 ↓
1 long video
 ↓
3 Shorts/Reels/TikToks
 ↓
1 carousel
 ↓
1 article/newsletter
```

---

## 24. Phase 4 — Analytics Intelligence

Build:

- dashboard
- performance history
- cohort/series comparisons
- topic scoring based on actual results
- automated weekly strategy report

Claude should answer questions such as:

> Which topics are worth producing more of?

> What makes our strongest videos different?

> Which hooks produce better retention?

> Which visual structures are correlated with higher completion?

> What should the next 10 videos be?

---

## 25. Phase 5 — Semi-Autonomous Studio

Eventually allow:

```text
Monday
 ↓
n8n discovers opportunities
 ↓
Claude proposes 20 ideas
 ↓
Claude researches top ideas
 ↓
Scripts + storyboards generated
 ↓
Assets generated
 ↓
Videos rendered overnight
 ↓
Tuesday morning
 ↓
Creator reviews a queue of completed drafts
 ↓
Approve selected videos
 ↓
Automated distribution
```

This is the point at which the system starts functioning like a small media operation.

---

## 26. Example Internal Data Flow

A single content item should be representable as structured data.

```json
{
  "id": 104,
  "series": "How Software Actually Works",
  "topic": "What Happens When You Click Login?",
  "format": "visual_explainer",
  "status": "AWAITING_APPROVAL",
  "idea_score": 91,
  "hook": "Your browser doesn't actually send your password around the internet the way you might think.",
  "duration_target_seconds": 75,
  "script": "...",
  "storyboard": [
    {
      "scene": 1,
      "duration": 5,
      "narration": "...",
      "visual_type": "diagram",
      "animation": "browser_to_api",
      "assets": []
    }
  ],
  "assets": [],
  "voice": null,
  "video": null,
  "thumbnail": null
}
```

The exact schema can evolve, but the important principle is:

> **Make the production process machine-readable.**

That makes automation, retries, validation, and reuse much easier.

---

## 27. Important Architectural Principle: Separate Intelligence from Orchestration

Do not put all logic inside one giant prompt.

Prefer:

```text
n8n
  ├─ state management
  ├─ triggers
  ├─ retries
  ├─ integrations
  └─ scheduling

Claude
  ├─ reasoning
  ├─ research synthesis
  ├─ creative generation
  ├─ critique
  └─ decision support

Rendering system
  ├─ deterministic scene generation
  └─ video assembly

Database
  └─ persistent truth/state
```

This separation makes the system much easier to debug and upgrade.

---

## 28. What Claude Should Help Design Next

Treat this document as the starting specification.

Claude should next help produce, in order:

### A. Product/system specification

Define:

- components
- services
- data model
- APIs
- file structure
- environments
- secrets management
- failure handling

### B. Content schema

Define concrete JSON schemas for:

- idea
- research package
- script
- storyboard
- asset manifest
- publishing package
- analytics result

### C. n8n workflows

Design the actual workflows node-by-node.

### D. Remotion architecture

Define:

- reusable scene components
- animation primitives
- typography system
- transition system
- diagram components
- data-driven scene JSON format

### E. Prompt system

Create robust prompts/templates for:

- idea agent
- research agent
- script agent
- storyboard agent
- visual director
- QA agent
- analytics agent

### F. MVP implementation

Build the first end-to-end pipeline.

### G. First 10 videos

Develop the initial content batch while refining the production system.

---

## 29. Decision Rules

When there are multiple possible approaches, prioritize:

1. Quality over volume.
2. Simple architecture over tool sprawl.
3. Deterministic code for technical animations.
4. AI generation where it adds visual value.
5. Human approval before publishing initially.
6. Structured data over ad-hoc files/prompts.
7. Measurement over intuition.
8. Reusable components over one-off workflows.
9. Owned audience (email/site) over total dependence on social platforms.
10. Business value over vanity metrics.

---

## 30. The Actual Experiment

The business question is not:

> "Can AI make YouTube videos?"

The experiment is:

> **Can I use my design taste + technical knowledge + AI + automation to produce educational content that people genuinely value, while reducing the marginal cost/time of production enough to make the operation economically viable?**

### First benchmark

Produce **10–15 strong videos**.

For every video record:

- production time
- production cost
- revision count
- CTR
- retention
- views
- subscribers gained
- comments/shares
- email signups
- revenue/client leads

Then decide whether the concept deserves another 20–50 videos.

Do not attempt to scale before the first format demonstrates quality and audience response.

---

## 31. Final Strategic Position

The intended end state is not:

> "I have an AI that makes videos."

It is:

> **"I have a repeatable AI-native educational media system that turns ideas into researched, designed, animated, reviewed, and distributed content—and learns from audience response."**

That system can potentially create multiple forms of value:

```text
Content
  ↓
Audience
  ↓
Trust
  ├──────────────┐
  ↓              ↓
Products       Services
  ↓              ↓
Revenue        Revenue
       \        /
        \      /
         Business
```

The most important asset is therefore not the automation itself.

It is the **combination of editorial judgment, distinctive design, useful subject matter, and a system that compounds what is learned.**

---

## 32. Immediate Next Task for Claude

Start by turning this brief into a **concrete MVP implementation plan**.

The plan should specify:

1. Exact tool stack.
2. Local development setup.
3. PostgreSQL schema.
4. Folder/repository structure.
5. n8n workflow definitions.
6. Claude prompt/agent definitions.
7. Remotion project architecture.
8. Asset manifest format.
9. Human approval mechanism.
10. First YouTube publishing path.
11. Logging/error handling.
12. Estimated cost per video.
13. First 10-video content test plan.
14. Clear milestones from MVP → semi-automated studio.

Do not over-engineer the MVP.

The first objective is to get **one genuinely good video from idea → research → script → storyboard → assets → render → human approval → YouTube**.

Then iterate.

---

## Reference Documentation

These are useful official sources to verify while implementing platform integrations and policies:

- n8n documentation: https://docs.n8n.io/
- YouTube Data API: https://developers.google.com/youtube/v3/
- YouTube video upload API: https://developers.google.com/youtube/v3/docs/videos/insert
- YouTube monetization / YPP: https://support.google.com/youtube/answer/72851
- YouTube Partner Program availability: https://support.google.com/youtube/answer/7101720
- YouTube monetization/content policies: https://support.google.com/youtube/answer/1311392
- YouTube altered/synthetic content policy: https://support.google.com/youtube/answer/14328491
- Remotion: https://www.remotion.dev/
- FFmpeg: https://ffmpeg.org/
