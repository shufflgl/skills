"use client";

import { useEffect, useMemo, useState } from "react";
import snapshotData from "../.generated/catalog.json";
import {
  buildConsoleSearch,
  defaultConsoleState,
  filterSkills,
  parseConsoleState,
  type ArtifactKind,
  type CatalogFilter,
  type CatalogSnapshot,
  type CatalogView,
  type ConsoleSection,
  type SkillRecord,
} from "./catalog";

const snapshot = snapshotData as CatalogSnapshot;
const artifactKinds: ArtifactKind[] = ["scripts", "tests", "references", "assets"];
const filters: Array<{ value: CatalogFilter; label: string }> = [
  { value: "all", label: "All skills" },
  { value: "pinned", label: "Pinned" },
  { value: "scripts", label: "Has scripts" },
  { value: "tests", label: "Has tests" },
  { value: "references", label: "Has references" },
  { value: "assets", label: "Has assets" },
];

function formatDate(value: string | undefined): string {
  if (!value) return "Uncommitted";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}

function colorForName(name: string): string {
  const palette = ["#ef765b", "#7568d8", "#3f9d82", "#d8a53d", "#d95777", "#397aa8", "#775c45"];
  const value = [...name].reduce((total, character) => total + character.charCodeAt(0), 0);
  return palette[value % palette.length];
}

