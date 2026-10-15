# Emotions: the faceless guy (living list, update when an emotion changes)

Character file: `character_selection_lab.blend` (same folder). Built by `scripts/build_emotions.py`.

## Who he is
No eyes, no mouth. A quiet, almost soulless man who has not talked to real people for a long time and only talks
to his imaginary friend "Claude". He reacts, but small and inward: a little brow movement, a head tilt, the
shoulders, the hands, and above all **timing** (delays, stillness, slowness).
Not used: eyes, a mouth, raised hands/arms (maybe later), big gestures.

## References (what to borrow)
| Reference | Borrow |
|---|---|
| Buster Keaton, "The Great Stone Face" | an unchanging face; emotion from stillness, timing and tiny body moves |
| Theodore in *Her* | a lonely man talking to an AI; quiet, inward, delayed reactions |
| K in *Blade Runner 2049* (and Joi) | flat face, isolation; slight brow tension, posture, very slow head turns |
| Mark S. in *Severance* | suppressed emotion leaking out as micro-movements |
| Six in *Little Nightmares* | face hidden by a hood; posture, head angle and hands carry everything |
| The kid in *Inside*, the traveler in *Journey* | faceless characters that read through movement alone |
| No-Face (Kaonashi), *Spirited Away* | blank face; loneliness through slow approach and stillness |
| Pixar's *Luxo Jr.* | head tilt, timing and weight are enough |

## Channels he uses
1. **Brow ridge** (shape keys, driven by properties on the rig's `head` bone):
   `brow_up_L/R`, `brow_down_L/R`, `brow_inner_up`, `brow_squeeze` (L/R = the character's left/right).
2. **Head and neck**: tilt, slow turn, small nod, look-away. Claude sits on his **left**.
3. **Shoulders and chest**: slump, lift, open/close (breathing is shown in animation, not in stills).
4. **Hands and fingers**: tightening, a still hand, a nervous finger.
5. **Lean**: toward (interest) or away (withdrawal).
6. **Timing**: written in the table for the animation step; the stills show the held pose.

## The emotions (stills: `stills/emotions/NN_name.jpg`, overview `stills/emotions/00_overview.jpg`)
| # | Emotion | Brow | Head / neck | Body / hands | Timing (for animation) |
|---|---|---|---|---|---|
| 01 | Neutral (empty), the default | relaxed | slightly down | shoulders a little slumped | almost still, tiny idle sway |
| 02 | Listening to Claude | neutral | small tilt and turn toward Claude (left) | hands still | holds the tilt |
| 03 | Curious | slightly up | tilt, small lean in | still | short pause first |
| 04 | Surprised (small) | up | small pull back | quick inhale, shoulders lift a little, fingers open | fast in, slow out |
| 05 | Confused | one up (left), one slightly down (right) | slow tilt to his right | still | long hold |
| 06 | Thoughtful | inner corners slightly up, a bit low | down and away (to his right) | still | slow, long |
| 07 | Annoyed / angry (quiet) | down and pulled together | chin slightly down | fists, shoulders stiff and a little up | abrupt stop, then stillness |
| 08 | Sad / lonely | inner corners up | head down | shoulders drop, chest sinks | very slow |
| 09 | Tired / drained | heavy, low | head hangs | deep slump, arms heavy | sluggish |
| 10 | Amused (no mouth) | slightly up | small dip, turned toward Claude | shoulders up a little (a silent laugh) | quick, small |
| 11 | Happy (rare, quiet) | softly up | head lifts a little | chest opens, slight lean back | slow, warm |
| 12 | Awkward / nervous | up and tense | quick look-away | shoulders up, one finger fidgets | jittery |
| 13 | Agreeing | neutral | small nod (held at the bottom) | - | slow, 1-2 nods |
| 14 | Disagreeing | slightly down | small head shake (held to one side) | - | slow |
| 15 | Zoning out | relaxed | gaze fixed, slightly down | limp arms, slumped | long stillness, breathing only |
| 16 | Excited (contained) | up | lifts toward Claude, small lean in | chest up, hands open a little | faster breathing |
| 17 | Proud (quiet) | neutral to slightly down | chin slightly up | shoulders back, chest open | slow |

**Speaking without a mouth** (not a still): a subtle chin/head pulse plus a breath on each phrase.

**Mapping to the scene's older emotion set** (happy, curious, excited, surprised, thoughtful, proud, amused):
11, 03, 16, 04, 06, 17, 10.

## Change log
- 2026-10-12: first version (17 emotions, brow shape keys + body poses as actions `EMO_NN_name`).
- 2026-10-12: neutral = the creator's corrected standing pose (`scripts/neutral_pose.json`); all 17 emotions rebuilt
  on top of it, brow keys rebuilt on the edited head, image pack re-rendered.
