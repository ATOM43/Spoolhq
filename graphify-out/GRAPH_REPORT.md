# Graph Report - Project_Manager  (2026-10-18)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2845 nodes · 7375 edges · 165 communities (91 shown, 74 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 549 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `87b28fae`
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
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 148
- Community 149

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 97 edges
2. `WorktreeManager` - 74 edges
3. `ClaudeStreamParser` - 66 edges
4. `AgentPolicy` - 59 edges
5. `build_implementer_prompt()` - 45 edges
6. `FakeRunner` - 42 edges
7. `run_git()` - 41 edges
8. `Ticket` - 40 edges
9. `fixture_inputs()` - 36 edges
10. `EventBus` - 35 edges

## Surprising Connections (you probably didn't know these)
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `test_publish_completes_while_a_subscriber_never_reads()` --indirect_call--> `stuck()`  [INFERRED]
  daemon/tests/services/runs/test_bus.py → daemon/tests/services/git/test_recovery.py
- `ClaudeCliRunner` --uses--> `ClaudeStreamParser`  [INFERRED]
  daemon/src/spoolhq/services/agents/claude_cli.py → daemon/src/spoolhq/services/agents/claude_stream.py
- `ClaudeCliRunner` --uses--> `BackendInfo`  [INFERRED]
  daemon/src/spoolhq/services/agents/claude_cli.py → daemon/src/spoolhq/services/agents/model.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (165 total, 74 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (53): ClaudeCliRunner, format_version(), parse_version(), AgentPolicy, test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install() (+45 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (50): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), summarize(), _usage_counts(), PermissionDenied, RateLimit (+42 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (7): main(), make_stubs(), parse(), anonymise(), logged_in(), test_real_run_creates_a_file_and_is_denied_python(), test_template_is_in_the_built_wheel()

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (23): billing_for(), _Session, _signal_group(), _stream(), build_argv(), check_worktree(), child_env(), existing_stubs() (+15 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (52): load_ticket(), errors_for(), make_project(), replace_line(), save_and_read(), test_assignment_is_validated(), test_bad_file_name(), test_bad_project_name() (+44 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (18): agents_command(), describe(), available_runners(), keep_end(), PolicyViolation, usd_to_micro(), BackendInfo, Budget (+10 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (24): branch_name(), slugify(), default_branch_sha(), DirtyRepoError, ensure_no_operation_in_progress(), has_local_branch(), is_branch_name(), is_work_tree() (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (22): dumper(), loader(), merge(), parse(), read(), to_node(), to_plain(), _block_indent() (+14 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (12): branch_sha(), command_error(), subcommand(), trim_stderr(), _clear_read_only_and_retry(), marker_key(), _norm(), RegisteredWorktree (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (43): git_executable(), WorktreeManager, run_git(), branches(), make_read_only(), marker(), real(), registered_paths() (+35 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (39): RunLog, raw(), run_log(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_closed_log_refuses_calls(), test_committed_events_are_published_in_order() (+31 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (37): GateFailure, build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text() (+29 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (17): write_atomic(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError, find_ticket_file(), _id_sort_key() (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (20): allowed_env(), check_gate_command(), gate_env(), resolve_program(), split_command(), DoneWhenCheck, GateFailureData, GateResult (+12 more)

### Community 14 - "Community 14"
Cohesion: 0.09
Nodes (14): utc_now(), Transaction, AttemptKind, AttemptStatus, Event, EventKind, RunStatus, Usage (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (35): ensure_clean(), status_entries(), GitResult, fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids() (+27 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (8): describe(), make_runner(), config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (36): explain_idle(), check_transition(), parse_status(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once(), test_allowed_transitions_pass() (+28 more)

### Community 20 - "Community 20"
Cohesion: 0.06
Nodes (37): description, engines, node, license, name, packageManager, private, type (+29 more)

### Community 21 - "Community 21"
Cohesion: 0.07
Nodes (16): ContextBudgetError, ContextError, PromptTemplateError, _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines() (+8 more)

### Community 22 - "Community 22"
Cohesion: 0.17
Nodes (36): load_project(), del_path(), errors_for(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml(), test_bad_slug_is_refused(), test_default_branch_git_error_is_reported() (+28 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (9): fail(), settings(), run_command(), review_command(), _deps(), edit_command(), list_command(), set_status_command() (+1 more)

### Community 24 - "Community 24"
Cohesion: 0.09
Nodes (13): serve(), load_or_create_token(), read_token(), token_path(), ensure_home(), disabled_hooks_dir(), hook_and_signing_options(), test_serve_starts_and_serves_docs() (+5 more)

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (5): check_ticket_id(), attempt_dir_name(), _check_count(), Attempt, Run

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 27 - "Community 27"
Cohesion: 0.09
Nodes (16): acquire_daemon_lock(), DaemonAlreadyRunning, DaemonLock, lock_path(), _read_pid(), _try_lock(), _unlock(), make_workspace() (+8 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (22): home_denials(), policy(), user_home(), worktree(), test_read_only_argv_has_only_the_read_tools(), test_read_only_policy_has_no_commands(), test_worktree_inside_the_claude_folder_is_refused(), test_worktree_must_not_be_or_contain_the_home() (+14 more)

### Community 29 - "Community 29"
Cohesion: 0.11
Nodes (23): cap_excerpt(), keep_head(), keep_newest_entries(), _lines(), select_spec(), _total(), Trimmed, words() (+15 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (16): ProjectError, ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate() (+8 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (17): append_transcript(), _artifact_name(), ArtifactName, attempt_dir(), attempt_files(), write_artifact(), attempt(), run_log() (+9 more)

### Community 32 - "Community 32"
Cohesion: 0.15
Nodes (22): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd(), gates() (+14 more)

### Community 33 - "Community 33"
Cohesion: 0.08
Nodes (6): health(), version(), Health, Version, _is_api_path(), LocalOnlyMiddleware

### Community 34 - "Community 34"
Cohesion: 0.11
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (15): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+7 more)

### Community 36 - "Community 36"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 37 - "Community 37"
Cohesion: 0.20
Nodes (23): finish(), consistency_errors(), parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met() (+15 more)

### Community 38 - "Community 38"
Cohesion: 0.16
Nodes (19): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion(), Health (+11 more)

### Community 39 - "Community 39"
Cohesion: 0.11
Nodes (10): recover_all_worktrees(), _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.23
Nodes (22): ReviewInputs, run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages(), test_cancelled_is_passed_through(), test_changes_requested_names_the_unmet_item() (+14 more)

### Community 41 - "Community 41"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 42 - "Community 42"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (9): describe(), GateLine, ItemVerdict, ReviewResult, _ignore(), InvalidVerdict, _location(), ParsedItem (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (17): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_clean_strips_ansi_and_crlf() (+9 more)

### Community 45 - "Community 45"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 47 - "Community 47"
Cohesion: 0.16
Nodes (13): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+5 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (12): create_app(), lifespan(), check_git(), make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves() (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.12
Nodes (5): ApiClient, ApiError, DaemonNotRunning, test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401()

### Community 50 - "Community 50"
Cohesion: 0.15
Nodes (8): _read(), show_command(), ContextInputs, DependencyView, PreviousAttempt, RenderedPrompt, ReviewNote, TicketView

### Community 51 - "Community 51"
Cohesion: 0.18
Nodes (11): require_valid(), critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours(), summary() (+3 more)

### Community 52 - "Community 52"
Cohesion: 0.15
Nodes (7): table(), _cost(), list_command(), _run_log(), show_command(), _tokens(), _workspace()

### Community 53 - "Community 53"
Cohesion: 0.18
Nodes (10): hours(), check_command(), _invalid_lines(), _listing(), next_command(), _plan_failed(), summary_command(), _valid_listing() (+2 more)

### Community 54 - "Community 54"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 55 - "Community 55"
Cohesion: 0.19
Nodes (11): Agents, Budget, Commands, ContextSettings, GatesSettings, GateTimeouts, GitSettings, Limits (+3 more)

### Community 56 - "Community 56"
Cohesion: 0.18
Nodes (10): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_db_path(), state_dir(), _statements() (+2 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (12): parse_done_when(), DoneItem, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants(), test_done_when_ignores_code_fences() (+4 more)

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 59 - "Community 59"
Cohesion: 0.18
Nodes (9): ProcessResult, run_process(), _signal_group(), _stop_tree(), alive(), run(), test_invalid_utf8_and_crlf_are_cleaned_in_the_log(), test_output_cap_cuts_the_log_and_drains_the_process() (+1 more)

### Community 60 - "Community 60"
Cohesion: 0.34
Nodes (17): copy_dashboard(), make_project(), set_status(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files(), test_check_valid_plan(), test_next_on_the_dashboard() (+9 more)

### Community 61 - "Community 61"
Cohesion: 0.12
Nodes (7): _gate_word(), _items(), render_review_prompt(), review(), capture(), test_each_review_is_its_own_run(), test_real_review_names_the_missing_test()

### Community 62 - "Community 62"
Cohesion: 0.22
Nodes (8): sort_tickets(), IdleReason, _ids(), next_ready(), _statuses(), _unmet(), waiting_on(), Ticket

### Community 63 - "Community 63"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 64 - "Community 64"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 65 - "Community 65"
Cohesion: 0.20
Nodes (9): FakeRunner, test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file(), test_token_budget() (+1 more)

### Community 66 - "Community 66"
Cohesion: 0.16
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 67 - "Community 67"
Cohesion: 0.15
Nodes (4): RunRegistry, WorkspaceRuns, test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 68 - "Community 68"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 69 - "Community 69"
Cohesion: 0.25
Nodes (11): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 71 - "Community 71"
Cohesion: 0.17
Nodes (8): clock(), free_port(), git_repo(), home(), isolated_git(), projects_dir(), token(), workspace()

### Community 72 - "Community 72"
Cohesion: 0.21
Nodes (7): id_key(), _and_list(), _find_cycles(), sort_ids(), validate_plan(), test_ids_sort_by_number(), test_three_ticket_cycle_lists_its_members_in_order()

### Community 73 - "Community 73"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 74 - "Community 74"
Cohesion: 0.18
Nodes (4): configure_logging(), JsonFormatter, PlainFormatter, _Redactor

### Community 75 - "Community 75"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 76 - "Community 76"
Cohesion: 0.26
Nodes (8): parse_worktree_list(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_with_no_root_does_nothing(), test_worktree_of_a_killed_process_is_recovered(), test_parse_worktree_list()

### Community 77 - "Community 77"
Cohesion: 0.21
Nodes (4): PlanError, PlanProblem, SchedulerError, TransitionError

### Community 78 - "Community 78"
Cohesion: 0.30
Nodes (8): apply_transition(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 80 - "Community 80"
Cohesion: 0.27
Nodes (9): test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401() (+1 more)

### Community 81 - "Community 81"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 82 - "Community 82"
Cohesion: 0.22
Nodes (3): init(), validate_project(), version()

### Community 83 - "Community 83"
Cohesion: 0.24
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 84 - "Community 84"
Cohesion: 0.47
Nodes (7): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 85 - "Community 85"
Cohesion: 0.25
Nodes (4): test_client_connection_refused(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 86 - "Community 86"
Cohesion: 0.36
Nodes (4): commit_file(), manager(), wt_repo(), wt_root()

### Community 87 - "Community 87"
Cohesion: 0.39
Nodes (5): log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token(), test_reconfiguring_replaces_handlers()

### Community 89 - "Community 89"
Cohesion: 0.43
Nodes (6): test_init_existing_folder(), test_init_reports_every_problem(), test_init_then_validate(), test_init_with_branch_and_remote(), test_validate_missing_project(), test_validate_prints_every_error()

### Community 90 - "Community 90"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 93 - "Community 93"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 96 - "Community 96"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 97 - "Community 97"
Cohesion: 0.47
Nodes (3): is_test(), main(), oversized()

## Knowledge Gaps
- **145 isolated node(s):** `CopyState`, `RetryProps`, `DaemonReply`, `RawDaemonInfo`, `spoolhq` (+140 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 972 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **74 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorktreeManager` connect `Community 9` to `Community 2`, `Community 6`, `Community 39`, `Community 8`, `Community 76`, `Community 14`, `Community 16`, `Community 48`, `Community 83`, `Community 86`, `Community 58`, `Community 92`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `RunLog` connect `Community 10` to `Community 34`, `Community 67`, `Community 100`, `Community 14`, `Community 47`, `Community 48`, `Community 52`, `Community 25`, `Community 27`, `Community 31`, `Community 95`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `AgentPolicy` connect `Community 0` to `Community 65`, `Community 3`, `Community 5`, `Community 40`, `Community 28`, `Community 94`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `RunLog` (e.g. with `EventBus` and `Attempt`) actually correct?**
  _`RunLog` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ClaudeStreamParser` (e.g. with `ClaudeCliRunner` and `_Session`) actually correct?**
  _`ClaudeStreamParser` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `AgentPolicy` (e.g. with `ClaudeCliRunner` and `build_argv()`) actually correct?**
  _`AgentPolicy` has 8 INFERRED edges - model-reasoned connections that need verification._