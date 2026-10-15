import React from "react";
import { Composition, CalculateMetadataFunction } from "remotion";
import { Video, Project } from "./Video";
import defaults from "../default.json";

const meta: CalculateMetadataFunction<Project> = ({ props }) => ({ durationInFrames: Math.round(props.durationSec * props.fps), fps: props.fps });

export const Root: React.FC = () => (
  <>
    <Composition id="Video" component={Video} fps={30} width={1920} height={1080} durationInFrames={900} defaultProps={defaults as Project} calculateMetadata={meta} />
    <Composition id="VideoVertical" component={Video} fps={30} width={1080} height={1920} durationInFrames={900} defaultProps={defaults as Project} calculateMetadata={meta} />
  </>
);
