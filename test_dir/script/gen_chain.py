import argparse
import json
import os
from pathlib import Path


def fnv1a_32(s: str) -> int:
    h = 0x811C9DC5
    for ch in s:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


class PRNG:
    def __init__(self, seed: int):
        self.a = seed & 0xFFFFFFFF

    def next(self) -> float:
        self.a = (self.a + 0x6D2B79F5) & 0xFFFFFFFF
        t = (self.a ^ (self.a >> 15)) * (1 | self.a)
        t &= 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (61 | t)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        t ^= t >> 14
        return (t & 0xFFFFFFFF) / 4294967296.0

    def randint(self, lo: int, hi: int) -> int:
        if lo > hi:
            lo, hi = hi, lo
        r = self.next()
        return lo + int(r * (hi - lo + 1))


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def gen_start(dir_path: Path, start: int, m: int, rng: PRNG) -> None:
    for a in range(start):
        data = {
            "token": rng.randint(0, 9),
            "d": rng.randint(0, 6),
            "b": rng.randint(0, 2),
            "k": rng.randint(0, m - 1),
            "m": m,
        }
        write_json(dir_path / f"start_{a}.json", data)


def gen_steps(dir_path: Path, hops: int, m: int) -> None:
    for t in range(2, hops + 1):
        for j in range(m):
            data = {
                "token": (t + 2 * j) % 10,
                "d": (t + j) % 7,
                "b": (t + j) % 3,
                "k": (t + 3 * j) % m,
                "m": m,
            }
            write_json(dir_path / f"step{t}_{j}.json", data)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="chain")
    p.add_argument("--hops", type=int, default=10)
    p.add_argument("--m", type=int, default=6)
    p.add_argument("--start", type=int, default=5)
    p.add_argument("--seed", default="opencode")
    args = p.parse_args()

    out_dir = Path(args.dir)
    hops = max(2, int(args.hops))
    m = max(1, int(args.m))
    start = max(1, int(args.start))
    seed = str(args.seed)

    rng = PRNG(fnv1a_32(seed))
    gen_start(out_dir, start, m, rng)
    gen_steps(out_dir, hops, m)
    print(f"generated: start_{start} and steps up to {hops} with m={m} in {out_dir}")


if __name__ == "__main__":
    main()
