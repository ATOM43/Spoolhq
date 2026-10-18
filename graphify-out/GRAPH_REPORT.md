# Graph Report - Spoolhq  (2026-10-18)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2444 nodes · 6528 edges · 114 communities (78 shown, 36 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 582 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `60d09e27`
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
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 112
- Community 113

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 94 edges
2. `WorktreeManager` - 72 edges
3. `ClaudeStreamParser` - 64 edges
4. `AgentPolicy` - 48 edges
5. `build_implementer_prompt()` - 46 edges
6. `Ticket` - 40 edges
7. `run_git()` - 38 edges
8. `fixture_inputs()` - 37 edges
9. `EventBus` - 34 edges
10. `list_tickets()` - 33 edges

## Surprising Connections (you probably didn't know these)
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/git/test_worktrees.py → daemon/src/spoolhq/services/git/runner.py
- `test_error_without_stderr_has_no_colon()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_git_error_keeps_the_last_20_stderr_lines()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (114 total, 36 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (18): attempt_dir_name(), _check_count(), check_ticket_id(), encode_payload(), _event_kind(), fetch_run(), _to_event(), _to_run() (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (49): build_argv(), child_env(), sandbox_settings(), AgentPolicy, assert_gone(), fake_probe(), parent_env(), read_record() (+41 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (29): branch_name(), slugify(), branch_exists(), branch_sha(), default_branch_sha(), DirtyRepoError, ensure_no_operation_in_progress(), is_work_tree() (+21 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (18): agents_command(), describe(), fail(), settings(), table(), _cost(), list_command(), _run_log() (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (57): load_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated(), test_bad_file_name() (+49 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (44): WorktreeManager, commit_file(), git_repo(), run_git(), branches(), make_read_only(), marker(), real() (+36 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (17): format_errors(), write_atomic(), run_editor(), start_edit(), TicketEdit, source_name(), TicketError, TicketValidationError (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (36): ClaudeStreamParser, assistant(), load(), parse(), replay(), result(), test_accepted_modes_can_be_widened_by_the_adapter(), test_acting_before_init_is_a_violation() (+28 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (40): RunLog, test_attempt_kind_is_validated(), raw(), run_log(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_closed_log_refuses_calls() (+32 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (40): _and_list(), validate_plan(), check_transition(), parse_status(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once() (+32 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (19): available_runners(), format_version(), parse_version(), PolicyViolation, BackendInfo, Budget, check_command(), FileEdit (+11 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (33): copy_dashboard(), make_project(), set_status(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files(), test_check_valid_plan(), test_next_on_the_dashboard() (+25 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (23): _find_cycles(), id_key(), require_valid(), sort_ids(), sort_tickets(), critical_path(), CriticalPath, _hours() (+15 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (10): check_ticket_id(), marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, remove_path(), same_path(), Worktree (+2 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (37): description, engines, node, license, name, packageManager, private, type (+29 more)

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (33): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text(), big_docs() (+25 more)

### Community 18 - "Community 18"
Cohesion: 0.09
Nodes (34): ensure_clean(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes(), test_default_branch_sha() (+26 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (17): cap_excerpt(), PromptTemplateError, ContextInputs, _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines() (+9 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (6): health(), version(), Health, Version, _is_api_path(), LocalOnlyMiddleware

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (18): _block_indent(), _dumper(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _loader(), _node() (+10 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (17): append_transcript(), _artifact_name(), ArtifactName, attempt_dir(), attempt_files(), write_artifact(), attempt(), run_log() (+9 more)

### Community 23 - "Community 23"
Cohesion: 0.21
Nodes (30): load_project(), del_path(), errors_for(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml(), test_bad_slug_is_refused(), test_empty_or_non_mapping_file() (+22 more)

### Community 24 - "Community 24"
Cohesion: 0.14
Nodes (24): editor_command(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores(), test_edit_invalid_restores_the_backup() (+16 more)

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (8): parse_done_when(), check_ticket_id(), DoneItem, TicketMeta, test_done_when_heading_variants(), test_done_when_ignores_code_fences(), test_done_when_items(), test_empty_done_when_is_a_warning()

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (14): state_db_path(), seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts() (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (9): billing_for(), check_worktree(), ClaudeCliRunner, existing_stubs(), expand_home(), _remove_empty_tree(), remove_new_stubs(), BackendUnavailableError (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (17): home_denials(), policy(), user_home(), worktree(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused() (+9 more)

### Community 29 - "Community 29"
Cohesion: 0.11
Nodes (15): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+7 more)

### Community 30 - "Community 30"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (9): acquire_daemon_lock(), DaemonAlreadyRunning, DaemonLock, lock_path(), _read_pid(), _try_lock(), _unlock(), _clear_read_only_and_retry() (+1 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (8): FakeRunner, test_cancel(), test_detect(), test_policy_violation(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file(), test_token_budget(), test_writes_outside_the_worktree_are_skipped()

### Community 33 - "Community 33"
Cohesion: 0.16
Nodes (19): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion(), Health (+11 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (10): _blocks(), epoch_to_datetime(), _int(), summarize(), _usage_counts(), usd_to_micro(), RateLimit, test_api_retry_on_rate_limit_is_reported() (+2 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (8): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, _ticket_order(), WorktreeInfo, WorktreeState

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (8): config_path(), ConfigError, default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings, disabled_hooks_dir()

### Community 37 - "Community 37"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.14
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 41 - "Community 41"
Cohesion: 0.13
Nodes (11): PlanProblem, SchedulerError, TransitionError, apply_transition(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid() (+3 more)

### Community 42 - "Community 42"
Cohesion: 0.19
Nodes (9): _serve(), load_or_create_token(), read_token(), token_path(), ensure_home(), test_empty_token_file_is_replaced(), test_loose_token_file_mode_is_tightened(), test_token_file_and_home_have_private_modes() (+1 more)

### Community 43 - "Community 43"
Cohesion: 0.15
Nodes (10): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_dir(), _statements(), _user_version() (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (12): Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate(), project_dir(), save_project() (+4 more)

### Community 45 - "Community 45"
Cohesion: 0.14
Nodes (8): ProjectError, dump(), merge(), parse(), read(), to_node(), to_plain(), _yaml()

### Community 46 - "Community 46"
Cohesion: 0.16
Nodes (11): check_command(), _hours(), _invalid_lines(), _listing(), next_command(), _plan_failed(), summary_command(), _valid_listing() (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.15
Nodes (7): clock(), free_port(), home(), isolated_git(), projects_dir(), token(), workspace()

### Community 48 - "Community 48"
Cohesion: 0.13
Nodes (10): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install(), use(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon() (+2 more)

### Community 49 - "Community 49"
Cohesion: 0.28
Nodes (16): load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file(), test_invalid_env_names_variable() (+8 more)

### Community 50 - "Community 50"
Cohesion: 0.18
Nodes (7): test_serve_starts_and_serves_docs(), wait_for_health(), main(), make_stubs(), parse(), anonymise(), logged_in()

### Community 51 - "Community 51"
Cohesion: 0.20
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 52 - "Community 52"
Cohesion: 0.17
Nodes (13): keep_head(), keep_newest_entries(), _lines(), select_spec(), _total(), Trimmed, words(), test_entries_keep_the_preamble_when_it_fits() (+5 more)

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 54 - "Community 54"
Cohesion: 0.12
Nodes (5): ApiClient, ApiError, DaemonNotRunning, test_client_connection_refused(), test_client_sends_token_and_reports_401()

### Community 55 - "Community 55"
Cohesion: 0.13
Nodes (12): create_app(), lifespan(), check_git(), test_create_app_uses_token_file(), make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves() (+4 more)

### Community 56 - "Community 56"
Cohesion: 0.16
Nodes (9): ContextBudgetError, ContextError, DependencyView, GateFailure, PreviousAttempt, RenderedPrompt, ReviewNote, TicketView (+1 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (4): configure_logging(), JsonFormatter, PlainFormatter, _Redactor

### Community 58 - "Community 58"
Cohesion: 0.14
Nodes (3): _Session, _signal_group(), _stream()

### Community 59 - "Community 59"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 60 - "Community 60"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 61 - "Community 61"
Cohesion: 0.24
Nodes (9): Agents, Budget, Commands, ContextSettings, GitSettings, Limits, MergePolicy, _Strict (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.15
Nodes (5): dotted_path(), _message(), _model_at(), _number(), ProjectValidationError

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (8): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_second_acquire_names_the_holder(), test_serve_refuses_while_another_daemon_holds_the_lock(), test_startup_recovers_and_skips_a_corrupt_database(), test_startup_without_a_projects_folder_serves()

### Community 64 - "Community 64"
Cohesion: 0.25
Nodes (11): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.18
Nodes (7): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1(), manager(), wt_repo(), wt_root()

### Community 66 - "Community 66"
Cohesion: 0.17
Nodes (4): init(), serve(), validate_project(), version()

### Community 67 - "Community 67"
Cohesion: 0.24
Nodes (10): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning() (+2 more)

### Community 69 - "Community 69"
Cohesion: 0.26
Nodes (8): branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing(), test_worktree_of_a_killed_process_is_recovered()

### Community 70 - "Community 70"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 71 - "Community 71"
Cohesion: 0.24
Nodes (8): test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401(), test_version_without_token_is_401()

### Community 72 - "Community 72"
Cohesion: 0.27
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 73 - "Community 73"
Cohesion: 0.40
Nodes (7): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 74 - "Community 74"
Cohesion: 0.42
Nodes (5): log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token(), test_reconfiguring_replaces_handlers()

### Community 77 - "Community 77"
Cohesion: 0.43
Nodes (6): test_init_existing_folder(), test_init_reports_every_problem(), test_init_then_validate(), test_init_with_branch_and_remote(), test_validate_missing_project(), test_validate_prints_every_error()

### Community 78 - "Community 78"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 81 - "Community 81"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 83 - "Community 83"
Cohesion: 0.33
Nodes (4): _fail_after_yaml(), test_failed_rename_leaves_nothing(), test_failure_mid_init_leaves_nothing(), test_missing_git_is_reported()

### Community 84 - "Community 84"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **19 isolated node(s):** `spoolhq`, `spoolhq-desktop`, `Config`, `InvalidRequest`, `NotRunning` (+14 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 800 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **36 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorktreeManager` connect `Community 5` to `Community 65`, `Community 2`, `Community 3`, `Community 35`, `Community 69`, `Community 75`, `Community 15`, `Community 51`, `Community 55`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `RunLog` (e.g. with `EventBus` and `Attempt`) actually correct?**
  _`RunLog` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `spoolhq`, `spoolhq-desktop`, `Config` to the rest of the system?**
  _19 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.060939060939060936 - nodes in this community are weakly interconnected._
- **Why does `RunLog` connect `Community 8` to `Community 0`, `Community 3`, `Community 68`, `Community 38`, `Community 75`, `Community 43`, `Community 82`, `Community 22`, `Community 55`, `Community 26`, `Community 63`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08108108108108109 - nodes in this community are weakly interconnected._