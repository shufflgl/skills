import { cp, mkdir, rm, writeFile } from "node:fs/promises";

const outputUrl = new URL("../pages-dist/", import.meta.url);
const clientUrl = new URL("../dist/client/", import.meta.url);
const workerUrl = new URL("../dist/server/index.js", import.meta.url);

await rm(outputUrl, { recursive: true, force: true });
await mkdir(outputUrl, { recursive: true });
await cp(clientUrl, outputUrl, { recursive: true });

workerUrl.searchParams.set("export", `${Date.now()}`);
const { default: worker } = await import(workerUrl.href);
const response = await worker.fetch(
  new Request("https://skills.lglgl.me/", {
    headers: { accept: "text/html" },
  }),
  {
    ASSETS: {
      fetch: async () => new Response("Not found", { status: 404 }),
    },
  },
  {
    waitUntil() {},
    passThroughOnException() {},
  },
);

if (!response.ok) {
  throw new Error(`Static export failed with status ${response.status}.`);
}

const html = await response.text();
await Promise.all([
  writeFile(new URL("index.html", outputUrl), html),
  writeFile(new URL("404.html", outputUrl), html),
]);

console.log("Cloudflare Pages output is ready in pages-dist/.");
