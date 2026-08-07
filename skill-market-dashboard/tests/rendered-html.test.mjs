import assert from "node:assert/strict";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(new Request("http://localhost/", { headers: { accept: "text/html" } }), {
    ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) },
  }, { waitUntil() {}, passThroughOnException() {} });
}

test("server-renders the repository-backed skill catalog", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /SKILL Agora/);
  assert.match(html, /SKILL CATALOG/);
  assert.match(html, /Download Bilibili Audio/);
  assert.match(html, /Check EPUB Quality/);
  assert.match(html, /Find the right skill/);
  assert.match(html, /Search catalog/);
  assert.match(html, /Workflows/);
  assert.match(html, /Download Bilibili Audio to Apple Music/);
  assert.match(html, /Install/);
  assert.match(html, /https:\/\/github.com\/shufflgl\/skills/);
  assert.doesNotMatch(html, /Required checks|Repository Console|Workflow dependencies|Artifact inventory/);
  assert.doesNotMatch(html, /codex-preview|SkeletonPreview|Your site is taking shape/);
});
