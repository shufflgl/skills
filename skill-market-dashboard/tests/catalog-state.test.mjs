import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { filterCatalog } from "../app/catalog.ts";

const skills = [
  {
    name: "book-skill",
    skillId: "$book-skill",
    displayName: "Book Skill",
    summary: "Inspect an EPUB.",
    description: "Runs for book files.",
    category: "Books",
  },
  {
    name: "media-skill",
    skillId: "$media-skill",
    displayName: "Media Skill",
    summary: "Summarize a video.",
    description: "Runs for video links.",
    category: "Media",
  },
];

const workflows = [
  {
    kind: "workflow",
    name: "media-workflow",
    displayName: "Media Workflow",
    summary: "Move finished audio into a music library.",
    category: "Media",
  },
];

const items = [...skills.map((skill) => ({ kind: "skill", ...skill })), ...workflows];

test("searches skills and workflows", () => {
  assert.deepEqual(filterCatalog(items, "EPUB", "All", "All").map((item) => item.name), ["book-skill"]);
  assert.deepEqual(filterCatalog(items, "music library", "All", "All").map((item) => item.name), ["media-workflow"]);
});

test("filters by tab and category", () => {
  assert.deepEqual(filterCatalog(items, "", "Media", "Skills").map((item) => item.name), ["media-skill"]);
  assert.deepEqual(filterCatalog(items, "", "Media", "Workflows").map((item) => item.name), ["media-workflow"]);
});

test("generated public data contains categorized skills and no personal absolute paths", async () => {
  const catalog = await readFile(new URL("../.generated/catalog.json", import.meta.url), "utf8");
  assert.doesNotMatch(catalog, /\/(?:Users|home|private|Volumes)\//);
  const snapshot = JSON.parse(catalog);
  assert.ok(snapshot.skills.every((skill) => typeof skill.category === "string"));
  for (const workflow of snapshot.workflows) {
    assert.equal(typeof workflow.category, "string");
  }
});
