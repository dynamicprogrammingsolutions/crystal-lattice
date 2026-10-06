import assert from "node:assert/strict";
import test from "node:test";
import { focusGeometry, stackedPopupGeometry, validateSessionActionsContract } from "../../scripts/visual-assets/session-actions-composition.mjs";

test("a relationship cannot claim a different plugin or action label than its schema", () => {
  const mappings = [
    { package: "session-title-app", plugin: "session_title", id: "edit_title_from_view", label: "Edit title", actionId: "set_session_title" },
    { package: "generate-title-app", plugin: "generate_title", id: "generate_title_from_view", label: "Generate title", actionId: "generate_title_for_session" },
    { package: "summarize-range-app", plugin: "summarize_range", id: "summarize_range", label: "Summarize range", actionId: "summarize_range" },
  ];
  const config = { plugins: mappings.map(row => `path:plugins/${row.package}`) };
  const contract = {
    configExcerpt: config, mappings,
    schema: mappings.map(row => ({
      id: row.id, plugin: row.plugin, label: row.label, action_id: row.actionId, ui_type: "session_action",
    })),
  };
  validateSessionActionsContract(contract, config);
  const altered = structuredClone(contract);
  altered.schema[1].label = "A made-up action";
  assert.throws(() => validateSessionActionsContract(altered, config));
  const wrongOwner = structuredClone(contract);
  wrongOwner.schema[0].plugin = "another_plugin";
  assert.throws(() => validateSessionActionsContract(wrongOwner, config));
});

test("focus geometry retains intervening real rows and rejects off-canvas magnification", () => {
  const geometry = {
    popover: { x: 700, y: 100, width: 340, height: 600 },
    rows: [
      { frame: { x: 712, y: 160, width: 270, height: 44 } },
      { frame: { x: 712, y: 204, width: 270, height: 44 } },
      { frame: { x: 712, y: 336, width: 270, height: 44 } },
    ],
  };
  const layout = { height: 1600, focus: { x: 600, y: 500, width: 500, labelOnly: true } };
  const focus = focusGeometry(geometry, layout);
  assert.equal(focus.y, 52);
  assert.equal(focus.height, 236);
  assert.throws(() => focusGeometry(geometry, { ...layout, height: 650 }));
});

test("stacked popup keeps native chrome, marks omissions, and maps only the real action rows", () => {
  const geometry = {
    popover: { x: 1252, y: 198, width: 346, height: 479 },
    rows: [526, 570, 614].map((y, index) => ({
      id: `action-${index}`,
      frame: { x: 1277, y, width: 252, height: 44 },
    })),
  };
  const layout = { height: 1600, focus: { y: 880, width: 1008, headerHeight: 64, cropBreakHeight: 14, outlineInset: 12 } };
  const excerpt = stackedPopupGeometry(geometry, layout);
  assert.equal(excerpt.headerHeight, 64);
  assert.equal(excerpt.bodyTop, 320);
  assert.equal(excerpt.left, 12);
  assert.equal(excerpt.width, 322);
  assert.equal(excerpt.bottom, 467);
  assert.deepEqual(excerpt.omitted, { y: 64, height: 256 });
  assert.deepEqual(excerpt.rows.map(row => row.id), geometry.rows.map(row => row.id));
  assert.equal(new Set(excerpt.rows.map(row => row.color)).size, 3);
  for (const row of excerpt.rows) {
    assert.ok(row.x >= 0 && row.x + row.width <= geometry.popover.width);
    assert.ok(row.y >= excerpt.bodyTop && row.y + row.height <= geometry.popover.height);
  }
  assert.throws(() => stackedPopupGeometry(geometry, { ...layout, height: 1200 }));
});