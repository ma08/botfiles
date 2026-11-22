// Zeta-only smoothed, weighted prime sum, computed deterministically at module load:
//   Gz(x) = sum_{n<=x} Lambda(n) (x/n - 1) - x log x + (1 + gamma) x
// Lambda is the von Mangoldt function (log p on prime powers p^k, else 0).
// Sampled every 100 up to 100,000 (the curve is continuous: jumps cancel at prime powers).

export const GZ_XMAX = 100_000;

export const GZ_POINTS: [number, number][] = (() => {
  const N = GZ_XMAX;
  const sieve = new Uint8Array(N + 1).fill(1);
  sieve[0] = 0;
  sieve[1] = 0;
  for (let i = 2; i * i <= N; i++) {
    if (sieve[i]) for (let j = i * i; j <= N; j += i) sieve[j] = 0;
  }
  const lam = new Float64Array(N + 1);
  for (let p = 2; p <= N; p++) {
    if (!sieve[p]) continue;
    const lp = Math.log(p);
    for (let q = p; q <= N; q *= p) lam[q] = lp;
  }
  const gamma = 0.5772156649015329;
  let s1 = 0;
  let psi = 0;
  const pts: [number, number][] = [];
  for (let n = 1; n <= N; n++) {
    s1 += lam[n] / n;
    psi += lam[n];
    if (n % 100 === 0) pts.push([n, n * s1 - psi - n * Math.log(n) + (1 + gamma) * n]);
  }
  return pts;
})();
