/** A SpoolHQ project: its spec, settings and repository. */
export {
  COALESCE_MS,
  useProjectEvents,
  type EventSource,
} from "./model/events";
export {
  useProject,
  useProjects,
  type ProjectDetail,
  type ProjectSummary,
} from "./model/queries";
export {
  loadSpec,
  saveSpec,
  SPEC_FILE,
  useSpec,
  type SpecFile,
} from "./model/spec";
export { ProjectStatus } from "./ui/ProjectStatus";
