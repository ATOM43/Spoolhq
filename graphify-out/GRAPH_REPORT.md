# Graph Report - Project_Manager  (2026-10-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3252 nodes · 8688 edges · 174 communities (95 shown, 79 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 686 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `13a07e30`
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
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 156
- Community 157

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 111 edges
2. `WorktreeManager` - 74 edges
3. `ClaudeStreamParser` - 61 edges
4. `run_git()` - 50 edges
5. `RunRegistry` - 47 edges
6. `build_implementer_prompt()` - 46 edges
7. `FakeRunner` - 44 edges
8. `RunLoop` - 44 edges
9. `AgentPolicy` - 43 edges
10. `Ticket` - 40 edges

## Surprising Connections (you probably didn't know these)
- `integrate()` --calls--> `IntegrationResult`  [INFERRED]
  daemon/tests/services/runloop/test_loop.py → daemon/src/spoolhq/services/runloop/integrator.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `test_error_without_stderr_has_no_colon()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_git_error_keeps_the_last_20_stderr_lines()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 5-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (174 total, 79 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (52): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), keep_end(), summarize(), _usage_counts(), usd_to_micro() (+44 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (32): GateLine, HoldForIntegration, IntegrationResult, IntegrationStatus, Integrator, active_message(), agent_stopped(), attempt_once() (+24 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (23): agents_command(), describe(), make_runner(), available_runners(), existing_stubs(), permission_modes(), requested_tools(), PolicyViolation (+15 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (32): check_git(), disabled_hooks_path(), check_ticket_id(), branch_name(), slugify(), branch_sha(), default_branch_sha(), DirtyRepoError (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (44): describe(), _header(), _path(), _split_files(), trim_diff(), ItemVerdict, ReviewResult, _gate_word() (+36 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (47): git_executable(), WorktreeManager, test_interrupted_run_keeps_its_worktree(), commit_file(), git_repo(), run_git(), branches(), make_read_only() (+39 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (20): fail(), hours(), settings(), table(), check_command(), _invalid_lines(), _listing(), next_command() (+12 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (30): copy_dashboard(), make_project(), set_status(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files(), test_check_valid_plan(), test_next_on_the_dashboard() (+22 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (42): RunLog, test_startup_recovers_and_skips_a_corrupt_database(), raw(), run_log(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_closed_log_refuses_calls() (+34 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (8): take_run_lock(), RunLoop, _user_errors(), Active, Flags, NotFoundError, RunActiveError, RunLoopError

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (19): health(), cancel_run(), current_run(), discard_ticket(), _errors(), _loop(), pause_run(), resume_run() (+11 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (34): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+26 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (10): _clear_read_only_and_retry(), marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, remove_path(), same_path(), Worktree (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (20): lifespan(), acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld (+12 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (36): build_implementer_prompt(), _slot_sources(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text() (+28 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (15): ProcessResult, run_process(), _signal_group(), _stop_tree(), test_startup_without_a_projects_folder_serves(), test_serve_starts_and_serves_docs(), wait_for_health(), main() (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.14
Nodes (41): load_project(), run_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml() (+33 more)

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (19): allowed_env(), check_gate_command(), gate_env(), resolve_program(), split_command(), DoneWhenCheck, GateFailureData, GateResult (+11 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (12): utc_now(), AttemptStatus, EventKind, RunStatus, Usage, recover_interrupted(), encode_payload(), event_kind() (+4 more)

### Community 21 - "Community 21"
Cohesion: 0.15
Nodes (32): Budget, assert_gone(), read_record(), Recorder, run(), runner(), test_api_key_billing_passes_the_key_and_the_budget(), test_billing_follows_the_auth_method() (+24 more)

### Community 22 - "Community 22"
Cohesion: 0.10
Nodes (37): explain_idle(), check_transition(), parse_status(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once(), test_allowed_transitions_pass() (+29 more)

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (37): description, engines, node, license, name, packageManager, private, type (+29 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (34): ensure_clean(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes(), test_default_branch_sha() (+26 more)

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (15): ContextBudgetError, ContextError, PromptTemplateError, _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines() (+7 more)

### Community 26 - "Community 26"
Cohesion: 0.10
Nodes (27): editor_command(), run_editor(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment() (+19 more)

### Community 27 - "Community 27"
Cohesion: 0.08
Nodes (17): keep_for(), recover_all_worktrees(), _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (18): dumper(), loader(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap() (+10 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (19): require_valid(), sort_tickets(), critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours() (+11 more)

### Community 30 - "Community 30"
Cohesion: 0.14
Nodes (24): Hooked, crashed_run(), lock_is_free(), status(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree(), test_current_lists_the_phase_lines(), test_current_with_no_run() (+16 more)

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (24): FakeRunner, ReviewInputs, OutcomeRunner, run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages() (+16 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (24): cap_excerpt(), keep_head(), keep_newest_entries(), _lines(), select_spec(), _total(), Trimmed, words() (+16 more)

### Community 33 - "Community 33"
Cohesion: 0.09
Nodes (19): build_excerpt(), take(), clean(), _clip(), failing_tests(), first_failure(), _priority(), split_lines() (+11 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (7): TicketEdit, source_name(), TicketError, TicketValidationError, find_ticket_file(), render_ticket(), _ticket_files()

### Community 35 - "Community 35"
Cohesion: 0.23
Nodes (23): RunRegistry, failing(), Transcripts, kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text() (+15 more)

### Community 36 - "Community 36"
Cohesion: 0.15
Nodes (22): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd(), gates() (+14 more)

### Community 37 - "Community 37"
Cohesion: 0.11
Nodes (13): _assistant(), clock(), FakeGates, _init(), make_loop(), make(), Merging, project() (+5 more)

### Community 39 - "Community 39"
Cohesion: 0.10
Nodes (10): ApiClient, ApiError, DaemonNotRunning, _detail(), test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host() (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (11): create_app(), serve(), load_or_create_token(), read_token(), token_path(), ensure_home(), test_create_app_uses_token_file(), test_empty_token_file_is_replaced() (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.14
Nodes (17): on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact(), attempt(), run_log() (+9 more)

### Community 42 - "Community 42"
Cohesion: 0.11
Nodes (12): _read(), show_command(), ContextInputs, DependencyView, GateFailure, PreviousAttempt, RenderedPrompt, ReviewNote (+4 more)

### Community 43 - "Community 43"
Cohesion: 0.17
Nodes (12): all_command(), _base(), _call(), cancel_command(), _client(), _current_run_id(), discard_command(), _follow() (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (13): ProjectError, ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate() (+5 more)

### Community 45 - "Community 45"
Cohesion: 0.11
Nodes (15): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+7 more)

### Community 46 - "Community 46"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 47 - "Community 47"
Cohesion: 0.12
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 48 - "Community 48"
Cohesion: 0.12
Nodes (13): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_db_path(), state_dir(), _statements() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (19): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion(), Health (+11 more)

### Community 51 - "Community 51"
Cohesion: 0.10
Nodes (3): _Session, _signal_group(), _stream()

### Community 52 - "Community 52"
Cohesion: 0.14
Nodes (12): Agents, Budget, check_slug(), Commands, ContextSettings, GatesSettings, GateTimeouts, GitSettings (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.21
Nodes (23): parse_ticket(), errors_for(), make_project(), replace_line(), test_assignment_is_validated(), test_bad_file_name(), test_broken_file_does_not_stop_the_others(), test_crlf_frontmatter_errors_count_lines() (+15 more)

### Community 54 - "Community 54"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 55 - "Community 55"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 56 - "Community 56"
Cohesion: 0.13
Nodes (10): id_key(), PlanError, PlanProblem, SchedulerError, TransitionError, _and_list(), _find_cycles(), sort_ids() (+2 more)

### Community 57 - "Community 57"
Cohesion: 0.12
Nodes (5): ResumeTimer, ManualClock, test_cancel_and_close_drop_the_schedule(), test_fires_once_at_reset_plus_a_minute(), test_the_polling_thread_fires_and_a_failing_callback_is_logged()

### Community 58 - "Community 58"
Cohesion: 0.16
Nodes (13): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.13
Nodes (12): AgentPolicy, test_policy_fields_are_untouched_by_credentials_list(), test_unusable_backend_raises_before_starting(), test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced() (+4 more)

### Community 60 - "Community 60"
Cohesion: 0.14
Nodes (17): load_ticket(), read_ticket(), save_ticket(), tickets_dir(), test_body_is_written_verbatim(), test_changing_status_changes_only_that_line(), test_dashboard_filters(), test_flow_mapping_frontmatter_is_re_rendered() (+9 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (9): billing_for(), ClaudeCliRunner, format_version(), parse_version(), fake_probe(), test_auth_status_that_is_not_json(), test_linux_needs_bubblewrap_and_socat(), test_macos_is_enforceable_and_others_are_not() (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.20
Nodes (14): home_denials(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket(), test_extra_stack_commands_are_allowed(), test_read_only_git_follows_stack_commands() (+6 more)

### Community 63 - "Community 63"
Cohesion: 0.19
Nodes (13): build_argv(), child_env(), parent_env(), settings_json(), test_api_billing_keeps_only_the_api_key(), test_argv_is_exactly_the_documented_command_line(), test_budget_flag_only_for_api_billing(), test_child_env_is_an_allowlist() (+5 more)

### Community 64 - "Community 64"
Cohesion: 0.20
Nodes (11): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (7): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_next_follows_the_run_to_its_end(), test_status_of_an_active_run(), test_status_with_no_run()

### Community 66 - "Community 66"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 67 - "Community 67"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 68 - "Community 68"
Cohesion: 0.15
Nodes (11): parse_done_when(), DoneItem, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants(), test_done_when_ignores_code_fences() (+3 more)

### Community 69 - "Community 69"
Cohesion: 0.15
Nodes (5): merge(), parse(), read(), to_node(), write_atomic()

### Community 70 - "Community 70"
Cohesion: 0.17
Nodes (5): _deps(), edit_command(), list_command(), set_status_command(), show_command()

### Community 71 - "Community 71"
Cohesion: 0.15
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 72 - "Community 72"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 73 - "Community 73"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 74 - "Community 74"
Cohesion: 0.15
Nodes (9): check_worktree(), expand_home(), _remove_empty_tree(), remove_new_stubs(), test_read_only_argv_has_only_the_read_tools(), test_read_only_policy_has_no_commands(), test_stubs_with_content_are_kept(), test_worktree_inside_the_claude_folder_is_refused() (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.25
Nodes (11): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+3 more)

### Community 77 - "Community 77"
Cohesion: 0.14
Nodes (3): init(), validate_project(), version()

### Community 78 - "Community 78"
Cohesion: 0.19
Nodes (5): config_path(), default_projects_dir(), default_worktrees_dir(), home_dir(), Settings

### Community 79 - "Community 79"
Cohesion: 0.23
Nodes (12): round_trip_tickets(), save_and_read(), test_block_list_keeps_its_layout(), test_emptied_block_list_becomes_flow(), test_empty_list_stays_flow(), test_flow_list_stays_flow(), test_new_key_in_frontmatter_only_file(), test_new_key_is_appended_with_the_files_line_ending() (+4 more)

### Community 80 - "Community 80"
Cohesion: 0.18
Nodes (4): configure_logging(), JsonFormatter, PlainFormatter, _Redactor

### Community 81 - "Community 81"
Cohesion: 0.22
Nodes (8): test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401(), test_version_without_token_is_401()

### Community 82 - "Community 82"
Cohesion: 0.22
Nodes (7): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install(), use(), fake_claude_cmd(), sandbox_which()

### Community 83 - "Community 83"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 84 - "Community 84"
Cohesion: 0.30
Nodes (8): apply_transition(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 85 - "Community 85"
Cohesion: 0.35
Nodes (6): auth(), follow(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_refusals_carry_the_message(), test_run_through_the_api_is_held_for_integration()

### Community 86 - "Community 86"
Cohesion: 0.27
Nodes (7): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 87 - "Community 87"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 88 - "Community 88"
Cohesion: 0.47
Nodes (7): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 92 - "Community 92"
Cohesion: 0.22
Nodes (8): _id_sort_key(), list_tickets(), test_bad_project_name(), test_dashboard_plan_loads(), test_invalid_files_are_ordered_by_case_sensitive_name(), test_missing_project(), test_project_without_tickets_folder(), test_unknown_status_filter()

### Community 93 - "Community 93"
Cohesion: 0.39
Nodes (5): log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token(), test_reconfiguring_replaces_handlers()

### Community 95 - "Community 95"
Cohesion: 0.39
Nodes (3): policy(), user_home(), worktree()

### Community 97 - "Community 97"
Cohesion: 0.33
Nodes (3): sandbox_settings(), with_config_dir(), test_claude_config_dir_is_denied_when_set()

### Community 99 - "Community 99"
Cohesion: 0.43
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 100 - "Community 100"
Cohesion: 0.48
Nodes (3): manager(), wt_repo(), wt_root()

### Community 102 - "Community 102"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 104 - "Community 104"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 105 - "Community 105"
Cohesion: 0.47
Nodes (3): is_test(), main(), oversized()

## Knowledge Gaps
- **145 isolated node(s):** `CopyState`, `RetryProps`, `DaemonReply`, `RawDaemonInfo`, `build` (+140 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1108 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **79 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 8` to `Community 1`, `Community 98`, `Community 3`, `Community 35`, `Community 5`, `Community 6`, `Community 38`, `Community 9`, `Community 41`, `Community 13`, `Community 47`, `Community 48`, `Community 49`, `Community 20`, `Community 86`, `Community 58`, `Community 27`, `Community 30`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `Community 5` to `Community 3`, `Community 99`, `Community 100`, `Community 6`, `Community 67`, `Community 12`, `Community 86`, `Community 27`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `ClaudeStreamParser` connect `Community 0` to `Community 2`, `Community 51`, `Community 90`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `RunLog` (e.g. with `Attempt` and `AttemptKind`) actually correct?**
  _`RunLog` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ClaudeStreamParser` (e.g. with `FileEdit` and `Message`) actually correct?**
  _`ClaudeStreamParser` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CopyState`, `RetryProps`, `DaemonReply` to the rest of the system?**
  _145 weakly-connected nodes found - possible documentation gaps or missing edges._