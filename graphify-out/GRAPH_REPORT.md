# Graph Report - Spoolhq  (2026-10-18)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2470 nodes · 6610 edges · 127 communities (85 shown, 42 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 584 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `83a66db4`
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
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 125
- Community 126

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 89 edges
2. `WorktreeManager` - 71 edges
3. `ClaudeStreamParser` - 65 edges
4. `AgentPolicy` - 54 edges
5. `build_implementer_prompt()` - 46 edges
6. `run_git()` - 39 edges
7. `Ticket` - 37 edges
8. `fixture_inputs()` - 37 edges
9. `EventBus` - 34 edges
10. `load_settings()` - 32 edges

## Surprising Connections (you probably didn't know these)
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `failing_config()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/git/test_worktrees.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/git/test_worktrees.py → daemon/src/spoolhq/services/git/runner.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `append_transcript()` --uses--> `Attempt`  [INFERRED]
  daemon/src/spoolhq/services/runs/files.py → daemon/src/spoolhq/services/runs/model.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (127 total, 42 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (18): utc_now(), ArtifactName, attempt_dir_name(), _check_count(), encode_payload(), _event_kind(), fetch_run(), _to_event() (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (23): dump(), dumper(), loader(), merge(), parse(), read(), to_node(), to_plain() (+15 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (15): fail(), hours(), settings(), table(), _cost(), list_command(), show_command(), _tokens() (+7 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (48): load_ticket(), errors_for(), make_project(), replace_line(), save_and_read(), test_assignment_is_validated(), test_bad_file_name(), test_bad_project_name() (+40 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (43): git_executable(), WorktreeManager, run_git(), branches(), make_read_only(), marker(), real(), registered_paths() (+35 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (40): _run_log(), RunLog, raw(), run_log(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_closed_log_refuses_calls() (+32 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (38): GateFailure, build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text() (+30 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (40): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml(), test_bad_slug_is_refused() (+32 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (13): run_editor(), start_edit(), TicketEdit, source_name(), TicketError, TicketValidationError, find_ticket_file(), read_ticket() (+5 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (37): description, engines, node, license, name, packageManager, private, type (+29 more)

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (37): validate_plan(), check_transition(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once(), test_allowed_transitions_pass(), test_critical_path_skips_done_tickets() (+29 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (20): branch_sha(), default_branch_sha(), ensure_no_operation_in_progress(), has_local_branch(), is_branch_name(), is_work_tree(), MissingBranchError, operation_in_progress() (+12 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (31): ensure_clean(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes(), test_default_branch_sha() (+23 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (6): marker_key(), _norm(), RegisteredWorktree, same_path(), Worktree, WorktreeExistsError

### Community 16 - "Community 16"
Cohesion: 0.17
Nodes (32): assistant(), load(), parse(), replay(), result(), test_acting_before_init_is_a_violation(), test_api_billing_reports_cost_in_micro_usd(), test_assistant_rate_limit_error_without_later_success() (+24 more)

### Community 17 - "Community 17"
Cohesion: 0.08
Nodes (16): cap_excerpt(), ContextInputs, _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines(), _previous_vars() (+8 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (14): _recover_one(), RecoveryAction, RecoveryEntry, RecoveryReport, DirtyRepoError, RepoNotReadyError, check_git_version(), GitError (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (29): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install(), use(), copy_dashboard(), make_project(), set_status() (+21 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (25): editor_command(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores(), test_edit_interrupted_restores() (+17 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (11): ApiClient, ApiError, DaemonNotRunning, test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably() (+3 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (9): create_app(), lifespan(), health(), version(), Health, Version, check_git(), recover_all_worktrees() (+1 more)

### Community 23 - "Community 23"
Cohesion: 0.14
Nodes (13): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), summarize(), _usage_counts(), RateLimit, test_accepted_modes_can_be_widened_by_the_adapter() (+5 more)

### Community 24 - "Community 24"
Cohesion: 0.12
Nodes (21): keep_head(), keep_newest_entries(), _lines(), select_spec(), _total(), Trimmed, words(), RepoDocs (+13 more)

### Community 26 - "Community 26"
Cohesion: 0.15
Nodes (10): serve(), _serve(), load_or_create_token(), read_token(), token_path(), ensure_home(), test_empty_token_file_is_replaced(), test_loose_token_file_mode_is_tightened() (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.21
Nodes (25): read_record(), run(), runner(), test_api_key_billing_passes_the_key_and_the_budget(), test_billing_follows_the_auth_method(), test_claude_config_dir_reaches_the_settings(), test_default_permission_mode_from_env_scrub_is_accepted(), test_detect_leaves_no_stubs_in_the_current_folder() (+17 more)

### Community 28 - "Community 28"
Cohesion: 0.13
Nodes (11): FakeRunner, BackendInfo, RunResult, AgentRunner, test_cancel(), test_detect(), test_policy_violation(), test_replay_of_the_recorded_real_run() (+3 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (17): home_denials(), policy(), user_home(), worktree(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused() (+9 more)

### Community 30 - "Community 30"
Cohesion: 0.13
Nodes (12): ProjectError, ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate() (+4 more)

### Community 31 - "Community 31"
Cohesion: 0.14
Nodes (14): state_db_path(), seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts() (+6 more)

### Community 32 - "Community 32"
Cohesion: 0.15
Nodes (16): append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact(), attempt(), run_log(), test_append_transcript_refuses_non_json() (+8 more)

### Community 33 - "Community 33"
Cohesion: 0.11
Nodes (15): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+7 more)

### Community 34 - "Community 34"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (14): keep_end(), PolicyViolation, usd_to_micro(), check_command(), FileEdit, Message, Outcome, PermissionDenied (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.16
Nodes (19): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion(), Health (+11 more)

### Community 37 - "Community 37"
Cohesion: 0.12
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (16): EventBus, stuck(), bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get() (+8 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (7): config_path(), ConfigError, default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (10): check_command(), _invalid_lines(), _listing(), next_command(), _plan_failed(), summary_command(), _valid_listing(), PlanError (+2 more)

### Community 42 - "Community 42"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (13): build_argv(), sandbox_settings(), with_config_dir(), AgentPolicy, Budget, settings_json(), test_argv_is_exactly_the_documented_command_line(), test_budget_flag_only_for_api_billing() (+5 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (4): RunRegistry, WorkspaceRuns, test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 45 - "Community 45"
Cohesion: 0.11
Nodes (11): check_worktree(), existing_stubs(), expand_home(), format_version(), parse_version(), _remove_empty_tree(), remove_new_stubs(), BackendUnavailableError (+3 more)

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (10): Agents, Budget, check_slug(), Commands, ContextSettings, GitSettings, Limits, MergePolicy (+2 more)

### Community 47 - "Community 47"
Cohesion: 0.18
Nodes (11): require_valid(), critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours(), summary() (+3 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (8): ContextBudgetError, ContextError, PromptTemplateError, DependencyView, PreviousAttempt, RenderedPrompt, ReviewNote, TicketView

### Community 49 - "Community 49"
Cohesion: 0.28
Nodes (16): load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file(), test_invalid_env_names_variable() (+8 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (9): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_dir(), _statements(), _user_version() (+1 more)

### Community 51 - "Community 51"
Cohesion: 0.20
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 52 - "Community 52"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.18
Nodes (9): client(), clock(), free_port(), git_repo(), home(), isolated_git(), projects_dir(), token() (+1 more)

### Community 54 - "Community 54"
Cohesion: 0.23
Nodes (10): sort_tickets(), explain_idle(), IdleReason, _ids(), next_ready(), _statuses(), _unmet(), waiting_on() (+2 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (7): acquire_daemon_lock(), DaemonAlreadyRunning, lock_path(), _read_pid(), _try_lock(), _unlock(), _clear_read_only_and_retry()

### Community 56 - "Community 56"
Cohesion: 0.16
Nodes (12): child_env(), fake_claude_cmd(), fake_probe(), parent_env(), test_api_billing_keeps_only_the_api_key(), test_auth_status_that_is_not_json(), test_child_env_is_an_allowlist(), test_linux_needs_bubblewrap_and_socat() (+4 more)

### Community 57 - "Community 57"
Cohesion: 0.20
Nodes (10): recover_worktrees(), parse_worktree_list(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), test_recovery_with_no_root_does_nothing() (+2 more)

### Community 58 - "Community 58"
Cohesion: 0.19
Nodes (9): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_second_acquire_names_the_holder(), test_serve_refuses_while_another_daemon_holds_the_lock(), test_startup_recovers_and_skips_a_corrupt_database(), test_startup_without_a_projects_folder_serves() (+1 more)

### Community 59 - "Community 59"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 60 - "Community 60"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 61 - "Community 61"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 62 - "Community 62"
Cohesion: 0.16
Nodes (6): parse_done_when(), DoneItem, test_done_when_heading_variants(), test_done_when_ignores_code_fences(), test_done_when_items(), test_empty_done_when_is_a_warning()

### Community 63 - "Community 63"
Cohesion: 0.18
Nodes (8): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 64 - "Community 64"
Cohesion: 0.25
Nodes (11): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.23
Nodes (5): billing_for(), ClaudeCliRunner, test_failing_version_command_means_not_installed(), test_unusable_backend_raises_before_starting(), test_real_run_creates_a_file_and_is_denied_python()

### Community 69 - "Community 69"
Cohesion: 0.19
Nodes (4): dotted_path(), _message(), _model_at(), _number()

### Community 70 - "Community 70"
Cohesion: 0.22
Nodes (5): main(), make_stubs(), parse(), anonymise(), logged_in()

### Community 71 - "Community 71"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 72 - "Community 72"
Cohesion: 0.19
Nodes (6): remove_path(), test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1(), test_remove_path_handles_files_and_symlinks()

### Community 73 - "Community 73"
Cohesion: 0.24
Nodes (8): test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401(), test_version_without_token_is_401()

### Community 74 - "Community 74"
Cohesion: 0.23
Nodes (4): check_ticket_id(), branch_name(), slugify(), neutral_cwd()

### Community 75 - "Community 75"
Cohesion: 0.27
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 76 - "Community 76"
Cohesion: 0.22
Nodes (3): init(), validate_project(), version()

### Community 77 - "Community 77"
Cohesion: 0.25
Nodes (4): id_key(), _and_list(), _find_cycles(), sort_ids()

### Community 79 - "Community 79"
Cohesion: 0.24
Nodes (4): agents_command(), describe(), available_runners(), test_claude_code_cli_is_the_only_backend()

### Community 80 - "Community 80"
Cohesion: 0.22
Nodes (4): TransitionError, apply_transition(), parse_status(), TransitionResult

### Community 81 - "Community 81"
Cohesion: 0.20
Nodes (8): _id_sort_key(), InvalidTicket, list_tickets(), test_dashboard_plan_loads(), test_folders_are_ignored(), test_hidden_and_other_files_are_ignored(), test_invalid_files_are_ordered_by_case_sensitive_name(), test_unknown_status_filter()

### Community 82 - "Community 82"
Cohesion: 0.47
Nodes (7): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 86 - "Community 86"
Cohesion: 0.36
Nodes (4): commit_file(), manager(), wt_repo(), wt_root()

### Community 87 - "Community 87"
Cohesion: 0.25
Nodes (3): assert_gone(), Recorder, test_cancel()

### Community 88 - "Community 88"
Cohesion: 0.25
Nodes (5): format_errors(), parse_ticket(), test_defaults_for_optional_fields(), test_every_status_is_accepted(), test_parse_ticket_parts()

### Community 89 - "Community 89"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 91 - "Community 91"
Cohesion: 0.52
Nodes (6): copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 92 - "Community 92"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 95 - "Community 95"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **19 isolated node(s):** `eslint-import-resolver-typescript`, `@fontsource/inter`, `@fontsource/jetbrains-mono`, `jsdom`, `prettier` (+14 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 813 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **42 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 5` to `Community 0`, `Community 97`, `Community 2`, `Community 35`, `Community 32`, `Community 38`, `Community 44`, `Community 58`, `Community 31`, `Community 94`, `Community 63`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `RunLog` (e.g. with `Usage` and `EventBus`) actually correct?**
  _`RunLog` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `eslint-import-resolver-typescript`, `@fontsource/inter`, `@fontsource/jetbrains-mono` to the rest of the system?**
  _19 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05450165612767239 - nodes in this community are weakly interconnected._
- **Why does `WorktreeManager` connect `Community 4` to `Community 2`, `Community 72`, `Community 15`, `Community 18`, `Community 51`, `Community 22`, `Community 86`, `Community 57`, `Community 90`, `Community 63`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06516290726817042 - nodes in this community are weakly interconnected._