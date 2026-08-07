export type CatalogCategory = "Books" | "Media" | "Repository" | "Workflow";
export type CatalogTab = "All" | "Skills" | "Workflows";

export type SkillRecord = {
  kind: "skill";
  name: string;
  displayName: string;
  summary: string;
  description: string;
  skillId: string;
  category: CatalogCategory;
};

export type WorkflowRecord = {
  kind: "workflow";
  name: string;
  displayName: string;
  summary: string;
  category: CatalogCategory;
};

export type CatalogItem = SkillRecord | WorkflowRecord;

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
};

export function filterCatalog(
  items: CatalogItem[],
  query: string,
  category: CatalogCategory | "All",
  tab: CatalogTab,
): CatalogItem[] {
  const needle = query.trim().toLowerCase();
  return items.filter((item) => {
    const tabMatches =
      tab === "All" ||
      (tab === "Skills" && item.kind === "skill") ||
      (tab === "Workflows" && item.kind === "workflow");
    const categoryMatches = category === "All" || item.category === category;
    const searchable = `${item.name} ${item.displayName} ${item.summary}${
      item.kind === "skill" ? ` ${item.skillId} ${item.description}` : ""
    }`.toLowerCase();
    return tabMatches && categoryMatches && (!needle || searchable.includes(needle));
  });
}
