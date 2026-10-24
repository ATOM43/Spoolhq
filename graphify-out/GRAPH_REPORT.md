# Graph Report - Project_Manager  (2026-10-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3457 nodes · 9821 edges · 187 communities (114 shown, 73 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 871 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d714a0fc`
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
- Community 94
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
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 118
- Community 119
- Community 120
- Community 121
- Community 123
- Community 124
- Community 126
- Community 127
- Community 173
- Community 174

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 125 edges
2. `WorktreeManager` - 86 edges
3. `RunRegistry` - 71 edges
4. `run_git()` - 68 edges
5. `ClaudeStreamParser` - 61 edges
6. `Transcripts` - 59 edges
7. `FakeRunner` - 48 edges
8. `RunLoop` - 47 edges
9. `build_implementer_prompt()` - 47 edges
10. `AgentPolicy` - 43 edges

## Surprising Connections (you probably didn't know these)
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/runloop/test_integration.py → daemon/src/spoolhq/services/git/runner.py
- `test_error_without_stderr_has_no_colon()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_git_error_keeps_the_last_20_stderr_lines()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `integrate()` --calls--> `IntegrationResult`  [INFERRED]
  daemon/tests/services/runloop/test_loop.py → daemon/src/spoolhq/services/runloop/integrator.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 5-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (187 total, 73 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (52): billing_for(), ClaudeCliRunner, format_version(), parse_version(), AgentPolicy, Budget, test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend() (+44 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (46): _header(), _path(), _split_files(), trim_diff(), GateLine, ItemVerdict, ReviewResult, _gate_word() (+38 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (28): check_ticket_id(), branch_name(), slugify(), branch_sha(), default_branch_sha(), ensure_no_operation_in_progress(), has_local_branch(), is_branch_name() (+20 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (34): advance(), checked_out(), commit(), conclude_merge(), conflict_files(), create_tag(), ensure_main_ready(), _git() (+26 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (43): _run_log(), RunLog, raw(), run_log(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_closed_log_refuses_calls() (+35 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (34): FakeRunner, ReviewInputs, test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run() (+26 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (22): check_worktree(), existing_stubs(), expand_home(), permission_modes(), _remove_empty_tree(), remove_new_stubs(), requested_tools(), PolicyViolation (+14 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (49): load_ticket(), errors_for(), make_project(), replace_line(), save_and_read(), test_assignment_is_validated(), test_bad_file_name(), test_block_list_keeps_its_layout() (+41 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (39): ClaudeStreamParser, assistant(), load(), parse(), replay(), result(), test_accepted_modes_can_be_widened_by_the_adapter(), test_acting_before_init_is_a_violation() (+31 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (41): _clear_read_only_and_retry(), remove_path(), run_git(), branches(), make_read_only(), marker(), real(), registered_paths() (+33 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (12): marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, same_path(), Worktree, WorktreeManager, WorktreeSession (+4 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (18): cancel_run(), current_run(), discard_ticket(), _errors(), integrate_ticket(), _loop(), pause_run(), resume_run() (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (7): RunLoop, Active, NotFoundError, RunActiveError, RunLoopError, user_errors(), Run

### Community 13 - "Community 13"
Cohesion: 0.10
Nodes (22): agent_stopped(), attempt_once(), check_resolved(), commit(), drive(), _git(), implement(), implementer_prompt() (+14 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (15): fail(), hours(), settings(), describe(), run_command(), check_command(), _invalid_lines(), _listing() (+7 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (14): run_editor(), start_edit(), TicketEdit, source_name(), TicketError, TicketValidationError, find_ticket_file(), InvalidTicket (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 17 - "Community 17"
Cohesion: 0.08
Nodes (4): keep_for(), anonymise(), logged_in(), test_real_run_creates_a_file_and_is_denied_python()

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (17): ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, _clean(), code(), escape_closing_tag(), fenced() (+9 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 20 - "Community 20"
Cohesion: 0.15
Nodes (40): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml(), test_bad_slug_is_refused() (+32 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (15): DaemonNotRunning, init(), serve(), validate_project(), version(), load_or_create_token(), read_token(), token_path() (+7 more)

### Community 22 - "Community 22"
Cohesion: 0.06
Nodes (37): description, engines, node, license, name, packageManager, private, type (+29 more)

### Community 23 - "Community 23"
Cohesion: 0.17
Nodes (30): LocalIntegrator, commit_file(), git(), hooked(), call(), kinds(), _linking(), local() (+22 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (34): ensure_clean(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes(), test_default_branch_sha() (+26 more)

### Community 25 - "Community 25"
Cohesion: 0.12
Nodes (25): RunRegistry, Hooked, crashed_run(), lock_is_free(), status(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree(), test_current_lists_the_phase_lines() (+17 more)

### Community 26 - "Community 26"
Cohesion: 0.10
Nodes (13): ArtifactName, AttemptStatus, Event, EventKind, RunStatus, Usage, recover_interrupted(), encode_payload() (+5 more)

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (26): _assistant(), failing(), _init(), _result(), Transcripts, kinds(), log_of(), phases() (+18 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (18): dumper(), loader(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap() (+10 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (33): build_implementer_prompt(), fixture_inputs(), fixture_ticket(), big_docs(), big_spec(), gate_output(), gate_retry(), test_attempt_kind_is_validated() (+25 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (26): _clean_line(), commit_message(), branch(), git_out(), head(), _squash(), _stage_link(), test_advance_fast_forwards_the_checked_out_branch() (+18 more)

### Community 31 - "Community 31"
Cohesion: 0.10
Nodes (14): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+6 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (21): build_argv(), child_env(), sandbox_settings(), with_config_dir(), parent_env(), settings_json(), test_api_billing_keeps_only_the_api_key(), test_argv_is_exactly_the_documented_command_line() (+13 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (25): editor_command(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores(), test_edit_interrupted_restores() (+17 more)

### Community 35 - "Community 35"
Cohesion: 0.10
Nodes (14): clock(), gate_result(), make_loop(), make(), ManualClock, Merging, project(), registry() (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.16
Nodes (14): show_command(), all_command(), _base(), _call(), cancel_command(), _client(), _current_run_id(), discard_command() (+6 more)

### Community 37 - "Community 37"
Cohesion: 0.12
Nodes (10): _blocks(), epoch_to_datetime(), _int(), keep_end(), summarize(), _usage_counts(), usd_to_micro(), RateLimit (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.11
Nodes (14): ProjectError, ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate() (+6 more)

### Community 39 - "Community 39"
Cohesion: 0.11
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (17): on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact(), attempt(), run_log() (+9 more)

### Community 41 - "Community 41"
Cohesion: 0.11
Nodes (14): allowed_env(), check_gate_command(), gate_env(), split_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused() (+6 more)

### Community 42 - "Community 42"
Cohesion: 0.12
Nodes (13): Agents, Budget, check_slug(), Commands, ContextSettings, GatesSettings, GateTimeouts, GitSettings (+5 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (15): state_db_path(), seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts() (+7 more)

### Community 44 - "Community 44"
Cohesion: 0.11
Nodes (15): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+7 more)

### Community 45 - "Community 45"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (10): resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when(), _not_run() (+2 more)

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (8): HoldForIntegration, IntegrationStatus, Integrator, Agents, Current, EndKind, Flags, record_phase()

### Community 48 - "Community 48"
Cohesion: 0.13
Nodes (13): _branch_of(), finish(), recover_integrations(), _set_run(), _get(), Integration, IntegrationState, open_integrations() (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.16
Nodes (23): validate_plan(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once(), test_critical_path_skips_done_tickets(), test_critical_path_ties_prefer_lower_ids(), test_cycle_starts_at_its_lowest_id_wherever_the_walk_enters() (+15 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (19): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion(), Health (+11 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (14): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, WorktreeInfo, WorktreeState, branches(), real() (+6 more)

### Community 52 - "Community 52"
Cohesion: 0.14
Nodes (11): FakeGates, main(), _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped() (+3 more)

### Community 53 - "Community 53"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 54 - "Community 54"
Cohesion: 0.11
Nodes (8): parse_done_when(), DoneItem, TicketMeta, test_done_when_heading_variants(), test_done_when_ignores_code_fences(), test_done_when_items(), test_empty_done_when_is_a_warning(), test_parse_ticket_parts()

### Community 55 - "Community 55"
Cohesion: 0.14
Nodes (11): client(), clock(), free_port(), git_repo(), home(), isolated_git(), projects_dir(), run_client() (+3 more)

### Community 56 - "Community 56"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 57 - "Community 57"
Cohesion: 0.12
Nodes (5): ApiClient, ApiError, _detail(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401()

### Community 58 - "Community 58"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 61 - "Community 61"
Cohesion: 0.17
Nodes (14): sort_tickets(), explain_idle(), IdleReason, _ids(), next_ready(), _statuses(), _unmet(), waiting_on() (+6 more)

### Community 62 - "Community 62"
Cohesion: 0.15
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket(), test_template_is_in_the_built_wheel()

### Community 63 - "Community 63"
Cohesion: 0.14
Nodes (14): assert_snapshot(), block(), fixture_text(), read_text(), base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries() (+6 more)

### Community 64 - "Community 64"
Cohesion: 0.13
Nodes (7): id_key(), PlanError, PlanProblem, SchedulerError, _and_list(), _find_cycles(), sort_ids()

### Community 65 - "Community 65"
Cohesion: 0.13
Nodes (3): _Session, _signal_group(), _stream()

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (14): home_denials(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket(), test_extra_stack_commands_are_allowed(), test_read_only_git_follows_stack_commands() (+6 more)

### Community 67 - "Community 67"
Cohesion: 0.18
Nodes (11): require_valid(), critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours(), summary() (+3 more)

### Community 68 - "Community 68"
Cohesion: 0.25
Nodes (16): fake_tool_cmd(), gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+8 more)

### Community 69 - "Community 69"
Cohesion: 0.15
Nodes (6): config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings

### Community 70 - "Community 70"
Cohesion: 0.13
Nodes (7): clean(), _Log, ProcessResult, run_process(), _signal_group(), _stop_tree(), test_clean_strips_ansi_and_crlf()

### Community 71 - "Community 71"
Cohesion: 0.10
Nodes (7): agents_command(), describe(), describe(), make_runner(), review_command(), available_runners(), test_claude_code_cli_is_the_only_backend()

### Community 72 - "Community 72"
Cohesion: 0.16
Nodes (13): cap_excerpt(), keep_head(), keep_newest_entries(), _lines(), select_spec(), _total(), Trimmed, words() (+5 more)

### Community 73 - "Community 73"
Cohesion: 0.17
Nodes (10): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_dir(), _statements(), _user_version() (+2 more)

### Community 74 - "Community 74"
Cohesion: 0.14
Nodes (7): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_next_follows_the_run_to_its_end(), test_status_of_an_active_run(), test_status_with_no_run()

### Community 75 - "Community 75"
Cohesion: 0.17
Nodes (5): _deps(), edit_command(), list_command(), set_status_command(), show_command()

### Community 76 - "Community 76"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 77 - "Community 77"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 78 - "Community 78"
Cohesion: 0.34
Nodes (17): copy_dashboard(), make_project(), set_status(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files(), test_check_valid_plan(), test_next_on_the_dashboard() (+9 more)

### Community 79 - "Community 79"
Cohesion: 0.15
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 80 - "Community 80"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 81 - "Community 81"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 82 - "Community 82"
Cohesion: 0.16
Nodes (5): merge(), parse(), read(), to_node(), write_atomic()

### Community 83 - "Community 83"
Cohesion: 0.18
Nodes (11): TransitionError, check_transition(), parse_status(), test_allowed_transitions_pass(), test_disallowed_transition_messages(), test_disallowed_transitions_raise(), test_running_from_blocked_also_waits_for_dependencies(), test_running_needs_a_valid_plan() (+3 more)

### Community 84 - "Community 84"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 85 - "Community 85"
Cohesion: 0.25
Nodes (11): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+3 more)

### Community 86 - "Community 86"
Cohesion: 0.15
Nodes (3): default_agents(), health(), Health

### Community 87 - "Community 87"
Cohesion: 0.16
Nodes (5): table(), _cost(), list_command(), show_command(), _tokens()

### Community 88 - "Community 88"
Cohesion: 0.20
Nodes (7): DependencyView, GateFailure, PreviousAttempt, RenderedPrompt, RepoDocs, ReviewNote, TicketView

### Community 89 - "Community 89"
Cohesion: 0.23
Nodes (7): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_serve_refuses_while_another_daemon_holds_the_lock(), test_startup_recovers_and_skips_a_corrupt_database(), test_startup_without_a_projects_folder_serves()

### Community 90 - "Community 90"
Cohesion: 0.18
Nodes (4): configure_logging(), JsonFormatter, PlainFormatter, _Redactor

### Community 91 - "Community 91"
Cohesion: 0.29
Nodes (6): auth(), follow(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_refusals_carry_the_message(), test_run_through_the_api_merges_into_main()

### Community 92 - "Community 92"
Cohesion: 0.23
Nodes (8): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 93 - "Community 93"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 94 - "Community 94"
Cohesion: 0.22
Nodes (6): create_app(), lifespan(), check_git(), recover_all_integrations(), recover_all_worktrees(), test_create_app_uses_token_file()

### Community 96 - "Community 96"
Cohesion: 0.41
Nodes (8): fake(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items(), test_unfinished_run_exits_2()

### Community 97 - "Community 97"
Cohesion: 0.24
Nodes (6): test_init_existing_folder(), test_init_reports_every_problem(), test_init_then_validate(), test_init_with_branch_and_remote(), test_validate_missing_project(), test_validate_prints_every_error()

### Community 98 - "Community 98"
Cohesion: 0.30
Nodes (8): apply_transition(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 99 - "Community 99"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 100 - "Community 100"
Cohesion: 0.33
Nodes (6): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder()

### Community 101 - "Community 101"
Cohesion: 0.33
Nodes (5): log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token(), test_reconfiguring_replaces_handlers()

### Community 102 - "Community 102"
Cohesion: 0.24
Nodes (3): start(), test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 103 - "Community 103"
Cohesion: 0.36
Nodes (8): test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401(), test_version_without_token_is_401()

### Community 104 - "Community 104"
Cohesion: 0.22
Nodes (8): _id_sort_key(), list_tickets(), test_bad_project_name(), test_dashboard_filters(), test_dashboard_plan_loads(), test_missing_project(), test_project_without_tickets_folder(), test_unknown_status_filter()

### Community 105 - "Community 105"
Cohesion: 0.25
Nodes (4): test_client_connection_refused(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 108 - "Community 108"
Cohesion: 0.25
Nodes (3): repo(), set_identity(), test_real_review_names_the_missing_test()

### Community 109 - "Community 109"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 112 - "Community 112"
Cohesion: 0.43
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 113 - "Community 113"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 114 - "Community 114"
Cohesion: 0.48
Nodes (3): manager(), wt_repo(), wt_root()

### Community 115 - "Community 115"
Cohesion: 0.43
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 116 - "Community 116"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 118 - "Community 118"
Cohesion: 0.47
Nodes (3): main(), make_stubs(), parse()

### Community 120 - "Community 120"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 121 - "Community 121"
Cohesion: 0.47
Nodes (3): is_test(), main(), oversized()

### Community 123 - "Community 123"
Cohesion: 0.50
Nodes (3): next_kind(), AttemptKind, test_next_kind()

## Knowledge Gaps
- **19 isolated node(s):** `spoolhq`, `spoolhq-desktop`, `Config`, `InvalidRequest`, `NotRunning` (+14 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1154 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **73 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 4` to `Community 12`, `Community 13`, `Community 17`, `Community 23`, `Community 25`, `Community 26`, `Community 27`, `Community 33`, `Community 39`, `Community 40`, `Community 43`, `Community 47`, `Community 48`, `Community 89`, `Community 92`, `Community 102`, `Community 111`, `Community 119`, `Community 123`, `Community 124`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `RunLog` (e.g. with `Attempt` and `AttemptKind`) actually correct?**
  _`RunLog` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `spoolhq`, `spoolhq-desktop`, `Config` to the rest of the system?**
  _19 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05710162853019996 - nodes in this community are weakly interconnected._
- **Why does `WorktreeManager` connect `Community 10` to `Community 2`, `Community 3`, `Community 9`, `Community 12`, `Community 77`, `Community 14`, `Community 47`, `Community 48`, `Community 17`, `Community 112`, `Community 51`, `Community 114`, `Community 30`, `Community 25`, `Community 92`, `Community 94`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05163511187607573 - nodes in this community are weakly interconnected._