# /// script
# requires-python = ">=3.10"
# dependencies = ["mpmath", "numpy"]
# ///
"""Generate real data for the RH explainer scenes. Writes JSON into public/data/."""
import json, math
from pathlib import Path
import numpy as np
import mpmath as mp

OUT = Path(__file__).resolve().parent.parent / "public" / "data"
OUT.mkdir(parents=True, exist_ok=True)
mp.mp.dps = 30


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, separators=(",", ":")))
    print("wrote", name)


# ---------- primes ----------
N = 1_000_000
sieve = np.ones(N + 1, dtype=bool); sieve[:2] = False
for i in range(2, int(N ** 0.5) + 1):
    if sieve[i]:
        sieve[i * i::i] = False
primes = np.nonzero(sieve)[0]
pi_cum = np.cumsum(sieve)


def li(x):
    return float(mp.li(x)) if x >= 2 else 0.0


# Staircase up to 100 (integers) and zoomed views
stair100 = {"x": list(range(0, 101)), "pi": [int(pi_cum[x]) for x in range(0, 101)],
            "primes": [int(p) for p in primes[primes <= 100]]}
def view(xmax, n=600):
    xs = np.linspace(2, xmax, n)
    return {"xmax": xmax,
            "x": [round(float(x), 3) for x in xs],
            "pi": [int(pi_cum[int(x)]) for x in xs],
            "li": [round(li(float(x)), 3) for x in xs],
            "band": [round(math.sqrt(x) * math.log(x) / (8 * math.pi), 3) for x in xs]}
dump("primes.json", {
    "stair100": stair100,
    "view1e4": view(10_000),
    "view1e6": view(1_000_000),
    "facts": {"pi_1e12": 37607912018, "li_minus_pi_1e12": 38263,
              "pi_1e6": int(pi_cum[N]), "li_1e6": round(li(1e6), 1)},
})

# ---------- zeta zeros ----------
zeros = [float(mp.zetazero(k).imag) for k in range(1, 101)]
dump("zeros.json", {"gammas": [round(g, 6) for g in zeros]})

# ---------- explicit formula for psi ----------
xs = np.linspace(1.5, 40, 900)
# true psi (Chebyshev), using prime powers
def psi_true(x):
    s = 0.0
    for p in primes[primes <= x]:
        pk = p
        while pk <= x:
            s += math.log(p); pk *= p
    return s
psi = [round(psi_true(x), 4) for x in xs]
rhos = [mp.mpc(0.5, g) for g in zeros]
def psi_partial(x, n):
    x = mp.mpf(x)
    tot = x - mp.log(2 * mp.pi) - 0.5 * mp.log(1 - x ** -2)
    for r in rhos[:n]:
        tot -= 2 * mp.re(x ** r / r)
    return float(tot)
partials = {}
for n in (1, 3, 10, 30, 100):
    partials[str(n)] = [round(psi_partial(x, n), 4) for x in xs]
waves = {}
for k in range(3):
    waves[str(k + 1)] = [round(float(-2 * mp.re(mp.mpf(x) ** rhos[k] / rhos[k])), 4) for x in xs]
dump("explicit.json", {"x": [round(float(x), 4) for x in xs], "psi": psi, "partials": partials, "waves": waves})

# ---------- primes by last digit ----------
checkpoints = [int(v) for v in np.unique(np.round(np.logspace(1, 6, 120)).astype(int))]
counts = {d: [] for d in ("1", "3", "7", "9")}
for c in checkpoints:
    ps = primes[primes <= c]
    for d in counts:
        counts[d].append(int(np.sum(ps % 10 == int(d))))
dump("lastdigit.json", {"x": checkpoints, "counts": counts})

# ---------- a curve over F_p ----------
p = 31
A, B = 1, 3  # 41 points vs expected 32: deviation 9, inside the Hasse bound 2*sqrt(31) ~ 11.1
pts = [(x, y) for x in range(p) for y in range(p) if (y * y - (x ** 3 + A * x + B)) % p == 0]
n_aff = len(pts)
dump("curve.json", {"p": p, "equation": f"y^2 = x^3 + {A}x + {B}", "points": pts,
                    "count_projective": n_aff + 1, "expected": p + 1, "bound": round(2 * math.sqrt(p), 3)})

# ---------- Lean + timeline facts ----------
dump("lean.json", {
    "files": 175187, "lines": 17374215, "comments": 0, "sorry": 0, "axiom_decls": 0, "native_decide": 0,
    "compressed_bytes": 239275554, "toolchain": "Lean v4.33.1 · Mathlib v4.33.1",
    "main_lean": [
        "import Statements",
        "import Supplements.Kernels.MainTheoremsAll",
        "",
        "theorem riemannHypothesis : RiemannHypothesis := rhOfAll",
        "",
        "theorem riemannZeta_eq_zero_re : RiemannZetaZerosOnLine := rhOfAll",
        "",
        "theorem LFunction_ne_zero_of_half_lt_re : DirichletLNonvanishingRightOfHalf := allChi",
        "",
        "theorem LFunction_eq_zero_re : DirichletLZerosOnLine := claimAll.2.1",
        "",
        "theorem LFunction_eq_zero_re_of_isPrimitive : PrimitiveDirichletLZerosOnLine := critAll",
    ],
    "mathlib_rh": [
        "def RiemannHypothesis : Prop :=",
        "  ∀ (s : ℂ) (_ : riemannZeta s = 0) (_ : ¬∃ n : ℕ, s = -2 * (n + 1)) (_ : s ≠ 1),",
        "    s.re = 1 / 2",
    ],
})
dump("notetimeline.json", {"items": [
    {"date": "2026-10-06", "label": "Stepanov determinant"},
    {"date": "2026-10-08", "label": "first positivity test"},
    {"date": "2026-10-09", "label": "derivatives on CM curves"},
    {"date": "2026-10-14", "label": "period determinants"},
    {"date": "2026-10-19", "label": "toy: qN = M^k + R"},
    {"date": "2026-10-20", "label": "switch to the smoothed prime sum"},
    {"date": "2026-11-15", "label": "iterated theta lifts, m ~ sqrt X", "cluster": 8},
    {"date": "2026-11-16", "label": "GRH"},
]})
