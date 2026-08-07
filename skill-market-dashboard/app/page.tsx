"use client";

import { useEffect, useMemo, useState } from "react";
import { Copy, Download } from "lucide-react";
import { FaGithub } from "react-icons/fa6";
import snapshotData from "../.generated/catalog.json";
import {
  filterCatalog,
  type CatalogCategory,
  type CatalogItem,
  type CatalogSnapshot,
  type CatalogTab,
} from "./catalog";

const snapshot = snapshotData as CatalogSnapshot;
const items: CatalogItem[] = [...snapshot.skills, ...snapshot.workflows];

function categoriesForTab(tab: CatalogTab): CatalogCategory[] {
  return Array.from(
    new Set(
      items
        .filter(
          (item) =>
            tab === "All" ||
            (tab === "Skills" && item.kind === "skill") ||
            (tab === "Workflows" && item.kind === "workflow"),
        )
        .map((item) => item.category),
    ),
  ).sort();
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<CatalogTab>("All");
  const [category, setCategory] = useState<CatalogCategory | "All">("All");
  const [installItem, setInstallItem] = useState<CatalogItem | null>(null);
  const [copied, setCopied] = useState(false);
  const [urlReady, setUrlReady] = useState(false);

  const categories = useMemo(
    () => categoriesForTab(tab),
    [tab],
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const requestedCategory = params.get("category");
    const requestedTab = params.get("tab");
    const initialTab =
      requestedTab === "Skills" || requestedTab === "Workflows"
        ? requestedTab
        : "All";
    /* URL restoration is an external browser-state synchronization. */
    /* eslint-disable react-hooks/set-state-in-effect */
    setQuery(params.get("q") ?? "");
    setTab(initialTab);
    if (
      requestedCategory &&
      categoriesForTab(initialTab).includes(requestedCategory as CatalogCategory)
    ) {
      setCategory(requestedCategory as CatalogCategory);
    }
    setUrlReady(true);
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  useEffect(() => {
    if (!urlReady) return;
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (tab !== "All") params.set("tab", tab);
    if (category !== "All") params.set("category", category);
    const search = params.toString();
    window.history.replaceState(null, "", search ? `?${search}` : window.location.pathname);
  }, [category, query, tab, urlReady]);

  useEffect(() => {
    if (!installItem) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setInstallItem(null);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [installItem]);

  const visibleItems = useMemo(
    () => filterCatalog(items, query, category, tab),
    [category, query, tab],
  );

  function selectTab(nextTab: CatalogTab) {
    setTab(nextTab);
    if (
      category !== "All" &&
      !categoriesForTab(nextTab).includes(category)
    ) {
      setCategory("All");
    }
  }

  function installPrompt(item: CatalogItem): string {
    const itemType = item.kind === "skill" ? "Skill" : "workflow";
    const sourceDirectory =
      item.kind === "skill"
        ? item.name
        : `workflows/${item.name}`;
    const sourceUrl = `${snapshot.repository.url}/tree/${snapshot.repository.branch}/${sourceDirectory}`;

    return `Install this ${itemType} from the shufflgl/skills repository.

Name: ${item.displayName}
Source: ${sourceUrl}

Install it using the standard installation method for the current AI client. Confirm that it is available after installation.`;
  }

  async function copyInstallPrompt() {
    if (!installItem) return;
    try {
      await navigator.clipboard.writeText(installPrompt(installItem));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <main>
      <header className="site-header">
        <div className="brand">
          <span className="brand-logo" role="img" aria-label="Agora logo" />
          <span>SKILL Agora</span>
        </div>
        <a
          className="github-link"
          href={snapshot.repository.url}
          target="_blank"
          rel="noreferrer"
          aria-label="Open GitHub repository"
          title="Open GitHub repository"
        >
          <FaGithub size={18} aria-hidden="true" />
        </a>
      </header>

      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">SKILL CATALOG</p>
        <h1 id="page-title">Find the right skill or workflow.</h1>
        <p>Browse the reusable capabilities maintained in this repository.</p>
      </section>

      <section className="catalog" aria-labelledby="catalog-title">
        <div className="tabs" role="tablist" aria-label="Catalog type">
          {(["All", "Skills", "Workflows"] as CatalogTab[]).map((item) => (
            <button
              key={item}
              type="button"
              role="tab"
              aria-selected={tab === item}
              className={tab === item ? "active" : ""}
              onClick={() => selectTab(item)}
            >
              {item}
            </button>
          ))}
        </div>

        <div className="catalog-tools">
          <label className="search">
            <span className="sr-only">Search catalog</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search catalog"
            />
          </label>

          <div className="categories" aria-label="Catalog categories">
            {(["All", ...categories] as const).map((item) => (
              <button
                key={item}
                type="button"
                className={category === item ? "active" : ""}
                onClick={() => setCategory(item)}
                aria-pressed={category === item}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="catalog-heading">
          <h2 id="catalog-title">
            {category === "All" ? tab : `${category} ${tab.toLowerCase()}`}
          </h2>
          <span>{visibleItems.length}</span>
        </div>

        <div className="skill-grid">
          {visibleItems.map((item) => (
            <article className="skill-card" key={`${item.kind}:${item.name}`}>
              <div className="card-labels">
                <span className="item-kind">{item.kind}</span>
                <span className="skill-category">{item.category}</span>
              </div>
              <h3>{item.displayName}</h3>
              <p>{item.summary}</p>
              <button
                className="install-button"
                type="button"
                aria-label={`Install ${item.displayName}`}
                title="Install"
                onClick={() => {
                  setCopied(false);
                  setInstallItem(item);
                }}
              >
                <Download size={16} strokeWidth={1.8} aria-hidden="true" />
              </button>
            </article>
          ))}
        </div>

        {visibleItems.length === 0 && (
          <div className="empty">
            <strong>No matching items.</strong>
            <span>Try another search or category.</span>
          </div>
        )}
      </section>

      <footer>
        <span>{snapshot.skills.length} skills · {snapshot.workflows.length} workflows</span>
        <span>{snapshot.repository.name}</span>
      </footer>

      {installItem && (
        <div className="modal-backdrop" role="presentation">
          <section
            className="install-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="install-title"
          >
            <div className="modal-header">
              <div>
                <p className="eyebrow">INSTALL PROMPT</p>
                <h2 id="install-title">{installItem.displayName}</h2>
              </div>
              <button
                className="close-button"
                type="button"
                aria-label="Close install prompt"
                onClick={() => setInstallItem(null)}
              >
                ×
              </button>
            </div>
            <p className="modal-intro">
              Copy this prompt and give it to your AI coding assistant. It explains
              how to install only this item without copying the whole repository.
            </p>
            <textarea
              className="install-prompt"
              readOnly
              value={installPrompt(installItem)}
              aria-label={`Install prompt for ${installItem.displayName}`}
            />
            <button className="copy-button" type="button" onClick={copyInstallPrompt}>
              <Copy size={15} strokeWidth={1.9} aria-hidden="true" />
              {copied ? "Copied" : "Copy prompt"}
            </button>
          </section>
        </div>
      )}
    </main>
  );
}
