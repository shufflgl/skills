"use client";

import { useEffect, useMemo, useState } from "react";
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

  return (
    <main>
      <header className="site-header">
        <div className="brand">
          <span className="brand-mark">S</span>
          <span>Skillroom</span>
        </div>
        <p>A small catalog of reusable agent skills.</p>
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
    </main>
  );
}
