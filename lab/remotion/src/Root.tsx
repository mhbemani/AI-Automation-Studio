import React from "react";
import { Composition, CalculateMetadataFunction } from "remotion";
import { Flow, Scene } from "./Flow";
import defaults from "../scenes/request-flow.json";

const FPS = 30;
const meta: CalculateMetadataFunction<Scene> = ({ props }) => ({ durationInFrames: Math.round(props.durationSec * FPS) });

export const Root: React.FC = () => (
  <>
    <Composition id="Flow" component={Flow} fps={FPS} width={1920} height={1080} durationInFrames={450} defaultProps={defaults as Scene} calculateMetadata={meta} />
    <Composition id="FlowVertical" component={Flow} fps={FPS} width={1080} height={1920} durationInFrames={450} defaultProps={defaults as Scene} calculateMetadata={meta} />
  </>
);
