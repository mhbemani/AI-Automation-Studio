import React from "react";
import { Composition, CalculateMetadataFunction } from "remotion";
import { Video, Project } from "./Video";
import defaults from "../default.json";
import { AbsoluteFill } from "remotion";
import { CharacterOverlay } from "./Character";
import { geo } from "./layout";

const meta: CalculateMetadataFunction<Project> = ({ props }) => ({ durationInFrames: Math.round(props.durationSec * props.fps), fps: props.fps });

// flicker bisect only: the character overlay alone on black, fixed left layout (compare against an FFmpeg reference composite)
const CharCheck: React.FC<Project> = ({ character, scenes }) => (
  <AbsoluteFill style={{ background: "#000" }}><CharacterOverlay cfg={character} geos={[geo("presenter_left_diagram_right", 1920, 1080)]} starts={[0]} T={0.5} /></AbsoluteFill>
);
export const Root: React.FC = () => (
  <>
    <Composition id="Video" component={Video} fps={30} width={1920} height={1080} durationInFrames={900} defaultProps={defaults as Project} calculateMetadata={meta} />
    <Composition id="CharCheck" component={CharCheck} fps={30} width={1920} height={1080} durationInFrames={900} defaultProps={defaults as Project} calculateMetadata={meta} />
    <Composition id="VideoVertical" component={Video} fps={30} width={1080} height={1920} durationInFrames={900} defaultProps={defaults as Project} calculateMetadata={meta} />
  </>
);
