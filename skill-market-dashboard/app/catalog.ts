export type ArtifactKind = "scripts" | "tests" | "references" | "assets";
export type ConsoleSection = "overview" | "skills" | "workflows" | "quality";
export type CatalogView = "grid" | "list";
export type CatalogFilter = "all" | ArtifactKind | "pinned";

export type SourceFile = {
  name: string;
  path: string;
  url: string;
};

export type GitChange = {
  commit: string;
  date: string;
  subject: string;
};

export type PublicGitChange = Omit<GitChange, "subject">;

export type SkillRecord = {
  kind: "skill";
  name: string;
  displayName: string;
  summary: string;
  description: string;
  skillId: string;
  path: string;
  sourceUrl: string;
  editUrl: string;
  issueUrl: string;
  artifacts: Record<ArtifactKind, SourceFile[]>;
  files: SourceFile[];
  latestChange: GitChange | null;
  checks: string[];
};

export type WorkflowDependency = {
  skill: string;
  source: string;
  requirement: "required" | "optional";
  purpose: string;
};

export type WorkflowRecord = {
  kind: "workflow";
  name: string;
  displayName: string;
  summary: string;
  dependencies: WorkflowDependency[];
  latestChange: PublicGitChange | null;
};

export type ValidationCheck = {
  id: string;
  label: string;
  status: "pass" | "fail";
  message: string;
  command: string;
  affectedItem: string | null;
  details?: {
    total: number;
    passed: number;
    skipped: number;
    suites: number;
  };
};

export type CatalogSnapshot = {
  schemaVersion: number;
  generatedAt: string;
  repository: {
    name: string;
    url: string;
    commit: string;
    branch: string;
  };
  skills: SkillRecord[];
  workflows: WorkflowRecord[];
  checks: ValidationCheck[];
  recentChanges: GitChange[];
};

export type ConsoleState = {
  section: ConsoleSection;
  query: string;
  filter: CatalogFilter;
  view: CatalogView;
  item: string;
};

const sections = new Set<ConsoleSection>(["overview", "skills", "workflows", "quality"]);
const filters = new Set<CatalogFilter>(["all", "scripts", "tests", "references", "assets", "pinned"]);
const views = new Set<CatalogView>(["grid", "list"]);

export const defaultConsoleState: ConsoleState = {
  section: "overview",
  query: "",
  filter: "all",
  view: "grid",
  item: "",
};

export function parseConsoleState(search: string): ConsoleState {
  const params = new URLSearchParams(search);
  const section = params.get("section") as ConsoleSection | null;
  const filter = params.get("filter") as CatalogFilter | null;
  const view = params.get("view") as CatalogView | null;
  return {
    section: section && sections.has(section) ? section : "overview",
    query: params.get("q") ?? "",
    filter: filter && filters.has(filter) ? filter : "all",
    view: view && views.has(view) ? view : "grid",
    item: params.get("item") ?? "",
  };
}

export function buildConsoleSearch(state: ConsoleState): string {
  const params = new URLSearchParams();
  if (state.section !== "overview") params.set("section", state.section);
  if (state.query) params.set("q", state.query);
  if (state.filter !== "all") params.set("filter", state.filter);
  if (state.view !== "grid") params.set("view", state.view);
  if (state.item) params.set("item", state.item);
  const value = params.toString();
  return value ? `?${value}` : "";
}

export function filterSkills(
  skills: SkillRecord[],
  query: string,
  filter: CatalogFilter,
  pinnedNames: string[] = [],
): SkillRecord[] {
  const needle = query.trim().toLowerCase();
  return skills.filter((skill) => {
    const artifactMatch =
      filter === "all" ||
      (filter === "pinned" ? pinnedNames.includes(skill.name) : skill.artifacts[filter].length > 0);
    const searchable = `${skill.name} ${skill.skillId} ${skill.displayName} ${skill.summary} ${skill.description}`.toLowerCase();
    return artifactMatch && (!needle || searchable.includes(needle));
  });
}
