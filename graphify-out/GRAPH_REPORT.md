# Graph Report - Spoolhq  (2026-10-18)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2247 nodes · 5993 edges · 112 communities (75 shown, 37 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 517 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0e9331e6`
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
- Community 110
- Community 111

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 94 edges
2. `WorktreeManager` - 72 edges
3. `ClaudeStreamParser` - 64 edges
4. `AgentPolicy` - 48 edges
5. `Ticket` - 40 edges
6. `run_git()` - 38 edges
7. `EventBus` - 34 edges
8. `list_tickets()` - 32 edges
9. `ClaudeCliRunner` - 31 edges
10. `load_settings()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `failing_config()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/git/test_worktrees.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/git/test_worktrees.py → daemon/src/spoolhq/services/git/runner.py
- `test_publish_completes_while_a_subscriber_never_reads()` --indirect_call--> `stuck()`  [INFERRED]
  daemon/tests/services/runs/test_bus.py → daemon/tests/services/git/test_recovery.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (112 total, 37 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (49): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), summarize(), _usage_counts(), usd_to_micro(), PermissionDenied (+41 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (62): _id_sort_key(), list_tickets(), load_ticket(), parse_ticket(), read_ticket(), save_ticket(), errors_for(), make_project() (+54 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (17): _tokens(), attempt_dir_name(), _check_count(), check_ticket_id(), encode_payload(), _event_kind(), fetch_run(), _to_run() (+9 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (18): parse_done_when(), run_editor(), start_edit(), TicketEdit, source_name(), TicketError, TicketValidationError, check_ticket_id() (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (27): PlanError, PlanProblem, SchedulerError, TransitionError, _find_cycles(), id_key(), require_valid(), sort_ids() (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (14): fail(), settings(), table(), _cost(), list_command(), show_command(), _workspace(), _deps() (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (40): _run_log(), RunLog, raw(), run_log(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_closed_log_refuses_calls() (+32 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (41): _and_list(), validate_plan(), explain_idle(), check_transition(), parse_status(), dashboard(), make(), messages() (+33 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (35): fake_claude_cmd(), assert_gone(), fake_probe(), read_record(), Recorder, run(), runner(), test_api_key_billing_passes_the_key_and_the_budget() (+27 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (41): git_executable(), WorktreeManager, run_git(), branches(), make_read_only(), marker(), real(), registered_paths() (+33 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (20): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project(), client() (+12 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (37): description, engines, node, license, name, packageManager, private, type (+29 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (12): PolicyViolation, BackendInfo, check_command(), FileEdit, Message, Outcome, PolicyError, RunResult (+4 more)

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (32): ensure_clean(), status_entries(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes() (+24 more)

### Community 16 - "Community 16"
Cohesion: 0.17
Nodes (34): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml(), test_bad_slug_is_refused() (+26 more)

### Community 17 - "Community 17"
Cohesion: 0.10
Nodes (18): _block_indent(), _dumper(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _loader(), _node() (+10 more)

### Community 18 - "Community 18"
Cohesion: 0.16
Nodes (32): copy_dashboard(), make_project(), set_status(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files(), test_check_valid_plan(), test_next_on_the_dashboard() (+24 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (24): editor_command(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores(), test_edit_invalid_restores_the_backup() (+16 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (17): append_transcript(), _artifact_name(), ArtifactName, attempt_dir(), attempt_files(), write_artifact(), attempt(), run_log() (+9 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (6): branch_sha(), command_error(), marker_key(), RegisteredWorktree, remove_path(), Worktree

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (9): keep_for(), recover_all_worktrees(), _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (10): branch_name(), check_ticket_id(), slugify(), GitError, BranchConflictError, _clear_read_only_and_retry(), IdentityError, _norm() (+2 more)

### Community 24 - "Community 24"
Cohesion: 0.09
Nodes (3): Subscription, _to_event(), Event

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (8): create_app(), lifespan(), health(), version(), Health, Version, check_git(), test_create_app_uses_token_file()

### Community 27 - "Community 27"
Cohesion: 0.13
Nodes (14): sandbox_settings(), FakeRunner, AgentPolicy, settings_json(), test_argv_is_exactly_the_documented_command_line(), test_policy_fields_are_untouched_by_credentials_list(), test_settings_json(), test_cancel() (+6 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (14): ProjectError, ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate() (+6 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (14): state_db_path(), seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts() (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (15): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+7 more)

### Community 31 - "Community 31"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 32 - "Community 32"
Cohesion: 0.12
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 33 - "Community 33"
Cohesion: 0.16
Nodes (19): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion(), Health (+11 more)

### Community 34 - "Community 34"
Cohesion: 0.11
Nodes (14): disabled_hooks_path(), check_git_version(), disabled_hooks_dir(), git_env(), GitResult, hook_and_signing_options(), neutral_cwd(), parse_git_version() (+6 more)

### Community 35 - "Community 35"
Cohesion: 0.14
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 36 - "Community 36"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (10): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_dir(), _statements(), _user_version() (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.14
Nodes (8): dump(), merge(), parse(), read(), to_node(), to_plain(), write_atomic(), _yaml()

### Community 39 - "Community 39"
Cohesion: 0.16
Nodes (10): billing_for(), build_argv(), ClaudeCliRunner, format_version(), parse_version(), Budget, test_budget_flag_only_for_api_billing(), test_no_prompt_and_no_skip_permissions_in_argv() (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.20
Nodes (14): home_denials(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket(), test_extra_stack_commands_are_allowed(), test_read_only_git_follows_stack_commands() (+6 more)

### Community 41 - "Community 41"
Cohesion: 0.22
Nodes (8): _serve(), load_or_create_token(), read_token(), token_path(), test_empty_token_file_is_replaced(), test_loose_token_file_mode_is_tightened(), test_token_file_and_home_have_private_modes(), test_token_is_created_once_and_reused()

### Community 42 - "Community 42"
Cohesion: 0.28
Nodes (16): load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file(), test_invalid_env_names_variable() (+8 more)

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (9): branch_exists(), default_branch_sha(), DirtyRepoError, ensure_no_operation_in_progress(), is_work_tree(), MissingBranchError, operation_in_progress(), OperationInProgressError (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.20
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 45 - "Community 45"
Cohesion: 0.18
Nodes (10): check_command(), _hours(), _invalid_lines(), _listing(), next_command(), _plan_failed(), summary_command(), _valid_listing() (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 47 - "Community 47"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (4): ApiClient, ApiError, DaemonNotRunning, test_client_connection_refused()

### Community 49 - "Community 49"
Cohesion: 0.15
Nodes (3): _Session, _signal_group(), _stream()

### Community 50 - "Community 50"
Cohesion: 0.20
Nodes (10): parse_worktree_list(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+2 more)

### Community 51 - "Community 51"
Cohesion: 0.17
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 52 - "Community 52"
Cohesion: 0.20
Nodes (8): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_second_acquire_names_the_holder(), test_serve_refuses_while_another_daemon_holds_the_lock(), test_startup_recovers_and_skips_a_corrupt_database(), test_startup_without_a_projects_folder_serves()

### Community 53 - "Community 53"
Cohesion: 0.18
Nodes (6): test_client_sends_token_and_reports_401(), test_serve_starts_and_serves_docs(), wait_for_health(), main(), make_stubs(), parse()

### Community 54 - "Community 54"
Cohesion: 0.25
Nodes (11): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+3 more)

### Community 55 - "Community 55"
Cohesion: 0.23
Nodes (7): acquire_daemon_lock(), DaemonAlreadyRunning, lock_path(), _read_pid(), _try_lock(), _unlock(), test_unknown_holder_pid()

### Community 57 - "Community 57"
Cohesion: 0.17
Nodes (4): init(), serve(), validate_project(), version()

### Community 59 - "Community 59"
Cohesion: 0.20
Nodes (6): config_path(), ConfigError, default_projects_dir(), default_worktrees_dir(), ensure_home(), home_dir()

### Community 60 - "Community 60"
Cohesion: 0.27
Nodes (8): Agents, Budget, Commands, GitSettings, Limits, MergePolicy, _Strict, Tracker

### Community 61 - "Community 61"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 62 - "Community 62"
Cohesion: 0.23
Nodes (6): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install(), use(), sandbox_which()

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (5): check_worktree(), existing_stubs(), expand_home(), _remove_empty_tree(), remove_new_stubs()

### Community 64 - "Community 64"
Cohesion: 0.27
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 65 - "Community 65"
Cohesion: 0.20
Nodes (3): test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 66 - "Community 66"
Cohesion: 0.24
Nodes (4): agents_command(), describe(), available_runners(), test_claude_code_cli_is_the_only_backend()

### Community 67 - "Community 67"
Cohesion: 0.40
Nodes (7): apply_transition(), copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 68 - "Community 68"
Cohesion: 0.36
Nodes (8): test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401(), test_version_without_token_is_401()

### Community 71 - "Community 71"
Cohesion: 0.43
Nodes (6): test_init_existing_folder(), test_init_reports_every_problem(), test_init_then_validate(), test_init_with_branch_and_remote(), test_validate_missing_project(), test_validate_prints_every_error()

### Community 72 - "Community 72"
Cohesion: 0.36
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 73 - "Community 73"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 78 - "Community 78"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 80 - "Community 80"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 81 - "Community 81"
Cohesion: 0.47
Nodes (5): child_env(), parent_env(), test_api_billing_keeps_only_the_api_key(), test_child_env_is_an_allowlist(), test_windows_variables_only_on_windows()

### Community 83 - "Community 83"
Cohesion: 0.33
Nodes (3): test_session_teardown_failure_keeps_the_original_error(), broken(), test_teardown_deletes_the_folder_when_git_cannot()

### Community 84 - "Community 84"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **19 isolated node(s):** `Config`, `InvalidRequest`, `NotRunning`, `TokenMissing`, `spoolhq` (+14 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 734 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 6` to `Community 2`, `Community 35`, `Community 5`, `Community 37`, `Community 12`, `Community 82`, `Community 52`, `Community 20`, `Community 22`, `Community 56`, `Community 24`, `Community 29`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `RunLog` (e.g. with `EventBus` and `Attempt`) actually correct?**
  _`RunLog` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `InvalidRequest`, `NotRunning` to the rest of the system?**
  _19 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0675549322113137 - nodes in this community are weakly interconnected._
- **Why does `WorktreeManager` connect `Community 9` to `Community 34`, `Community 5`, `Community 72`, `Community 75`, `Community 76`, `Community 12`, `Community 44`, `Community 50`, `Community 83`, `Community 21`, `Community 22`, `Community 23`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0856140350877193 - nodes in this community are weakly interconnected._