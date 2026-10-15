import React from 'react';
import {AbsoluteFill, Composition, OffthreadVideo, Html5Video, staticFile} from 'remotion';

// Character clip (VP9 alpha webm) composited next to a "diagram" panel on navy.
const Test: React.FC<{method: 'offthread' | 'html5'}> = ({method}) => (
  <AbsoluteFill style={{background: '#0b1020'}}>
    <AbsoluteFill style={{left: 80, top: 200, width: 900, height: 600, borderRadius: 24, background: '#1b2547', color: '#9fb3ff', fontSize: 48, padding: 40, fontFamily: 'sans-serif'}}>
      Diagram goes here
    </AbsoluteFill>
    <AbsoluteFill style={{left: 960}}>
      {method === 'offthread'
        ? <OffthreadVideo src={staticFile('facet.webm')} transparent muted />
        : <Html5Video src={staticFile('facet.webm')} muted />}
    </AbsoluteFill>
  </AbsoluteFill>
);
export const Root: React.FC = () => (
  <>
    <Composition id="Offthread" component={Test} defaultProps={{method: 'offthread' as const}} durationInFrames={360} fps={30} width={1920} height={1080} />
    <Composition id="Html5" component={Test} defaultProps={{method: 'html5' as const}} durationInFrames={360} fps={30} width={1920} height={1080} />
  </>
);
