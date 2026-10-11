import assert from "node:assert/strict";
import test from "node:test";
import { nativeExcerptGeometry } from "../../scripts/visual-assets/proof-batch-composition.mjs";

const native = { size: { width: 1520, height: 1464 }, geometry: { width: 760, height: 732 } };

test("native report crops preserve capture scale and reject hidden off-canvas content", () => {
  const crop = { x: 0, y: 0, width: 760, height: 518 };
  const result = nativeExcerptGeometry(native, crop, { x: 900, y: 180, width: 1440 },
    { width: 2400, height: 1350 });
  assert.equal(result.crop, "1520x1036+0+0");
  assert.equal(result.destination.height, 518 * 1440 / 760);
  assert.throws(() => nativeExcerptGeometry(native,
    { ...crop, height: 733 }, { x: 900, y: 180, width: 1440 }, { width: 2400, height: 1350 }));
  assert.throws(() => nativeExcerptGeometry(native,
    crop, { x: 1000, y: 180, width: 1440 }, { width: 2400, height: 1350 }));
});