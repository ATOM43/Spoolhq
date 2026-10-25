# Graph Report - Project_Manager  (2026-10-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 4186 nodes · 11569 edges · 238 communities (124 shown, 114 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1005 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3e42f8b2`
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
- Community 127
- Community 128
- Community 129
- Community 130
- Community 132
- Community 133
- Community 134
- Community 135
- Community 137
- Community 222
- Community 223
- Community 224

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 138 edges
2. `WorktreeManager` - 81 edges
3. `run_git()` - 71 edges
4. `ClaudeStreamParser` - 69 edges
5. `AgentPolicy` - 63 edges
6. `load_project()` - 54 edges
7. `FakeRunner` - 48 edges
8. `Transcripts` - 48 edges
9. `build_implementer_prompt()` - 47 edges
10. `RunLoop` - 43 edges

## Surprising Connections (you probably didn't know these)
- `test_error_without_stderr_has_no_colon()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_git_error_keeps_the_last_20_stderr_lines()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `test_detect()` --calls--> `FakeRunner`  [INFERRED]
  daemon/tests/services/agents/test_fake.py → daemon/src/spoolhq/services/agents/fake.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 5-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (238 total, 114 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (44): advance(), checked_out(), commit(), conclude_merge(), conflict_files(), create_tag(), ensure_main_ready(), _git() (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (63): _deps(), PlanError, PlanProblem, _and_list(), _find_cycles(), require_valid(), sort_ids(), sort_tickets() (+55 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (53): _force_utf8_streams(), main(), editor_command(), _unquote(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors() (+45 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (49): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (29): id_key(), slugify(), clean_title(), InvalidPlan, PlannerError, PlanOutput, PlanResult, generate_plan() (+21 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (51): state_db_path(), state_dir(), RunLog, test_startup_recovers_and_skips_a_corrupt_database(), FixedClock, raw(), run_log(), test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan() (+43 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (57): load_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated(), test_bad_file_name() (+49 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (25): approve_plan(), generate_plan(), _plans(), cancel_run(), current_run(), discard_ticket(), _errors(), integrate_ticket() (+17 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (37): ConfigError, load_settings(), test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1(), client(), clock() (+29 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (18): allowed_env(), billing_for(), ClaudeCliRunner, format_version(), parse_version(), _Session, _signal_group(), _stream() (+10 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (22): check_ticket_id(), approve_plan(), to_plain(), write_atomic(), run_editor(), start_edit(), TicketEdit, source_name() (+14 more)

### Community 11 - "Community 11"
Cohesion: 0.09
Nodes (49): git_executable(), WorktreeManager, make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project() (+41 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (7): RunLoop, Active, Flags, NotFoundError, record_phase(), RunLoopError, user_errors()

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (8): set_identity(), anonymise(), logged_in(), test_real_run_creates_a_file_and_is_denied_python(), test_real_review_names_the_missing_test(), FakeGates, main(), test_unknown_integration()

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (40): AgentPolicy, assert_gone(), fake_probe(), read_record(), Recorder, run(), runner(), test_api_key_billing_passes_the_key_and_the_budget() (+32 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (24): agent_stopped(), attempt_once(), check_resolved(), commit(), drive(), _git(), implement(), integrate() (+16 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (16): utc_now(), ArtifactName, AttemptStatus, EventKind, RunKind, RunStatus, Usage, recover_interrupted() (+8 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (40): ClaudeStreamParser, assistant(), load(), parse(), replay(), result(), test_accepted_modes_can_be_widened_by_the_adapter(), test_acting_before_init_is_a_violation() (+32 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (21): agents_command(), describe(), weighted_tokens(), available_runners(), BackendInfo, Budget, check_command(), FileEdit (+13 more)

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (17): EventBus, Subscription, Event, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others() (+9 more)

### Community 20 - "Community 20"
Cohesion: 0.06
Nodes (44): dependencies, react, react-dom, engines, node, name, packageManager, private (+36 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (22): _branch_of(), finish(), _hint(), recover_integrations(), _result(), tag_name(), _waiting(), IntegrationResult (+14 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (39): _clean_line(), commit_message(), is_junk(), is_secret(), _matches(), merge_head(), merge_in(), restore_branch() (+31 more)

### Community 23 - "Community 23"
Cohesion: 0.07
Nodes (13): last_merged(), HoldForIntegration, IntegrationStatus, Integrator, active_message(), take_run_lock(), Agents, Current (+5 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (33): build_argv(), child_env(), permission_modes(), home_denials(), parent_env(), settings_json(), test_api_billing_keeps_only_the_api_key(), test_argv_is_exactly_the_documented_command_line() (+25 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (36): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text(), big_docs() (+28 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 27 - "Community 27"
Cohesion: 0.09
Nodes (37): ensure_clean(), status_entries(), check_git_version(), parse_git_version(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it() (+29 more)

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (42): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml() (+34 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (8): marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, same_path(), Worktree, WorktreeSession, test_parse_worktree_list()

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (14): ProcessResult, run_process(), _signal_group(), _stop_tree(), test_serve_starts_and_serves_docs(), wait_for_health(), main(), make_stubs() (+6 more)

### Community 32 - "Community 32"
Cohesion: 0.06
Nodes (19): create_app(), lifespan(), default_agents(), check_git(), keep_for(), recover_all_integrations(), recover_all_worktrees(), test_health() (+11 more)

### Community 33 - "Community 33"
Cohesion: 0.08
Nodes (18): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+10 more)

### Community 34 - "Community 34"
Cohesion: 0.08
Nodes (18): dumper(), merge(), to_node(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap() (+10 more)

### Community 35 - "Community 35"
Cohesion: 0.14
Nodes (25): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree(), test_current_lists_the_phase_lines() (+17 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (29): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+21 more)

### Community 37 - "Community 37"
Cohesion: 0.10
Nodes (10): fail(), settings(), table(), _cost(), list_command(), _run_log(), show_command(), _tokens() (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.21
Nodes (26): LocalIntegrator, RunRegistry, git(), hooked(), call(), kinds(), log_of(), on_first() (+18 more)

### Community 39 - "Community 39"
Cohesion: 0.08
Nodes (12): describe(), make_runner(), review_command(), GateLine, ItemVerdict, ReviewResult, _gate_word(), _ignore() (+4 more)

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 41 - "Community 41"
Cohesion: 0.08
Nodes (14): cap_excerpt(), _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines(), _previous_vars(), _PromptLoader (+6 more)

### Community 42 - "Community 42"
Cohesion: 0.18
Nodes (25): FakeRunner, ReviewInputs, test_each_review_is_its_own_run(), run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages() (+17 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (17): ProjectError, ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate() (+9 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (16): App(), root, createItem(), getItem(), listItems(), Item, NewItem, ItemList() (+8 more)

### Community 45 - "Community 45"
Cohesion: 0.10
Nodes (15): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState, branches() (+7 more)

### Community 46 - "Community 46"
Cohesion: 0.10
Nodes (18): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+10 more)

### Community 47 - "Community 47"
Cohesion: 0.23
Nodes (25): failing(), Merging, Transcripts, kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text() (+17 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (13): remove_path(), check_template(), CheckResult, TemplateError, check_safe(), check_target(), _clean_up(), init_from_template() (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (10): _blocks(), epoch_to_datetime(), _int(), keep_end(), PolicyViolation, summarize(), _usage_counts(), usd_to_micro() (+2 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (14): approve_command(), all_command(), _base(), _call(), cancel_command(), _client(), _current_run_id(), discard_command() (+6 more)

### Community 51 - "Community 51"
Cohesion: 0.10
Nodes (10): ApiClient, ApiError, DaemonNotRunning, _detail(), test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host() (+2 more)

### Community 52 - "Community 52"
Cohesion: 0.11
Nodes (14): hours(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner(), next_command() (+6 more)

### Community 54 - "Community 54"
Cohesion: 0.10
Nodes (11): parse_done_when(), DoneItem, TicketMeta, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants() (+3 more)

### Community 55 - "Community 55"
Cohesion: 0.12
Nodes (19): capture(), on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact() (+11 more)

### Community 56 - "Community 56"
Cohesion: 0.12
Nodes (14): Agents, Budget, check_slug(), Commands, ContextSettings, GatesSettings, GateTimeouts, GitSettings (+6 more)

### Community 57 - "Community 57"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 58 - "Community 58"
Cohesion: 0.16
Nodes (15): auth(), follow(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_refusals_carry_the_message(), test_run_through_the_api_merges_into_main(), fake(), repo() (+7 more)

### Community 59 - "Community 59"
Cohesion: 0.12
Nodes (18): keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total(), Trimmed (+10 more)

### Community 60 - "Community 60"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 61 - "Community 61"
Cohesion: 0.13
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.14
Nodes (12): ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, GateFailure, PreviousAttempt, RenderedPrompt (+4 more)

### Community 63 - "Community 63"
Cohesion: 0.17
Nodes (10): resolve_program(), DoneWhenCheck, GateResult, GateRun, GateStatus, check_done_when(), _not_run(), _run_gate() (+2 more)

### Community 64 - "Community 64"
Cohesion: 0.24
Nodes (21): parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason() (+13 more)

### Community 65 - "Community 65"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 66 - "Community 66"
Cohesion: 0.12
Nodes (6): ResumeTimer, ManualClock, local(), test_cancel_and_close_drop_the_schedule(), test_fires_once_at_reset_plus_a_minute(), test_the_polling_thread_fires_and_a_failing_callback_is_logged()

### Community 67 - "Community 67"
Cohesion: 0.12
Nodes (10): _assistant(), clock(), _init(), make_loop(), make(), project(), registry(), _result() (+2 more)

### Community 68 - "Community 68"
Cohesion: 0.19
Nodes (14): init(), test_a_copier_failure_is_reported(), test_a_failed_commit_removes_the_repo_and_workspace(), test_a_failed_workspace_empties_an_existing_folder(), test_a_file_as_repo_is_refused(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_non_empty_folder_is_refused_and_untouched() (+6 more)

### Community 69 - "Community 69"
Cohesion: 0.19
Nodes (16): parse_plan(), _where(), dashboard_plan(), test_a_title_that_needs_quotes_stays_valid_yaml(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported() (+8 more)

### Community 70 - "Community 70"
Cohesion: 0.14
Nodes (9): _not_blank(), one_line(), PlannedTicket, parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_one_line_drops_control_and_format_characters(), test_text_fields_are_cleaned_to_one_line() (+1 more)

### Community 71 - "Community 71"
Cohesion: 0.15
Nodes (11): SchedulerError, TransitionError, apply_transition(), parse_status(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid() (+3 more)

### Community 72 - "Community 72"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 73 - "Community 73"
Cohesion: 0.25
Nodes (16): fake_tool_cmd(), gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+8 more)

### Community 74 - "Community 74"
Cohesion: 0.18
Nodes (14): is_git_url(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder(), test_a_local_git_work_tree_records_its_head() (+6 more)

### Community 75 - "Community 75"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 76 - "Community 76"
Cohesion: 0.14
Nodes (7): loader(), load_contract(), _message(), parse_contract(), _Strict, TemplateCommands, TemplateContract

### Community 77 - "Community 77"
Cohesion: 0.23
Nodes (10): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+2 more)

### Community 78 - "Community 78"
Cohesion: 0.16
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 79 - "Community 79"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 80 - "Community 80"
Cohesion: 0.12
Nodes (5): test_template_is_in_the_built_wheel(), assert_snapshot(), test_a_project_can_override_the_prompt(), test_template_syntax_and_closing_tags_in_the_spec_are_plain_text(), test_the_prompt_for_the_dashboard_spec()

### Community 81 - "Community 81"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 82 - "Community 82"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 83 - "Community 83"
Cohesion: 0.17
Nodes (6): config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings

### Community 84 - "Community 84"
Cohesion: 0.25
Nodes (9): serve(), load_or_create_token(), read_token(), token_path(), ensure_home(), test_empty_token_file_is_replaced(), test_loose_token_file_mode_is_tightened(), test_token_file_and_home_have_private_modes() (+1 more)

### Community 85 - "Community 85"
Cohesion: 0.18
Nodes (4): edit_command(), list_command(), set_status_command(), show_command()

### Community 86 - "Community 86"
Cohesion: 0.16
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 87 - "Community 87"
Cohesion: 0.20
Nodes (8): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements(), _user_version(), test_timestamps_are_utc_with_milliseconds()

### Community 88 - "Community 88"
Cohesion: 0.21
Nodes (9): _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state(), test_dirty_checkout_after_a_cut_off_fast_forward_is_left_alone() (+1 more)

### Community 89 - "Community 89"
Cohesion: 0.15
Nodes (3): init(), validate_project(), version()

### Community 90 - "Community 90"
Cohesion: 0.16
Nodes (9): check_gate_command(), gate_env(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused() (+1 more)

### Community 91 - "Community 91"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 92 - "Community 92"
Cohesion: 0.25
Nodes (7): auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template()

### Community 93 - "Community 93"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 94 - "Community 94"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 95 - "Community 95"
Cohesion: 0.27
Nodes (10): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning() (+2 more)

### Community 97 - "Community 97"
Cohesion: 0.22
Nodes (7): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install(), use(), fake_claude_cmd(), sandbox_which()

### Community 98 - "Community 98"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 99 - "Community 99"
Cohesion: 0.24
Nodes (5): just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 100 - "Community 100"
Cohesion: 0.15
Nodes (3): describe(), print_run(), run_command()

### Community 101 - "Community 101"
Cohesion: 0.18
Nodes (3): check_command(), describe_source(), list_command()

### Community 102 - "Community 102"
Cohesion: 0.27
Nodes (9): builtin_descriptions(), builtin_names(), builtin_root(), _clone(), _git(), _is_path(), _label(), _local() (+1 more)

### Community 103 - "Community 103"
Cohesion: 0.33
Nodes (9): make_plan(), test_a_failed_write_leaves_the_old_files(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members(), test_approving_twice_gives_nothing_to_approve() (+1 more)

### Community 104 - "Community 104"
Cohesion: 0.37
Nodes (7): jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once(), test_one_plan_per_project_at_a_time()

### Community 105 - "Community 105"
Cohesion: 0.18
Nodes (5): consistency_errors(), InvalidVerdict, _location(), ParsedItem, ParsedVerdict

### Community 106 - "Community 106"
Cohesion: 0.23
Nodes (3): health(), Health, create_app()

### Community 107 - "Community 107"
Cohesion: 0.22
Nodes (3): get_engine(), make_engine(), test_migrations_create_and_drop_the_schema()

### Community 108 - "Community 108"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 109 - "Community 109"
Cohesion: 0.22
Nodes (3): clean(), _Log, test_clean_strips_ansi_and_crlf()

### Community 110 - "Community 110"
Cohesion: 0.24
Nodes (4): model_calls(), test_real_run_implements_and_approves_a_tiny_ticket(), test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 111 - "Community 111"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 112 - "Community 112"
Cohesion: 0.25
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 113 - "Community 113"
Cohesion: 0.33
Nodes (6): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder()

### Community 114 - "Community 114"
Cohesion: 0.27
Nodes (8): test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file(), test_writes_outside_the_worktree_are_skipped()

### Community 115 - "Community 115"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 116 - "Community 116"
Cohesion: 0.47
Nodes (7): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 117 - "Community 117"
Cohesion: 0.47
Nodes (4): Item, create_item(), get_item(), list_items()

### Community 118 - "Community 118"
Cohesion: 0.36
Nodes (4): test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 120 - "Community 120"
Cohesion: 0.36
Nodes (4): client(), test_session(), engine(), session()

### Community 121 - "Community 121"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 126 - "Community 126"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 127 - "Community 127"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 128 - "Community 128"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 129 - "Community 129"
Cohesion: 0.47
Nodes (3): manager(), wt_repo(), wt_root()

### Community 130 - "Community 130"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **190 isolated node(s):** `CopyState`, `RetryProps`, `DaemonReply`, `RawDaemonInfo`, `build` (+185 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1417 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **114 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 5` to `Community 11`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 19`, `Community 21`, `Community 23`, `Community 32`, `Community 35`, `Community 37`, `Community 38`, `Community 47`, `Community 53`, `Community 55`, `Community 93`, `Community 110`, `Community 122`, `Community 125`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `Event` connect `Community 19` to `Community 131`, `Community 5`, `Community 39`, `Community 136`, `Community 9`, `Community 14`, `Community 16`, `Community 18`, `Community 53`, `Community 23`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `ClaudeStreamParser` connect `Community 17` to `Community 131`, `Community 9`, `Community 42`, `Community 141`, `Community 49`, `Community 18`, `Community 24`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `RunLog` (e.g. with `Attempt` and `AttemptKind`) actually correct?**
  _`RunLog` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CopyState`, `RetryProps`, `DaemonReply` to the rest of the system?**
  _190 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.050284031138228484 - nodes in this community are weakly interconnected._