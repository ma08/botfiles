import React from 'react';
import {S01Hook} from './S01Hook';
import {S02Proof} from './S02Proof';

// Scene registry: scene id (from script/script.json) -> component. One file per scene, so parallel
// scene builders each own their own file. Unknown ids can use <Placeholder id=... index=... /> while drafting.
export const SCENES: Record<string, React.FC> = {
  s01_hook: S01Hook,
  s02_proof: S02Proof,
};
