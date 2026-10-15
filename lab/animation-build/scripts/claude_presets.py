"""Claude emotion presets as values of the ctrl custom properties (eyes and body are separate so they can be mixed).
Used by the sheets (claude_sheet.py) and by the action builder (milestone 5)."""
EYE_DEFAULT = dict(eye_open=1.0, eye_h_L=1.0, eye_h_R=1.0, eye_w=1.0, eye_y=0.0, look_x=0.0, look_y=0.0, eye_roll=0.0, glint=1.0, blush=0.0)
BODY_DEFAULT = dict(arm_L=0.0, arm_R=0.0, arm_fwd_L=0.0, arm_fwd_R=0.0, squash=0.0, lean=0.0, nod=0.0, turn=0.0, bob=0.0)
EMOTIONS = ["neutral", "happy", "curious", "excited", "surprised", "thoughtful", "proud", "amused"]
EYES = {   # cute rules: bigger glints, eyes set a little low (baby schema), blush, no stern tilts
 "neutral":    {},
 "happy":      dict(eye_h_L=.8, eye_h_R=.8, eye_w=1.2, eye_y=-.02, glint=1.5, blush=1.0),
 "curious":    dict(eye_h_L=1.2, eye_h_R=1.0, eye_w=1.1, eye_y=-.015, look_x=.025, look_y=.03, glint=1.5),
 "excited":    dict(eye_h_L=1.1, eye_h_R=1.1, eye_w=1.25, eye_y=-.015, glint=1.7, blush=.9),
 "surprised":  dict(eye_h_L=1.3, eye_h_R=1.3, eye_w=1.55, eye_y=-.01, glint=1.7, blush=.0),
 "thoughtful": dict(eye_h_L=1.0, eye_h_R=1.0, eye_w=1.1, eye_y=-.015, look_x=-.04, look_y=.035, glint=1.4),
 "proud":      dict(eye_h_L=.7, eye_h_R=.7, eye_w=1.25, eye_y=-.015, look_y=-.01, glint=1.5, blush=.6),
 "amused":     dict(eye_h_L=.3, eye_h_R=.95, eye_w=1.2, eye_y=-.015, glint=1.4, blush=.9),
}
BODY = {
 "neutral":    {},
 "happy":      dict(bob=.03, squash=-.12, arm_L=45, arm_R=45, lean=4),
 "curious":    dict(lean=7, arm_R=25),
 "excited":    dict(bob=.07, squash=-.3, arm_L=100, arm_R=100),
 "surprised":  dict(squash=-.4, bob=.04, arm_L=60, arm_R=60),
 "thoughtful": dict(lean=-5, arm_R=60, arm_fwd_R=25),
 "proud":      dict(squash=-.3, bob=.02, arm_L=15, arm_R=15),
 "amused":     dict(squash=.12, lean=5, bob=.015, arm_L=30, arm_R=30),
}
def preset(eyes="neutral", body="neutral"):
    d = dict(EYE_DEFAULT); d.update(BODY_DEFAULT); d.update(EYES[eyes]); d.update(BODY[body]); return d
