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
  assert.match(html, /Skillroom/);
  assert.match(html, /Skill catalog/);
  assert.match(html, /download-bilibili-audio/);
  assert.match(html, /Check EPUB Quality/);
  assert.match(html, /Required checks/);
  assert.match(html, /Repository Console/);
  assert.doesNotMatch(html, /Market readiness|Health score|Published|Review queue/);
  assert.doesNotMatch(html, /codex-preview|SkeletonPreview|Your site is taking shape/);
});