function markForName(name: string): string {
  return name
    .split("-")
    .filter((part) => !["to", "and", "the"].includes(part))
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function ArtifactCount({ skill, kind }: { skill: SkillRecord; kind: ArtifactKind }) {
  return (
    <span className={skill.artifacts[kind].length ? "artifact-count present" : "artifact-count"}>
      {kind.slice(0, 1).toUpperCase()} {skill.artifacts[kind].length}
    </span>
  );
}

export default function Home() {
  const [section, setSection] = useState<ConsoleSection>(defaultConsoleState.section);
  const [query, setQuery] = useState(defaultConsoleState.query);
  const [filter, setFilter] = useState<CatalogFilter>(defaultConsoleState.filter);
  const [view, setView] = useState<CatalogView>(defaultConsoleState.view);
  const [selectedName, setSelectedName] = useState(snapshot.skills[0]?.name ?? "");
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const [copied, setCopied] = useState(false);
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [pinned, setPinned] = useState<string[]>([]);
  const [urlReady, setUrlReady] = useState(false);

  useEffect(() => {
    const initial = parseConsoleState(window.location.search);
    /* URL restoration is an external browser-state synchronization. */
    /* eslint-disable react-hooks/set-state-in-effect */
    setSection(initial.section);
    setQuery(initial.query);
    setFilter(initial.filter);
    setView(initial.view);
    try {
      const stored = window.localStorage.getItem("skillroom:pinned");
      if (stored) setPinned(JSON.parse(stored));
    } catch {
      // Ignore unavailable or malformed browser storage.
    }
    if (initial.item.startsWith("skill:")) {
      const name = initial.item.slice("skill:".length);
      if (snapshot.skills.some((skill) => skill.name === name)) setSelectedName(name);
    }
    setUrlReady(true);
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  useEffect(() => {
    if (!urlReady) return;
    try {
      window.localStorage.setItem("skillroom:pinned", JSON.stringify(pinned));
    } catch {
      // Pinning is an enhancement; the catalog remains usable without storage.
    }
  }, [pinned, urlReady]);

  useEffect(() => {
    if (!urlReady) return;
    const search = buildConsoleSearch({
      section,
      query,
      filter,
      view,
      item: selectedName ? `skill:${selectedName}` : "",
    });
    window.history.replaceState(null, "", `${window.location.pathname}${search}`);
  }, [filter, query, section, selectedName, urlReady, view]);

  const filteredSkills = useMemo(
    () => filterSkills(snapshot.skills, query, filter, pinned),
    [filter, pinned, query],
  );
  const selected = snapshot.skills.find((skill) => skill.name === selectedName) ?? snapshot.skills[0];
  const passingChecks = snapshot.checks.filter((check) => check.status === "pass").length;
  const failingChecks = snapshot.checks.filter((check) => check.status === "fail");
  const testedSkills = snapshot.skills.filter((skill) => skill.artifacts.tests.length > 0).length;
  const referencedSkills = snapshot.skills.filter((skill) => skill.artifacts.references.length > 0).length;

  function selectSkill(skill: SkillRecord) {
    setSelectedName(skill.name);
    setInspectorOpen(true);
    setCopied(false);
    setCopiedPrompt(false);
  }

  async function copyText(value: string, onCopied: (value: boolean) => void) {
    try {
      await navigator.clipboard.writeText(value);
      onCopied(true);
      window.setTimeout(() => onCopied(false), 1600);
    } catch {
      onCopied(false);
    }
  }

  function togglePinned() {
    if (!selected) return;
    setPinned((items) =>
      items.includes(selected.name)
        ? items.filter((item) => item !== selected.name)
        : [...items, selected.name],
    );
  }

  function invocationFor(skill: SkillRecord): string {
    return `Use ${skill.skillId} for this task. Follow its full safety and completion contract.`;
  }

  const catalog = (
    <section className="market-panel" aria-labelledby="catalog-title">
      <div className="panel-heading">
        <div>
          <h2 id="catalog-title">Skill catalog</h2>
          <span>{filteredSkills.length} of {snapshot.skills.length}</span>
        </div>
        <div className="view-toggle" aria-label="Catalog view">
          <button className={view === "grid" ? "active" : ""} onClick={() => setView("grid")} aria-label="Grid view" aria-pressed={view === "grid"}>Grid</button>
          <button className={view === "list" ? "active" : ""} onClick={() => setView("list")} aria-label="List view" aria-pressed={view === "list"}>List</button>
        </div>
      </div>

      <div className="toolbar">
        <label className="search">
          <span>Search</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Name, ID, summary, or trigger…" />
        </label>
        <div className="filters" aria-label="Artifact filters">
          {filters.map((item) => (
            <button key={item.value} className={filter === item.value ? "active" : ""} onClick={() => setFilter(item.value)} aria-pressed={filter === item.value}>
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className={`skill-grid ${view}`}>
        {filteredSkills.map((skill) => (
          <a
            className={`skill-card ${selected?.name === skill.name ? "selected" : ""}`}
            key={skill.name}
            href={buildConsoleSearch({ section, query, filter, view, item: `skill:${skill.name}` })}
            onClick={(event) => {
              event.preventDefault();
              selectSkill(skill);
            }}
            aria-label={`Inspect ${skill.displayName}`}
          >
            <div className="card-top">
              <span className="skill-mark" style={{ background: colorForName(skill.name) }}>{markForName(skill.name)}</span>
              <span className="status cataloged">Cataloged</span>
            </div>
            <div className="skill-title">
              <h3>{skill.displayName}</h3>
              <span aria-hidden="true">↗</span>
            </div>
            <code>{skill.skillId}</code>
            <p>{skill.summary}</p>
            <div className="artifact-strip" aria-label="Artifact inventory">
              {artifactKinds.map((kind) => <ArtifactCount key={kind} skill={skill} kind={kind} />)}
            </div>
            <div className="card-footer">
              <span>{skill.files.length} repository files</span>
              <span>{formatDate(skill.latestChange?.date)}</span>
            </div>
          </a>
        ))}
      </div>
      {filteredSkills.length === 0 && (
        <div className="empty"><strong>No matching skills.</strong><span>Clear the search or choose another artifact filter.</span></div>
      )}
    </section>
  );

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => setSection("overview")} aria-label="Open overview">
          <span className="brand-mark">S</span>
          <span>Skillroom</span>
        </button>

        <nav aria-label="Main navigation">
          <p className="nav-label">Repository</p>
          {([
            ["overview", "OV", "Overview", snapshot.skills.length + snapshot.workflows.length],
            ["skills", "SK", "Skills", snapshot.skills.length],
            ["workflows", "WF", "Workflows", snapshot.workflows.length],
            ["quality", "QA", "Quality", failingChecks.length],
          ] as Array<[ConsoleSection, string, string, number]>).map(([value, mark, label, count]) => (
            <button key={value} className={`nav-item ${section === value ? "active" : ""}`} onClick={() => setSection(value)} aria-current={section === value ? "page" : undefined}>
              <span>{mark}</span>{label}<b className={value === "quality" && count > 0 ? "nav-alert" : ""}>{count}</b>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="repo-status">
            <span className={failingChecks.length ? "repo-dot warning" : "repo-dot"} />
            <div><strong>{snapshot.repository.name}</strong><small>{snapshot.repository.branch} · {snapshot.repository.commit}</small></div>
          </div>
          <a href={snapshot.repository.url} target="_blank" rel="noreferrer" aria-label="Open repository">↗</a>
        </div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">REPOSITORY CONSOLE</p>
            <h1>{section === "overview" ? "Make every skill visible." : section === "skills" ? "Explore the skill catalog." : section === "workflows" ? "See how skills work together." : "Trust what the repository proves."}</h1>
          </div>
          <a className="repository-link" href={snapshot.repository.url} target="_blank" rel="noreferrer">Open GitHub <span>↗</span></a>
        </header>

        {section === "overview" && (
          <>
            <section className="metrics" aria-label="Repository overview">
              <article className="metric-card hero-metric">
                <span className="metric-label">Distributable skills</span>
                <strong>{snapshot.skills.length}</strong>
                <p>Generated from root-level <code>SKILL.md</code> files</p>
              </article>
              <article className="metric-card">
                <span className="metric-label">Safe workflows</span>
                <strong className="plain-metric">{snapshot.workflows.length}</strong>
                <p>Public dependency metadata only</p>
              </article>
              <article className={`metric-card validation ${failingChecks.length ? "has-failures" : ""}`}>
                <span className="metric-label">Required checks</span>
                <strong className="plain-metric">{passingChecks}/{snapshot.checks.length}</strong>
                <p>{failingChecks.length ? `${failingChecks.length} check needs attention` : "Catalog and contracts are synchronized"}</p>
                <button onClick={() => setSection("quality")}>Open quality console <span>→</span></button>
              </article>
              <article className="metric-card coverage">
                <span className="metric-label">Artifact coverage</span>
                <div className="coverage-row"><span>Tests present</span><b>{testedSkills} / {snapshot.skills.length}</b></div>
                <div className="track"><i style={{ width: `${(testedSkills / snapshot.skills.length) * 100}%` }} /></div>
                <div className="coverage-row"><span>References present</span><b>{referencedSkills} / {snapshot.skills.length}</b></div>
                <div className="track"><i style={{ width: `${(referencedSkills / snapshot.skills.length) * 100}%` }} /></div>
              </article>
            </section>
            <section className="start-panel" aria-labelledby="start-title">
              <div className="start-copy">
                <p className="eyebrow">FROM CATALOG TO ACTION</p>
                <h2 id="start-title">Use a skill in three steps.</h2>
                <p>These skills are instructions for an agent, not buttons in this website. Pick a capability, copy its identifier, and give the task to Codex or Claude with the repository context available.</p>
              </div>
              <div className="start-steps">
                <div><b>01</b><strong>Pick a capability</strong><span>Search by outcome, trigger, or artifact.</span></div>
                <div><b>02</b><strong>Copy the Skill ID</strong><span>Use the exact <code>$skill-name</code> identifier.</span></div>
                <div><b>03</b><strong>Run it in your agent</strong><span>The agent follows the source contract and reports blockers.</span></div>
              </div>
            </section>
            {catalog}
            <section className="recent-panel" aria-labelledby="recent-title">
              <div className="panel-heading"><div><h2 id="recent-title">Recent repository changes</h2><span>Latest commits</span></div></div>
              <div className="change-list">
                {snapshot.recentChanges.map((change) => (
                  <a key={change.commit} href={`${snapshot.repository.url}/commit/${change.commit}`} target="_blank" rel="noreferrer">
                    <code>{change.commit}</code><span>{change.subject}</span><time>{formatDate(change.date)}</time>
                  </a>
                ))}
              </div>
            </section>
          </>
        )}

        {section === "skills" && catalog}

        {section === "workflows" && (
          <section className="workflow-panel" aria-labelledby="workflow-title">
            <div className="section-intro">
              <p className="eyebrow">SANITIZED PUBLIC VIEW</p>
              <h2 id="workflow-title">Workflow dependencies</h2>
              <p>Only names, summaries, and dependency contracts are published. Personal defaults and machine-specific instructions stay outside this snapshot.</p>
            </div>
            <div className="workflow-grid">
              {snapshot.workflows.map((workflow) => (
                <article className="workflow-card" key={workflow.name}>
                  <div className="workflow-heading"><span className="workflow-mark">WF</span><span className="safe-badge">Safe overview</span></div>
                  <h3>{workflow.displayName}</h3>
                  <code>{workflow.name}</code>
                  <p>{workflow.summary}</p>
                  <div className="dependency-list">
                    <div className="section-label"><span>Dependencies</span><b>{workflow.dependencies.length}</b></div>
                    {workflow.dependencies.map((dependency) => {
                      const repositorySkill = snapshot.skills.find((skill) => skill.skillId === dependency.skill);
                      return (
                        <div className="dependency" key={dependency.skill}>
                          <div>
                            {repositorySkill ? <button onClick={() => { selectSkill(repositorySkill); setSection("skills"); }}>{dependency.skill}</button> : <code>{dependency.skill}</code>}
                            <span className={`requirement ${dependency.requirement}`}>{dependency.requirement}</span>
                          </div>
                          <p>{dependency.purpose}</p>
                          <small>{dependency.source}</small>
                        </div>
                      );
                    })}
                  </div>
                  <p className="workflow-date">Last changed · {formatDate(workflow.latestChange?.date)}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {section === "quality" && (
          <section className="quality-panel" aria-labelledby="quality-title">
            <div className="section-intro">
              <p className="eyebrow">DETERMINISTIC EVIDENCE</p>
              <h2 id="quality-title">Repository quality</h2>
              <p>These results come from repository commands executed when this static snapshot was generated. Missing optional artifacts remain inventory facts, not failures.</p>
            </div>
            <div className="check-grid">
              {snapshot.checks.map((check) => (
                <article className={`check-card ${check.status}`} key={check.id}>
                  <div><span className="check-icon">{check.status === "pass" ? "PASS" : "FAIL"}</span><strong>{check.label}</strong></div>
                  <p>{check.status === "pass" ? check.message : "The repository command returned a failure."}</p>
                  {check.details && <div className="test-stats"><span><b>{check.details.total}</b>Total</span><span><b>{check.details.passed}</b>Passed</span><span><b>{check.details.skipped}</b>Skipped</span><span><b>{check.details.suites}</b>Suites</span></div>}
                  <code>{check.command}</code>
                  {check.status === "fail" && <details><summary>View failure output</summary><pre>{check.message}</pre></details>}
                </article>
              ))}
            </div>
            <div className="inventory-table-wrap">
              <div className="panel-heading"><div><h2>Artifact inventory</h2><span>Presence is informational</span></div></div>
              <table className="inventory-table">
                <thead><tr><th>Skill</th>{artifactKinds.map((kind) => <th key={kind}>{kind}</th>)}<th>Files</th></tr></thead>
                <tbody>
                  {snapshot.skills.map((skill) => (
                    <tr key={skill.name}><th><button onClick={() => { selectSkill(skill); setSection("skills"); }}>{skill.displayName}</button><code>{skill.skillId}</code></th>{artifactKinds.map((kind) => <td key={kind}>{skill.artifacts[kind].length}</td>)}<td>{skill.files.length}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <footer className="site-footer">
          <span>Generated {formatDate(snapshot.generatedAt)}</span>
          <span>Revision {snapshot.repository.commit}</span>
          <span>Schema v{snapshot.schemaVersion}</span>
        </footer>
      </section>

      {selected && inspectorOpen && (
        <aside className="inspector" aria-label="Skill details">
          <div className="inspector-head"><span>Skill details</span><button aria-label="Close details" onClick={() => { setInspectorOpen(false); setSelectedName(""); }}>×</button></div>
          <div className="selected-identity">
            <span className="skill-mark large" style={{ background: colorForName(selected.name) }}>{markForName(selected.name)}</span>
            <div><h2>{selected.displayName}</h2><code>{selected.skillId}</code></div>
          </div>
          <button className={`pin-action ${pinned.includes(selected.name) ? "pinned" : ""}`} onClick={togglePinned}>
            <span>{pinned.includes(selected.name) ? "★" : "☆"}</span>
            {pinned.includes(selected.name) ? "Pinned for this browser" : "Pin for later"}
          </button>
          <div className="truth-block">
            <div><span>Catalog state</span><strong>Validated</strong></div>
            <p>Metadata and catalog summary are synchronized in this snapshot.</p>
          </div>
          <div className="detail-grid">
            {artifactKinds.map((kind) => <div key={kind}><span>{kind}</span><strong>{selected.artifacts[kind].length}</strong></div>)}
          </div>
          <div className="summary-block"><span>Catalog summary</span><p>{selected.summary}</p></div>
          <div className="use-block">
            <div className="section-label"><span>Start a request</span><b>Agent handoff</b></div>
            <code>{invocationFor(selected)}</code>
            <button className="primary-action" onClick={() => copyText(invocationFor(selected), setCopiedPrompt)}>
              {copiedPrompt ? "Copied starter request" : "Copy starter request"}
            </button>
          </div>
          <details className="trigger-block"><summary>When it should run</summary><p>{selected.description}</p></details>
          <div className="source-list">
            <div className="section-label"><span>Repository contents</span><b>{selected.files.length}</b></div>
            {selected.files.slice(0, 8).map((file) => <a key={file.path} href={file.url} target="_blank" rel="noreferrer"><span>{file.name}</span><small>{file.path}</small></a>)}
            {selected.files.length > 8 && <p>+ {selected.files.length - 8} more files in the repository</p>}
          </div>
          <button className="secondary-action" onClick={() => copyText(selected.skillId, setCopied)}>{copied ? "Copied skill ID" : "Copy skill ID"}</button>
          <div className="action-grid">
            <a href={selected.sourceUrl} target="_blank" rel="noreferrer">View SKILL.md</a>
            <a href={selected.editUrl} target="_blank" rel="noreferrer">Edit on GitHub</a>
          </div>
          <a className="issue-action" href={selected.issueUrl} target="_blank" rel="noreferrer">Report an issue <span>↗</span></a>
          <p className="sync-note">{selected.latestChange ? `${selected.latestChange.commit} · ${formatDate(selected.latestChange.date)}` : "Not present in the current Git history"}</p>
        </aside>
      )}
    </main>
  );
}
