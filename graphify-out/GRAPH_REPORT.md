# Graph Report - Project_Manager  (2026-10-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3789 nodes · 10636 edges · 230 communities (123 shown, 107 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 959 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `51ce519e`
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
- Community 106
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
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 135
- Community 136
- Community 137
- Community 139
- Community 141
- Community 215
- Community 216

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 138 edges
2. `WorktreeManager` - 81 edges
3. `run_git()` - 70 edges
4. `ClaudeStreamParser` - 69 edges
5. `AgentPolicy` - 63 edges
6. `Transcripts` - 48 edges
7. `FakeRunner` - 48 edges
8. `build_implementer_prompt()` - 47 edges
9. `load_project()` - 47 edges
10. `RunLoop` - 43 edges

## Surprising Connections (you probably didn't know these)
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/runloop/test_integration.py → daemon/src/spoolhq/services/git/runner.py
- `esc()` --calls--> `escape_closing_tag()`  [INFERRED]
  daemon/src/spoolhq/services/planner/prompt.py → daemon/src/spoolhq/services/context/render.py
- `test_publish_completes_while_a_subscriber_never_reads()` --indirect_call--> `stuck()`  [INFERRED]
  daemon/tests/services/runs/test_bus.py → daemon/tests/services/git/test_recovery.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 5-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (230 total, 107 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (53): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), keep_end(), summarize(), _usage_counts(), usd_to_micro() (+45 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (24): weighted_tokens(), _Session, _signal_group(), check_worktree(), existing_stubs(), expand_home(), permission_modes(), _remove_empty_tree() (+16 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (37): capture(), agent_stopped(), attempt_once(), check_resolved(), commit(), drive(), _git(), implement() (+29 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (14): test_client_connection_refused(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon(), test_serve_starts_and_serves_docs(), wait_for_health(), main(), make_stubs() (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (38): _header(), _path(), _split_files(), trim_diff(), _gate_word(), _items(), render_review_prompt(), review() (+30 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (45): RunLog, test_startup_recovers_and_skips_a_corrupt_database(), raw(), run_log(), test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise() (+37 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (53): load_ticket(), errors_for(), make_project(), replace_line(), save_and_read(), test_assignment_is_validated(), test_bad_file_name(), test_bad_project_name() (+45 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (16): HoldForIntegration, IntegrationStatus, Integrator, active_message(), take_run_lock(), Agents, Current, EndKind (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (35): FakeRunner, ReviewInputs, test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run() (+27 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (23): disabled_hooks_path(), check_ticket_id(), slugify(), branch_name(), has_local_branch(), is_branch_name(), is_work_tree(), MissingBranchError (+15 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (19): TicketEdit, source_name(), TicketError, TicketValidationError, TicketMeta, find_ticket_file(), _id_sort_key(), InvalidTicket (+11 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (37): default_branch_sha(), ensure_clean(), ensure_no_operation_in_progress(), status_entries(), GitResult, fake_version(), run_git(), start_conflicting_merge() (+29 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (36): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text(), big_docs() (+28 more)

### Community 13 - "Community 13"
Cohesion: 0.09
Nodes (16): next_kind(), AttemptKind, AttemptStatus, Event, EventKind, RunKind, RunStatus, Usage (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (5): _set_run(), attempt_dir_name(), _check_count(), Attempt, Run

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 16 - "Community 16"
Cohesion: 0.18
Nodes (28): LocalIntegrator, RunRegistry, git(), hooked(), call(), kinds(), _linking(), log_of() (+20 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (25): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree(), test_current_lists_the_phase_lines() (+17 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (25): advance(), checked_out(), commit(), conclude_merge(), conflict_files(), create_tag(), ensure_main_ready(), _git() (+17 more)

### Community 20 - "Community 20"
Cohesion: 0.15
Nodes (40): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml(), test_bad_slug_is_refused() (+32 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (15): DaemonNotRunning, serve(), load_or_create_token(), read_token(), token_path(), config_path(), default_projects_dir(), default_worktrees_dir() (+7 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (18): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+10 more)

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (37): description, engines, node, license, name, packageManager, private, type (+29 more)

### Community 24 - "Community 24"
Cohesion: 0.13
Nodes (36): git_executable(), run_git(), branches(), make_read_only(), marker(), real(), registered_paths(), sha() (+28 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (7): marker_key(), _norm(), RegisteredWorktree, same_path(), Worktree, WorktreeManager, test_session_keep_leaves_the_worktree()

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (19): _branch_of(), finish(), _hint(), last_merged(), recover_integrations(), tag_name(), _get(), Integration (+11 more)

### Community 27 - "Community 27"
Cohesion: 0.10
Nodes (27): editor_command(), run_editor(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment() (+19 more)

### Community 28 - "Community 28"
Cohesion: 0.18
Nodes (30): read_record(), Recorder, run(), runner(), test_api_key_billing_passes_the_key_and_the_budget(), test_billing_follows_the_auth_method(), test_claude_config_dir_reaches_the_settings(), test_default_permission_mode_from_env_scrub_is_accepted() (+22 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (11): settings(), describe(), make_runner(), review_command(), GateLine, ItemVerdict, ReviewResult, _ignore() (+3 more)

### Community 30 - "Community 30"
Cohesion: 0.09
Nodes (18): dumper(), loader(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap() (+10 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (5): RunLoop, Active, NotFoundError, RunLoopError, user_errors()

### Community 32 - "Community 32"
Cohesion: 0.08
Nodes (16): commit_file(), _assistant(), clock(), gate_result(), _init(), make_loop(), make(), ManualClock (+8 more)

### Community 33 - "Community 33"
Cohesion: 0.10
Nodes (23): build_argv(), child_env(), sandbox_settings(), AgentPolicy, test_policy_fields_are_untouched_by_credentials_list(), test_unusable_backend_raises_before_starting(), parent_env(), settings_json() (+15 more)

### Community 34 - "Community 34"
Cohesion: 0.11
Nodes (16): InvalidPlan, PlanOutput, _kept(), esc(), render_planner_prompt(), draft_file_name(), Existing, check_plan() (+8 more)

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (16): EventBus, FixedClock, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get() (+8 more)

### Community 36 - "Community 36"
Cohesion: 0.10
Nodes (20): cap_excerpt(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total() (+12 more)

### Community 37 - "Community 37"
Cohesion: 0.13
Nodes (29): validate_plan(), explain_idle(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once(), test_critical_path_skips_done_tickets(), test_critical_path_ties_prefer_lower_ids() (+21 more)

### Community 38 - "Community 38"
Cohesion: 0.14
Nodes (24): plan_transcript(), _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing() (+16 more)

### Community 39 - "Community 39"
Cohesion: 0.10
Nodes (14): _read(), show_command(), ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, GateFailure (+6 more)

### Community 40 - "Community 40"
Cohesion: 0.11
Nodes (12): PlannerError, PlanResult, generate_plan(), finish(), _ignore(), read_spec(), approve_plan(), load_existing() (+4 more)

### Community 41 - "Community 41"
Cohesion: 0.17
Nodes (13): all_command(), _base(), _call(), cancel_command(), _client(), _current_run_id(), discard_command(), _follow() (+5 more)

### Community 42 - "Community 42"
Cohesion: 0.15
Nodes (24): is_junk(), is_secret(), _matches(), branch(), git_out(), head(), _squash(), _stage_link() (+16 more)

### Community 43 - "Community 43"
Cohesion: 0.11
Nodes (15): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_db_path(), state_dir(), _statements() (+7 more)

### Community 44 - "Community 44"
Cohesion: 0.27
Nodes (24): failing(), Transcripts, kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth() (+16 more)

### Community 45 - "Community 45"
Cohesion: 0.12
Nodes (14): ProjectError, ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate() (+6 more)

### Community 46 - "Community 46"
Cohesion: 0.20
Nodes (18): approve_plan(), generate_plan(), _plans(), cancel_run(), current_run(), discard_ticket(), _errors(), integrate_ticket() (+10 more)

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 48 - "Community 48"
Cohesion: 0.09
Nodes (12): _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines(), _previous_vars(), _PromptLoader, PromptTemplate (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (15): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+7 more)

### Community 50 - "Community 50"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 51 - "Community 51"
Cohesion: 0.15
Nodes (10): resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when(), _not_run() (+2 more)

### Community 52 - "Community 52"
Cohesion: 0.13
Nodes (13): client(), clock(), free_port(), git_repo(), home(), isolated_git(), plan_project(), projects_dir() (+5 more)

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (19): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion(), Health (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.11
Nodes (7): create_app(), lifespan(), default_agents(), check_git(), keep_for(), recover_all_integrations(), recover_all_worktrees()

### Community 55 - "Community 55"
Cohesion: 0.12
Nodes (9): fail(), table(), _cost(), list_command(), _run_log(), show_command(), _tokens(), _workspace() (+1 more)

### Community 56 - "Community 56"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.12
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.14
Nodes (13): Agents, Budget, check_slug(), Commands, ContextSettings, GatesSettings, GateTimeouts, GitSettings (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 60 - "Community 60"
Cohesion: 0.16
Nodes (12): hours(), check_command(), describe_plan(), _invalid_lines(), _listing(), next_command(), _path_line(), _plan_failed() (+4 more)

### Community 61 - "Community 61"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 62 - "Community 62"
Cohesion: 0.12
Nodes (9): billing_for(), ClaudeCliRunner, format_version(), parse_version(), fake_probe(), test_auth_status_that_is_not_json(), test_linux_needs_bubblewrap_and_socat(), test_macos_is_enforceable_and_others_are_not() (+1 more)

### Community 63 - "Community 63"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.13
Nodes (10): clean_title(), _not_blank(), one_line(), PlannedTicket, parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_one_line_drops_control_and_format_characters() (+2 more)

### Community 66 - "Community 66"
Cohesion: 0.19
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 67 - "Community 67"
Cohesion: 0.15
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket(), test_template_is_in_the_built_wheel()

### Community 68 - "Community 68"
Cohesion: 0.17
Nodes (10): FakeGates, _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state() (+2 more)

### Community 69 - "Community 69"
Cohesion: 0.12
Nodes (6): _stream(), merge(), parse(), read(), to_node(), write_atomic()

### Community 70 - "Community 70"
Cohesion: 0.20
Nodes (14): home_denials(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket(), test_extra_stack_commands_are_allowed(), test_read_only_git_follows_stack_commands() (+6 more)

### Community 71 - "Community 71"
Cohesion: 0.18
Nodes (11): require_valid(), critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours(), summary() (+3 more)

### Community 72 - "Community 72"
Cohesion: 0.15
Nodes (9): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket(), test_status_of_an_active_run() (+1 more)

### Community 73 - "Community 73"
Cohesion: 0.25
Nodes (16): fake_tool_cmd(), gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+8 more)

### Community 74 - "Community 74"
Cohesion: 0.12
Nodes (9): allowed_env(), check_gate_command(), gate_env(), split_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused() (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.15
Nodes (7): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState

### Community 76 - "Community 76"
Cohesion: 0.14
Nodes (7): id_key(), PlanError, PlanProblem, SchedulerError, _and_list(), _find_cycles(), sort_ids()

### Community 77 - "Community 77"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 78 - "Community 78"
Cohesion: 0.14
Nodes (11): parse_done_when(), DoneItem, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants(), test_done_when_ignores_code_fences() (+3 more)

### Community 79 - "Community 79"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 80 - "Community 80"
Cohesion: 0.16
Nodes (5): ApiClient, ApiError, _detail(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401()

### Community 81 - "Community 81"
Cohesion: 0.16
Nodes (7): DirtyRepoError, OperationInProgressError, RepoNotReadyError, _result(), _waiting(), IntegrationResult, integrate()

### Community 82 - "Community 82"
Cohesion: 0.17
Nodes (5): _deps(), edit_command(), list_command(), set_status_command(), show_command()

### Community 83 - "Community 83"
Cohesion: 0.15
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 85 - "Community 85"
Cohesion: 0.22
Nodes (8): sort_tickets(), IdleReason, _ids(), next_ready(), _statuses(), _unmet(), waiting_on(), Ticket

### Community 86 - "Community 86"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 87 - "Community 87"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 88 - "Community 88"
Cohesion: 0.20
Nodes (10): parse_worktree_list(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+2 more)

### Community 89 - "Community 89"
Cohesion: 0.18
Nodes (11): TransitionError, check_transition(), parse_status(), test_allowed_transitions_pass(), test_disallowed_transition_messages(), test_disallowed_transitions_raise(), test_running_from_blocked_also_waits_for_dependencies(), test_running_needs_a_valid_plan() (+3 more)

### Community 90 - "Community 90"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 91 - "Community 91"
Cohesion: 0.25
Nodes (11): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+3 more)

### Community 93 - "Community 93"
Cohesion: 0.18
Nodes (9): test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401() (+1 more)

### Community 95 - "Community 95"
Cohesion: 0.23
Nodes (7): auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template()

### Community 96 - "Community 96"
Cohesion: 0.17
Nodes (4): health(), version(), Health, Version

### Community 97 - "Community 97"
Cohesion: 0.22
Nodes (9): ProcessResult, run_process(), _signal_group(), _stop_tree(), alive(), run(), test_invalid_utf8_and_crlf_are_cleaned_in_the_log(), test_output_cap_cuts_the_log_and_drains_the_process() (+1 more)

### Community 98 - "Community 98"
Cohesion: 0.22
Nodes (8): apply_transition(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 99 - "Community 99"
Cohesion: 0.33
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 100 - "Community 100"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 101 - "Community 101"
Cohesion: 0.27
Nodes (10): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning() (+2 more)

### Community 102 - "Community 102"
Cohesion: 0.23
Nodes (8): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 103 - "Community 103"
Cohesion: 0.22
Nodes (7): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install(), use(), fake_claude_cmd(), sandbox_which()

### Community 104 - "Community 104"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 105 - "Community 105"
Cohesion: 0.18
Nodes (4): main(), start(), test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 106 - "Community 106"
Cohesion: 0.31
Nodes (6): auth(), follow(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_refusals_carry_the_message(), test_run_through_the_api_merges_into_main()

### Community 107 - "Community 107"
Cohesion: 0.33
Nodes (9): make_plan(), test_a_failed_write_leaves_the_old_files(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members(), test_approving_twice_gives_nothing_to_approve() (+1 more)

### Community 108 - "Community 108"
Cohesion: 0.37
Nodes (7): jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once(), test_one_plan_per_project_at_a_time()

### Community 109 - "Community 109"
Cohesion: 0.21
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 110 - "Community 110"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 111 - "Community 111"
Cohesion: 0.22
Nodes (3): init(), validate_project(), version()

### Community 112 - "Community 112"
Cohesion: 0.22
Nodes (3): clean(), _Log, test_clean_strips_ansi_and_crlf()

### Community 113 - "Community 113"
Cohesion: 0.33
Nodes (6): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder()

### Community 114 - "Community 114"
Cohesion: 0.24
Nodes (4): agents_command(), describe(), available_runners(), test_claude_code_cli_is_the_only_backend()

### Community 116 - "Community 116"
Cohesion: 0.22
Nodes (5): _clean_line(), commit_message(), test_control_characters_are_removed(), test_progress_note_is_wrapped_at_72(), test_untrusted_title_becomes_one_line_of_at_most_72()

### Community 117 - "Community 117"
Cohesion: 0.43
Nodes (3): GeneratePlan, PlanApproved, PlanStarted

### Community 119 - "Community 119"
Cohesion: 0.25
Nodes (5): _clear_read_only_and_retry(), remove_path(), test_list_worktrees_reports_each_state(), test_remove_path_handles_files_and_symlinks(), test_resume_needs_the_folder_and_the_marker()

### Community 120 - "Community 120"
Cohesion: 0.43
Nodes (6): test_init_existing_folder(), test_init_reports_every_problem(), test_init_then_validate(), test_init_with_branch_and_remote(), test_validate_missing_project(), test_validate_prints_every_error()

### Community 121 - "Community 121"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 125 - "Community 125"
Cohesion: 0.48
Nodes (3): manager(), wt_repo(), wt_root()

### Community 126 - "Community 126"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 128 - "Community 128"
Cohesion: 0.47
Nodes (3): policy(), user_home(), worktree()

### Community 130 - "Community 130"
Cohesion: 0.33
Nodes (3): test_session_teardown_failure_keeps_the_original_error(), broken(), test_teardown_deletes_the_folder_when_git_cannot()

### Community 132 - "Community 132"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 133 - "Community 133"
Cohesion: 0.47
Nodes (3): is_test(), main(), oversized()

### Community 136 - "Community 136"
Cohesion: 0.40
Nodes (3): done_when_items(), render_draft(), test_a_title_that_needs_quotes_stays_valid_yaml()

## Knowledge Gaps
- **145 isolated node(s):** `CopyState`, `RetryProps`, `DaemonReply`, `RawDaemonInfo`, `class-variance-authority` (+140 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1270 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **107 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 5` to `Community 2`, `Community 131`, `Community 7`, `Community 13`, `Community 14`, `Community 16`, `Community 17`, `Community 26`, `Community 31`, `Community 35`, `Community 40`, `Community 43`, `Community 44`, `Community 54`, `Community 55`, `Community 84`, `Community 100`, `Community 102`, `Community 105`, `Community 122`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `Community 25` to `Community 1`, `Community 130`, `Community 7`, `Community 9`, `Community 11`, `Community 19`, `Community 24`, `Community 26`, `Community 42`, `Community 54`, `Community 55`, `Community 75`, `Community 79`, `Community 84`, `Community 88`, `Community 102`, `Community 109`, `Community 119`, `Community 125`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `run_git()` connect `Community 24` to `Community 3`, `Community 4`, `Community 11`, `Community 16`, `Community 17`, `Community 19`, `Community 32`, `Community 42`, `Community 44`, `Community 52`, `Community 68`, `Community 72`, `Community 79`, `Community 88`, `Community 98`, `Community 99`, `Community 102`, `Community 106`, `Community 119`, `Community 125`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `RunLog` (e.g. with `Attempt` and `AttemptKind`) actually correct?**
  _`RunLog` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `ClaudeStreamParser` (e.g. with `ClaudeCliRunner` and `_Session`) actually correct?**
  _`ClaudeStreamParser` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CopyState`, `RetryProps`, `DaemonReply` to the rest of the system?**
  _145 weakly-connected nodes found - possible documentation gaps or missing edges._