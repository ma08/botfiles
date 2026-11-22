import React from 'react';
import {S01Claim} from './S01Claim';
import {S02Primes} from './S02Primes';
import {S03Zeros} from './S03Zeros';
import {S04Music} from './S04Music';
import {S05Parallel} from './S05Parallel';
import {S06Stepanov} from './S06Stepanov';
import {S07Wall} from './S07Wall';
import {S08Ladder} from './S08Ladder';
import {S09ToyAndEnd} from './S09ToyAndEnd';
import {S10Box} from './S10Box';
import {S11Checks} from './S11Checks';
import {S12Next} from './S12Next';

// Scene registry: one file per scene; builders edit only their own file.
export const SCENES: Record<string, React.FC> = {
  s01_claim: S01Claim,
  s02_primes: S02Primes,
  s03_zeros: S03Zeros,
  s04_music: S04Music,
  s05_parallel: S05Parallel,
  s06_stepanov: S06Stepanov,
  s07_wall: S07Wall,
  s08_ladder: S08Ladder,
  s09_toy_and_end: S09ToyAndEnd,
  s10_box: S10Box,
  s11_checks: S11Checks,
  s12_next: S12Next,
};
