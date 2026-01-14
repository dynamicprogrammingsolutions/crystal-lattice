const args = new Map<string, string>();
for (const s of Bun.argv.slice(2)) {
  const i = s.indexOf("=");
  if (i > 0) args.set(s.slice(0, i).replace(/^--/, ""), s.slice(i + 1));
}

const out = args.get("dir") ?? "chain";
const hops = Number(args.get("hops") ?? "10");
const m = Number(args.get("m") ?? "6");
const start = Number(args.get("start") ?? "5");
const seedIn = args.get("seed") ?? "opencode";

const to32 = (s: string) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
};

const rnd32 = (s: number) => {
  let a = s >>> 0;
  return () => {
    a += 0x6D2B79F5;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

const r = rnd32(to32(seedIn));

const ensureDir = async (p: string) => {
  await import("fs/promises").then(x => x.mkdir(p, { recursive: true }));
};

const int = (min: number, max: number) => Math.floor(r() * (max - min + 1)) + min;

const write = async (p: string, o: unknown) => {
  const s = JSON.stringify(o, null, 2) + "\n";
  await Bun.write(p, s);
};

const genStart = async () => {
  await ensureDir(out);
  const list: Array<Promise<void>> = [];
  for (let a = 0; a < start; a++) {
    const file = `${out}/start_${a}.json`;
    const o = { token: int(0, 9), d: int(0, 6), b: int(0, 2), k: int(0, m - 1), m };
    list.push(write(file, o));
  }
  await Promise.all(list);
};

const genSteps = async () => {
  const list: Array<Promise<void>> = [];
  for (let t = 2; t <= hops; t++) {
    for (let j = 0; j < m; j++) {
      const file = `${out}/step${t}_${j}.json`;
      const o = { token: (t + 2 * j) % 10, d: (t + j) % 7, b: (t + j) % 3, k: (t + 3 * j) % m, m };
      list.push(write(file, o));
    }
  }
  await Promise.all(list);
};

await genStart();
await genSteps();

console.log(`generated: start_${start} and steps up to ${hops} with m=${m} in ${out}`);
