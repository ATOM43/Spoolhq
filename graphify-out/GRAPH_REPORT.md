# Graph Report - Spoolhq  (2026-10-18)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1865 nodes · 4947 edges · 94 communities (72 shown, 22 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 419 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b65f274b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 92
- Community 93

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 94 edges
2. `WorktreeManager` - 73 edges
3. `Ticket` - 40 edges
4. `GitError` - 38 edges
5. `run_git()` - 37 edges
6. `EventBus` - 34 edges
7. `list_tickets()` - 32 edges
8. `make()` - 31 edges
9. `load_settings()` - 31 edges
10. `load_project()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/test_git_daemon.py → daemon/src/spoolhq/services/git/runner.py
- `test_error_without_stderr_has_no_colon()` --uses--> `GitResult`  [INFERRED]
  daemon/tests/test_git_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_git_error_keeps_the_last_20_stderr_lines()` --uses--> `GitResult`  [INFERRED]
  daemon/tests/test_git_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_dashboard_plan_loads()` --calls--> `list_tickets()`  [INFERRED]
  daemon/tests/test_tickets.py → daemon/src/spoolhq/services/tickets/store.py
- `test_unknown_status_filter()` --calls--> `list_tickets()`  [INFERRED]
  daemon/tests/test_tickets.py → daemon/src/spoolhq/services/tickets/store.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (94 total, 22 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (27): fail(), settings(), table(), check_command(), _hours(), _invalid_lines(), _listing(), next_command() (+19 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (43): copy_dashboard(), make_project(), set_status(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files(), test_check_valid_plan(), test_next_on_the_dashboard() (+35 more)

### Community 2 - "Community 2"
Cohesion: 0.14
Nodes (35): git_executable(), WorktreeManager, branches(), make_read_only(), marker(), real(), registered_paths(), sha() (+27 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (37): RunLog, raw(), run_log(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_closed_log_refuses_calls(), test_committed_events_are_published_in_order() (+29 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (17): acquire_daemon_lock(), DaemonAlreadyRunning, DaemonLock, lock_path(), _read_pid(), _try_lock(), _unlock(), _clear_read_only_and_retry() (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (13): utc_now(), encode_payload(), _event_kind(), fetch_run(), _to_run(), Transaction, AttemptKind, AttemptStatus (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (12): run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError, find_ticket_file(), _id_sort_key(), list_tickets() (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (18): _block_indent(), _dumper(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _loader(), _node() (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (5): attempt_dir_name(), _check_count(), check_ticket_id(), Attempt, Run

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (31): PlanProblem, validate_plan(), explain_idle(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once(), test_critical_path_skips_done_tickets() (+23 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (25): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+17 more)

### Community 12 - "Community 12"
Cohesion: 0.21
Nodes (30): load_project(), del_path(), errors_for(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml(), test_bad_slug_is_refused(), test_empty_or_non_mapping_file() (+22 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (17): append_transcript(), _artifact_name(), ArtifactName, attempt_dir(), attempt_files(), write_artifact(), attempt(), run_log() (+9 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (28): load_ticket(), save_ticket(), make_project(), replace_line(), test_assignment_is_validated(), test_body_is_written_verbatim(), test_broken_file_does_not_stop_the_others(), test_double_quoted_escapes_do_not_hide_the_comment() (+20 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (28): errors_for(), round_trip_tickets(), save_and_read(), test_bad_file_name(), test_bad_project_name(), test_block_list_keeps_its_layout(), test_changing_status_changes_only_that_line(), test_crlf_frontmatter_errors_count_lines() (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (23): ensure_clean(), status_entries(), run_git(), start_conflicting_merge(), test_branch_name_refuses_bad_ticket_ids(), test_default_branch_sha(), test_dirty_message_lists_20_entries(), test_dirty_repo_lists_tracked_and_untracked_changes() (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.10
Nodes (8): marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, same_path(), Worktree, test_parse_worktree_list(), test_session_keep_leaves_the_worktree()

### Community 18 - "Community 18"
Cohesion: 0.09
Nodes (3): Subscription, _to_event(), Event

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (16): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+8 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (12): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_db_path(), state_dir(), _statements() (+4 more)

### Community 23 - "Community 23"
Cohesion: 0.21
Nodes (18): HomePage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Card(), CardAction(), CardContent(), CardDescription() (+10 more)

### Community 24 - "Community 24"
Cohesion: 0.16
Nodes (20): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getDaemonInfo(), getHealth(), getVersion() (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.19
Nodes (10): DaemonNotRunning, _serve(), load_or_create_token(), read_token(), token_path(), ensure_home(), test_empty_token_file_is_replaced(), test_loose_token_file_mode_is_tightened() (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (8): parse_done_when(), check_ticket_id(), DoneItem, TicketMeta, test_done_when_heading_variants(), test_done_when_ignores_code_fences(), test_done_when_items(), test_empty_done_when_is_a_warning()

### Community 27 - "Community 27"
Cohesion: 0.14
Nodes (7): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (10): dotted_path(), ProjectError, ProjectValidationError, Project, _initial_yaml(), InitResult, list_workspaces(), _populate() (+2 more)

### Community 30 - "Community 30"
Cohesion: 0.15
Nodes (13): client(), clock(), commit_file(), free_port(), git_repo(), home(), isolated_git(), manager() (+5 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (24): description, engines, node, license, name, packageManager, private, type (+16 more)

### Community 32 - "Community 32"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (12): branch_exists(), branch_sha(), default_branch_sha(), DirtyRepoError, ensure_no_operation_in_progress(), is_work_tree(), MissingBranchError, operation_in_progress() (+4 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (13): AppRouter(), router, RootLayout(), routes, invokeMock, describe(), StatusPill(), TopBar() (+5 more)

### Community 35 - "Community 35"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 36 - "Community 36"
Cohesion: 0.14
Nodes (6): config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings

### Community 37 - "Community 37"
Cohesion: 0.13
Nodes (8): dump(), merge(), parse(), read(), to_node(), to_plain(), write_atomic(), _yaml()

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (8): branch_name(), check_ticket_id(), slugify(), BranchConflictError, _ticket_order(), WorktreeExistsError, test_quotes_and_semicolons_make_a_valid_branch(), test_slugify()

### Community 39 - "Community 39"
Cohesion: 0.21
Nodes (14): SettingsDialog(), ProjectPanelPage(), Button(), buttonVariants, CopyState, EmptyState(), Tabs(), TabsContent() (+6 more)

### Community 40 - "Community 40"
Cohesion: 0.17
Nodes (11): critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours(), summary(), _work_order() (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.13
Nodes (7): ApiClient, ApiError, test_client_connection_refused(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 42 - "Community 42"
Cohesion: 0.11
Nodes (3): keep_for(), recover_all_worktrees(), RunRegistry

### Community 43 - "Community 43"
Cohesion: 0.15
Nodes (14): check_git_version(), GitError, parse_git_version(), IdentityError, fake_version(), test_branch_name_raises_if_git_refuses_it(), test_missing_git_is_reported(), test_non_empty_hooks_dir_stops_git_from_starting() (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.14
Nodes (5): create_app(), lifespan(), health(), Health, check_git()

### Community 45 - "Community 45"
Cohesion: 0.15
Nodes (9): Agents, Budget, check_slug(), Commands, GitSettings, Limits, MergePolicy, _Strict (+1 more)

### Community 46 - "Community 46"
Cohesion: 0.22
Nodes (11): FixedClock, seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts() (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 48 - "Community 48"
Cohesion: 0.17
Nodes (9): command_error(), disabled_hooks_dir(), git_env(), GitResult, hook_and_signing_options(), neutral_cwd(), run_git(), subcommand() (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.24
Nodes (8): require_valid(), sort_tickets(), _ids(), next_ready(), _statuses(), _unmet(), waiting_on(), Ticket

### Community 50 - "Community 50"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 51 - "Community 51"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 52 - "Community 52"
Cohesion: 0.27
Nodes (10): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+2 more)

### Community 54 - "Community 54"
Cohesion: 0.17
Nodes (4): init(), serve(), validate_project(), version()

### Community 55 - "Community 55"
Cohesion: 0.20
Nodes (10): check_transition(), parse_status(), test_allowed_transitions_pass(), test_disallowed_transition_messages(), test_disallowed_transitions_raise(), test_running_from_blocked_also_waits_for_dependencies(), test_running_needs_a_valid_plan(), test_running_waits_for_every_dependency() (+2 more)

### Community 56 - "Community 56"
Cohesion: 0.27
Nodes (9): run_git(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+1 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 58 - "Community 58"
Cohesion: 0.30
Nodes (8): apply_transition(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 59 - "Community 59"
Cohesion: 0.27
Nodes (9): test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401() (+1 more)

### Community 60 - "Community 60"
Cohesion: 0.27
Nodes (7): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 62 - "Community 62"
Cohesion: 0.22
Nodes (8): init_project(), _fail_after_yaml(), test_failed_rename_leaves_nothing(), test_failure_mid_init_leaves_nothing(), test_init_finds_repo_notes(), test_init_never_modifies_the_repo(), test_init_refuses_existing_folder(), test_missing_git_is_reported()

### Community 63 - "Community 63"
Cohesion: 0.22
Nodes (5): remove_path(), test_list_shows_state(), test_list_worktrees_reports_each_state(), test_remove_path_handles_files_and_symlinks(), test_resume_needs_the_folder_and_the_marker()

### Community 64 - "Community 64"
Cohesion: 0.22
Nodes (3): WorktreeSession, test_session_teardown_failure_keeps_the_original_error(), test_session_tears_down_after_an_exception()

### Community 65 - "Community 65"
Cohesion: 0.24
Nodes (3): PlanError, SchedulerError, TransitionError

### Community 66 - "Community 66"
Cohesion: 0.25
Nodes (3): _message(), _model_at(), _number()

### Community 67 - "Community 67"
Cohesion: 0.31
Nodes (4): _and_list(), _find_cycles(), id_key(), sort_ids()

### Community 69 - "Community 69"
Cohesion: 0.22
Nodes (7): eslint, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals, typescript-eslint

### Community 70 - "Community 70"
Cohesion: 0.29
Nodes (5): root, queryClient, QueryProvider(), react-dom, @tanstack/react-query

### Community 72 - "Community 72"
Cohesion: 0.29
Nodes (4): format_errors(), parse_ticket(), test_defaults_for_optional_fields(), test_parse_ticket_parts()

### Community 73 - "Community 73"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 74 - "Community 74"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 75 - "Community 75"
Cohesion: 0.33
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

## Knowledge Gaps
- **19 isolated node(s):** `Config`, `InvalidRequest`, `NotRunning`, `TokenMissing`, `eslint-import-resolver-typescript` (+14 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 630 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 4` to `Community 0`, `Community 1`, `Community 5`, `Community 6`, `Community 9`, `Community 42`, `Community 13`, `Community 46`, `Community 18`, `Community 21`, `Community 22`, `Community 27`, `Community 60`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `RunLog` (e.g. with `EventBus` and `Attempt`) actually correct?**
  _`RunLog` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `InvalidRequest`, `NotRunning` to the rest of the system?**
  _19 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05506329113924051 - nodes in this community are weakly interconnected._
- **Why does `WorktreeManager` connect `Community 2` to `Community 0`, `Community 64`, `Community 38`, `Community 42`, `Community 43`, `Community 47`, `Community 48`, `Community 17`, `Community 56`, `Community 27`, `Community 60`, `Community 30`, `Community 63`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.07475678443420379 - nodes in this community are weakly interconnected._