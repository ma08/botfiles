// Exact prime counting up to 10^6 (sieve) plus li(x) and the RH-style band.
// Cross-checked offline against src/data/primes.json (stair100, view1e4, view1e6, facts).
// Used so the camera can zoom continuously from x = 100 to x = 10^6 with exact stairs.

export const PI_MAX_X = 1_000_000;

const buildPrefix = () => {
  const n = PI_MAX_X;
  const composite = new Uint8Array(n + 1);
  const prefix = new Int32Array(n + 1);
  composite[0] = 1;
  composite[1] = 1;
  for (let i = 2; i * i <= n; i++) {
    if (!composite[i]) for (let j = i * i; j <= n; j += i) composite[j] = 1;
  }
  let c = 0;
  for (let i = 0; i <= n; i++) {
    if (!composite[i]) c++;
    prefix[i] = c;
  }
  return prefix;
};

const PREFIX = buildPrefix();

/** pi(x): number of primes <= x (exact for 0 <= x <= 10^6). */
export const primePi = (x: number) => PREFIX[Math.max(0, Math.min(PI_MAX_X, Math.floor(x)))];

const EULER_GAMMA = 0.5772156649015329;

/** Logarithmic integral li(x) (principal value; li(2) = 1.045...), via the Ramanujan-Soldner series. */
export const li = (x: number) => {
  if (x <= 1) return 0;
  const L = Math.log(x);
  let term = 1;
  let sum = 0;
  for (let k = 1; k < 200; k++) {
    term *= L / k; // L^k / k!
    const add = term / k;
    sum += add;
    if (add < 1e-12 * sum) break;
  }
  return EULER_GAMMA + Math.log(L) + sum;
};

/** Half-width of the band li(x) +/- sqrt(x) log(x) / (8 pi). */
export const band = (x: number) => (x <= 1 ? 0 : (Math.sqrt(x) * Math.log(x)) / (8 * Math.PI));

/** All primes <= 10^6 in order (derived from the same prefix counts). */
export const PRIMES: number[] = (() => {
  const out: number[] = [];
  for (let i = 2; i <= PI_MAX_X; i++) if (PREFIX[i] !== PREFIX[i - 1]) out.push(i);
  return out;
})();

/** 37607912018 -> "37,607,912,018" (deterministic, no locale dependency). */
export const fmt = (n: number) => {
  const neg = n < 0;
  const s = String(Math.round(Math.abs(n)));
  let out = '';
  for (let i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 === 0) out += ',';
    out += s[i];
  }
  return (neg ? '-' : '') + out;
};
