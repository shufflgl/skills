import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  buildConsoleSearch,
  filterSkills,
  parseConsoleState,
} from "../app/catalog.ts";

const skills = [
  {
    name: "with-tests",
    skillId: "$with-tests",
    displayName: "With Tests",
    summary: "A searchable summary.",
    description: "Runs for a matching trigger.",
    artifacts: { scripts: [], tests: [{ name: "test.py" }], references: [], assets: [] },
  },
  {
    name: "with-reference",
    skillId: "$with-reference",
    displayName: "With Reference",
    summary: "Another capability.",
    description: "Runs elsewhere.",
    artifacts: { scripts: [], tests: [], references: [{ name: "guide.md" }], assets: [] },
  },
];

test("query state round-trips through a shareable URL", () => {
  const state = {
    section: "skills",
    query: "matching trigger",
    filter: "tests",
    view: "list",
    item: "skill:with-tests",
  };
  assert.deepEqual(parseConsoleState(buildConsoleSearch(state)), state);
});

test("invalid query state falls back to safe defaults", () => {
  assert.deepEqual(parseConsoleState("?section=admin&filter=broken&view=table"), {
    section: "overview",
    query: "",
    filter: "all",
    view: "grid",
    item: "",
  });
});

test("search and artifact filters are combined", () => {
  assert.deepEqual(filterSkills(skills, "matching trigger", "tests").map((skill) => skill.name), ["with-tests"]);
  assert.deepEqual(filterSkills(skills, "", "references").map((skill) => skill.name), ["with-reference"]);
});

test("generated public data contains no personal absolute paths", async () => {
  const catalog = await readFile(new URL("../.generated/catalog.json", import.meta.url), "utf8");
  assert.doesNotMatch(catalog, /\/(?:Users|home|private|Volumes)\//);
  const snapshot = JSON.parse(catalog);
  for (const workflow of snapshot.workflows) {
    assert.deepEqual(Object.keys(workflow).sort(), ["dependencies", "displayName", "kind", "latestChange", "name", "summary"]);
  }
});
