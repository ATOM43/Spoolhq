# Graph Report - Project_Manager  (2026-10-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 4843 nodes · 13272 edges · 290 communities (148 shown, 142 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1070 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `01b9a255`
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
- Community 131
- Community 132
- Community 133
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 146
- Community 147
- Community 148
- Community 149
- Community 150
- Community 151
- Community 152
- Community 153
- Community 154
- Community 155
- Community 156
- Community 158
- Community 159
- Community 161
- Community 162
- Community 164
- Community 165
- Community 274
- Community 275
- Community 276

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 89 edges
2. `WorktreeManager` - 78 edges
3. `load_project()` - 73 edges
4. `ClaudeStreamParser` - 64 edges
5. `run_git()` - 58 edges
6. `run_git()` - 50 edges
7. `RunLoop` - 49 edges
8. `build_implementer_prompt()` - 48 edges
9. `load_ticket()` - 45 edges
10. `FakeRunner` - 44 edges

## Surprising Connections (you probably didn't know these)
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/runloop/test_integration.py → daemon/src/spoolhq/services/git/runner.py
- `integrate()` --calls--> `IntegrationResult`  [INFERRED]
  daemon/tests/services/runloop/test_loop.py → daemon/src/spoolhq/services/runloop/integrator.py
- `test_detect()` --calls--> `FakeRunner`  [INFERRED]
  daemon/tests/services/agents/test_fake.py → daemon/src/spoolhq/services/agents/fake.py
- `test_installed_git_is_new_enough()` --calls--> `check_git_version()`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/delivery.py -> daemon/src/spoolhq/services/runloop/approval.py`
- 3-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/integration.py -> daemon/src/spoolhq/services/runloop/approval.py`
- 3-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/polling.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/delivery.py -> daemon/src/spoolhq/services/runloop/integration.py -> daemon/src/spoolhq/services/runloop/approval.py`
- 4-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/delivery.py -> daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/integration.py -> daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (290 total, 142 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (66): check_ticket_id(), ChangedFile, parse_numstat(), staged_changes(), advance(), checked_out(), commit(), conclude_merge() (+58 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (22): Project, HoldForIntegration, IntegrationResult, IntegrationStatus, Integrator, active_message(), take_run_lock(), RunLoop (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (27): attempt_dir_name(), _check_count(), _make_attempt_dir(), RunLog, AttemptKind, AttemptStatus, Event, EventKind (+19 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (58): billing_for(), ClaudeCliRunner, format_version(), parse_version(), assert_gone(), fake_probe(), read_record(), Recorder (+50 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (19): fail(), settings(), table(), _client(), _cost(), list_command(), _policy(), _run_log() (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (39): agent_stopped(), attempt_once(), check_resolved(), commit(), drive(), _git(), implement(), on_raw() (+31 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (27): create_tag(), _branch_of(), finish(), _hint(), last_merged(), publish_tag(), recover_integrations(), _result() (+19 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (20): GitHubClient, GitHubError, _message(), create_pull(), get_pull(), _list(), list_review_comments(), list_reviews() (+12 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (55): load_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated(), test_bad_file_name() (+47 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (25): client(), clock(), fake_backend(), fake_claude_cmd(), FixedClock, fixture_contract(), free_port(), git_identity() (+17 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (16): lifespan(), check_git(), keep_for(), recover_all_integrations(), recover_all_worktrees(), RecoveryReport, _check_not_newer(), connect() (+8 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (49): init_project(), load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_all_errors_are_reported_at_once() (+41 more)

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (27): ResumeTimer, ManualClock, bare(), crash_at(), delivery(), git(), log_of(), mate() (+19 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (21): approve_plan(), run_editor(), start_edit(), TicketEdit, source_name(), TicketError, TicketValidationError, find_ticket_file() (+13 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (25): PlanError, PlanProblem, SchedulerError, TransitionError, _find_cycles(), require_valid(), sort_ids(), sort_tickets() (+17 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (44): dependencies, react, react-dom, engines, node, name, packageManager, private (+36 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (25): remove_path(), CheckResult, _check_command(), load_contract(), _message(), parse_contract(), TemplateContract, TemplateError (+17 more)

### Community 17 - "Community 17"
Cohesion: 0.06
Nodes (22): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+14 more)

### Community 18 - "Community 18"
Cohesion: 0.06
Nodes (14): _Session, _signal_group(), _stream(), check_worktree(), existing_stubs(), expand_home(), permission_modes(), _remove_empty_tree() (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (40): ClaudeStreamParser, assistant(), load(), parse(), replay(), result(), test_accepted_modes_can_be_widened_by_the_adapter(), test_acting_before_init_is_a_violation() (+32 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (29): allowed_env(), build_argv(), child_env(), AgentPolicy, parent_env(), settings_json(), test_api_billing_keeps_only_the_api_key(), test_argv_is_exactly_the_documented_command_line() (+21 more)

### Community 21 - "Community 21"
Cohesion: 0.16
Nodes (29): LocalIntegrator, git(), hooked(), call(), kinds(), _linking(), local(), log_of() (+21 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (38): GateFailure, build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text() (+30 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (40): git_executable(), run_git(), branches(), make_read_only(), marker(), real(), registered_paths(), sha() (+32 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (10): marker_key(), _norm(), RegisteredWorktree, same_path(), Worktree, WorktreeManager, WorktreeSession, test_commit_refuses_an_empty_message() (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (36): ensure_clean(), status_entries(), GitResult, fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids() (+28 more)

### Community 27 - "Community 27"
Cohesion: 0.10
Nodes (39): _and_list(), validate_plan(), check_transition(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once(), test_allowed_transitions_pass() (+31 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 29 - "Community 29"
Cohesion: 0.09
Nodes (28): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+20 more)

### Community 30 - "Community 30"
Cohesion: 0.10
Nodes (37): raw(), run_log(), test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_cache_reads_count_a_tenth_toward_weighted_tokens(), test_closed_log_refuses_calls() (+29 more)

### Community 31 - "Community 31"
Cohesion: 0.14
Nodes (26): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree(), test_current_lists_the_phase_lines() (+18 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (30): ConfigError, load_settings(), test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token() (+22 more)

### Community 33 - "Community 33"
Cohesion: 0.11
Nodes (29): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+21 more)

### Community 34 - "Community 34"
Cohesion: 0.16
Nodes (17): GitHubPoller, fake(), FakeGitHub, git(), leaks(), log_of(), start(), status() (+9 more)

### Community 35 - "Community 35"
Cohesion: 0.10
Nodes (15): PolicyViolation, BackendInfo, Budget, FileEdit, Message, PermissionDenied, RateLimit, RunResult (+7 more)

### Community 36 - "Community 36"
Cohesion: 0.07
Nodes (10): ApiClient, ApiError, DaemonNotRunning, _detail(), test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host() (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.07
Nodes (14): cap_excerpt(), _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines(), _previous_vars(), _PromptLoader (+6 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (15): hours(), approve_command(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner() (+7 more)

### Community 39 - "Community 39"
Cohesion: 0.09
Nodes (18): dumper(), loader(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap() (+10 more)

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (25): FakeRunner, ReviewInputs, test_each_review_is_its_own_run(), run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages() (+17 more)

### Community 42 - "Community 42"
Cohesion: 0.14
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _current_run_id(), discard_command() (+7 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (16): App(), root, createItem(), getItem(), listItems(), Item, NewItem, ItemList() (+8 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (25): commit_file(), branch(), git_out(), head(), _squash(), _stage_link(), test_advance_fast_forwards_the_checked_out_branch(), test_advance_refuses_a_dirty_checkout() (+17 more)

### Community 45 - "Community 45"
Cohesion: 0.10
Nodes (11): clock(), FakeGates, gate_result(), make_loop(), make(), Merging, project(), registry() (+3 more)

### Community 46 - "Community 46"
Cohesion: 0.13
Nodes (25): editor_command(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores(), test_edit_interrupted_restores() (+17 more)

### Community 47 - "Community 47"
Cohesion: 0.10
Nodes (18): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.09
Nodes (11): is_test(), main(), oversized(), test_serve_starts_and_serves_docs(), wait_for_health(), main(), make_stubs(), parse() (+3 more)

### Community 49 - "Community 49"
Cohesion: 0.10
Nodes (12): ProjectError, ProjectValidationError, InitResult, list_workspaces(), _populate(), project_dir(), save_project(), template_description() (+4 more)

### Community 50 - "Community 50"
Cohesion: 0.25
Nodes (23): failing(), kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt() (+15 more)

### Community 51 - "Community 51"
Cohesion: 0.10
Nodes (14): approval_message(), approve(), decide(), read_artifact(), reject(), _user_approved(), _waiting(), as_record() (+6 more)

### Community 52 - "Community 52"
Cohesion: 0.11
Nodes (10): _blocks(), epoch_to_datetime(), _int(), keep_end(), summarize(), _usage_counts(), usd_to_micro(), Outcome (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.12
Nodes (12): init(), serve(), validate_project(), version(), load_or_create_token(), read_token(), token_path(), ensure_home() (+4 more)

### Community 54 - "Community 54"
Cohesion: 0.10
Nodes (12): _read(), show_command(), ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, PreviousAttempt (+4 more)

### Community 55 - "Community 55"
Cohesion: 0.09
Nodes (15): backend_names(), BackendSettings, _check_backend(), _check_base_url(), Commands, ContextSettings, GatesSettings, GateTimeouts (+7 more)

### Community 56 - "Community 56"
Cohesion: 0.11
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 57 - "Community 57"
Cohesion: 0.10
Nodes (11): parse_done_when(), DoneItem, TicketMeta, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants() (+3 more)

### Community 58 - "Community 58"
Cohesion: 0.13
Nodes (18): github_repo(), push(), check_github_url(), bare(), git(), _ssh_commands(), test_a_push_behind_the_remote_is_moved_not_forced(), test_a_refused_push_raises_with_the_hook_output() (+10 more)

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 60 - "Community 60"
Cohesion: 0.11
Nodes (10): slugify(), _clean_line(), clean_title(), _not_blank(), one_line(), PlannedTicket, done_when_items(), draft_file_name() (+2 more)

### Community 61 - "Community 61"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 62 - "Community 62"
Cohesion: 0.15
Nodes (10): resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when(), _not_run() (+2 more)

### Community 63 - "Community 63"
Cohesion: 0.13
Nodes (16): commit_message(), _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_control_characters_are_removed() (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.26
Nodes (12): decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note(), test_each_rule_alone_needs_a_person(), test_failing_gates_never_ask_the_reviewer_or_the_policy() (+4 more)

### Community 65 - "Community 65"
Cohesion: 0.15
Nodes (16): check_command(), home_denials(), PolicyError, test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket() (+8 more)

### Community 66 - "Community 66"
Cohesion: 0.12
Nodes (18): keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total(), Trimmed (+10 more)

### Community 67 - "Community 67"
Cohesion: 0.12
Nodes (18): build_excerpt(), take(), clean(), _clip(), failing_tests(), first_failure(), _priority(), split_lines() (+10 more)

### Community 68 - "Community 68"
Cohesion: 0.11
Nodes (10): GateLine, ItemVerdict, ReviewResult, _gate_word(), _ignore(), _items(), render_review_prompt(), review() (+2 more)

### Community 69 - "Community 69"
Cohesion: 0.16
Nodes (14): init(), test_a_copier_failure_is_reported(), test_a_failed_commit_removes_the_repo_and_workspace(), test_a_failed_workspace_empties_an_existing_folder(), test_a_file_as_repo_is_refused(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_non_empty_folder_is_refused_and_untouched() (+6 more)

### Community 70 - "Community 70"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 71 - "Community 71"
Cohesion: 0.13
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 72 - "Community 72"
Cohesion: 0.24
Nodes (21): parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason() (+13 more)

### Community 73 - "Community 73"
Cohesion: 0.16
Nodes (16): is_git_url(), _is_path(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder() (+8 more)

### Community 75 - "Community 75"
Cohesion: 0.12
Nodes (7): weighted_tokens(), PlannerError, PlanResult, generate_plan(), finish(), _ignore(), read_spec()

### Community 76 - "Community 76"
Cohesion: 0.15
Nodes (14): _recover_one(), recover_worktrees(), RecoveryEntry, parse_worktree_list(), WorktreeInfo, branches(), real(), registered() (+6 more)

### Community 77 - "Community 77"
Cohesion: 0.15
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket(), test_template_is_in_the_built_wheel()

### Community 78 - "Community 78"
Cohesion: 0.13
Nodes (7): store_github_token(), MemoryKeyring, test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins(), test_the_keychain()

### Community 79 - "Community 79"
Cohesion: 0.21
Nodes (9): _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state(), test_dirty_checkout_after_a_cut_off_fast_forward_is_left_alone() (+1 more)

### Community 80 - "Community 80"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 81 - "Community 81"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 82 - "Community 82"
Cohesion: 0.25
Nodes (16): fake_tool_cmd(), gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+8 more)

### Community 83 - "Community 83"
Cohesion: 0.17
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 84 - "Community 84"
Cohesion: 0.15
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 85 - "Community 85"
Cohesion: 0.21
Nodes (5): ahead_message(), Delivery, _failed(), _held(), pr_branch()

### Community 86 - "Community 86"
Cohesion: 0.16
Nodes (6): config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings

### Community 87 - "Community 87"
Cohesion: 0.16
Nodes (9): create_app(), make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped() (+1 more)

### Community 88 - "Community 88"
Cohesion: 0.10
Nodes (5): describe(), print_run(), run_command(), check_command(), list_command()

### Community 89 - "Community 89"
Cohesion: 0.21
Nodes (8): id_key(), InvalidPlan, PlanOutput, Existing, check_plan(), CheckedPlan, _id_errors(), next_id()

### Community 90 - "Community 90"
Cohesion: 0.22
Nodes (15): describe(), RuleHit, change(), decide(), test_a_project_list_replaces_the_default(), test_a_rename_hits_on_either_name(), test_delivery_mode(), test_describe_reads_stored_rules() (+7 more)

### Community 91 - "Community 91"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 92 - "Community 92"
Cohesion: 0.15
Nodes (7): _initial_yaml(), dump(), merge(), parse(), read(), to_node(), write_atomic()

### Community 93 - "Community 93"
Cohesion: 0.15
Nodes (8): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_github_reads_a_hidden_prompt(), test_secrets_set_refuses_other_names_and_empty_tokens(), test_secrets_set_without_a_keychain(), test_tickets_show_the_pull_request()

### Community 94 - "Community 94"
Cohesion: 0.16
Nodes (5): _Log, ProcessResult, run_process(), _signal_group(), _stop_tree()

### Community 95 - "Community 95"
Cohesion: 0.16
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 96 - "Community 96"
Cohesion: 0.39
Nodes (11): approve_ticket(), cancel_run(), current_run(), discard_ticket(), errors(), _loop(), pause_run(), reject_ticket() (+3 more)

### Community 97 - "Community 97"
Cohesion: 0.18
Nodes (8): CurrentRun, Discarded, MergedView, PhaseLine, PolicyView, Reject, RuleHitView, StartRun

### Community 98 - "Community 98"
Cohesion: 0.14
Nodes (8): check_gate_command(), gate_env(), split_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused(), test_unclosed_quote_is_refused()

### Community 99 - "Community 99"
Cohesion: 0.17
Nodes (9): apply_transition(), parse_status(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line() (+1 more)

### Community 100 - "Community 100"
Cohesion: 0.19
Nodes (8): test_health(), auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template()

### Community 101 - "Community 101"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 102 - "Community 102"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 103 - "Community 103"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 104 - "Community 104"
Cohesion: 0.18
Nodes (6): generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 105 - "Community 105"
Cohesion: 0.21
Nodes (11): test_init_existing_folder(), test_init_reports_every_problem(), test_init_template_ref_needs_a_template(), test_init_then_validate(), test_init_with_a_bad_template_creates_nothing(), test_init_with_a_git_template_prints_the_commit_first(), test_init_with_a_git_template_runs_no_global_git_hooks(), test_init_with_a_local_template() (+3 more)

### Community 106 - "Community 106"
Cohesion: 0.15
Nodes (4): sync(), health(), GitHubSync, Health

### Community 107 - "Community 107"
Cohesion: 0.19
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 108 - "Community 108"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 109 - "Community 109"
Cohesion: 0.26
Nodes (7): auth(), follow(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_refusals_carry_the_message(), test_run_through_the_api_merges_into_main()

### Community 111 - "Community 111"
Cohesion: 0.28
Nodes (8): plan_transcript(), jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once(), test_one_plan_per_project_at_a_time()

### Community 112 - "Community 112"
Cohesion: 0.17
Nodes (3): anonymise(), logged_in(), test_real_run_creates_a_file_and_is_denied_python()

### Community 113 - "Community 113"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 114 - "Community 114"
Cohesion: 0.25
Nodes (4): _assistant(), _init(), _result(), Transcripts

### Community 115 - "Community 115"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 116 - "Community 116"
Cohesion: 0.27
Nodes (10): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning() (+2 more)

### Community 117 - "Community 117"
Cohesion: 0.19
Nodes (8): _kept(), esc(), render_planner_prompt(), assert_snapshot(), test_a_project_can_override_the_prompt(), test_template_syntax_and_closing_tags_in_the_spec_are_plain_text(), test_the_prompt_for_the_dashboard_spec(), test_the_prompt_with_kept_tickets_and_a_template()

### Community 118 - "Community 118"
Cohesion: 0.22
Nodes (5): create_app(), client(), test_session(), engine(), session()

### Community 119 - "Community 119"
Cohesion: 0.22
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 120 - "Community 120"
Cohesion: 0.30
Nodes (10): make_plan(), test_a_failed_write_leaves_the_old_files(), test_a_title_that_needs_quotes_stays_valid_yaml(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members() (+2 more)

### Community 121 - "Community 121"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 122 - "Community 122"
Cohesion: 0.22
Nodes (4): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_nothing_installed_says_how_to_install(), use()

### Community 123 - "Community 123"
Cohesion: 0.18
Nodes (3): make_runner(), Agents, main()

### Community 124 - "Community 124"
Cohesion: 0.18
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 125 - "Community 125"
Cohesion: 0.31
Nodes (5): Base, Item, create_item(), get_item(), list_items()

### Community 126 - "Community 126"
Cohesion: 0.17
Nodes (3): describe(), make_runner(), review_command()

### Community 127 - "Community 127"
Cohesion: 0.18
Nodes (5): consistency_errors(), InvalidVerdict, _location(), ParsedItem, ParsedVerdict

### Community 128 - "Community 128"
Cohesion: 0.35
Nodes (6): approve_plan(), generate_plan(), _plans(), GeneratePlan, PlanApproved, PlanStarted

### Community 129 - "Community 129"
Cohesion: 0.17
Nodes (4): agents_command(), describe(), describe_roles(), available_runners()

### Community 130 - "Community 130"
Cohesion: 0.25
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 131 - "Community 131"
Cohesion: 0.29
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 132 - "Community 132"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 133 - "Community 133"
Cohesion: 0.24
Nodes (5): load_existing(), _recorded(), _replace_all(), sha256(), write_plan()

### Community 135 - "Community 135"
Cohesion: 0.27
Nodes (3): get_engine(), get_session(), make_engine()

### Community 136 - "Community 136"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 137 - "Community 137"
Cohesion: 0.33
Nodes (6): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder()

### Community 138 - "Community 138"
Cohesion: 0.20
Nodes (3): test_read_only_log_refuses_writes(), test_read_only_open_of_a_missing_database_creates_nothing(), test_read_only_open_refuses_an_unmigrated_database()

### Community 139 - "Community 139"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 143 - "Community 143"
Cohesion: 0.50
Nodes (5): alive(), run(), test_invalid_utf8_and_crlf_are_cleaned_in_the_log(), test_output_cap_cuts_the_log_and_drains_the_process(), test_timeout_stops_the_whole_process_tree()

### Community 144 - "Community 144"
Cohesion: 0.46
Nodes (5): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 145 - "Community 145"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 147 - "Community 147"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 148 - "Community 148"
Cohesion: 0.48
Nodes (3): manager(), wt_repo(), wt_root()

### Community 150 - "Community 150"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 151 - "Community 151"
Cohesion: 0.40
Nodes (5): state_db_path(), state_dir(), test_runs_of_an_older_database_are_ticket_runs(), test_text_file_is_not_a_spoolhq_database(), test_version_1_database_is_migrated()

### Community 153 - "Community 153"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 155 - "Community 155"
Cohesion: 0.33
Nodes (3): bare(), someone_pushes(), token()

### Community 156 - "Community 156"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 159 - "Community 159"
Cohesion: 0.40
Nodes (3): test_committed_events_are_published_in_order(), test_concurrent_appends_get_increasing_ids(), test_failed_insert_publishes_nothing()

## Knowledge Gaps
- **190 isolated node(s):** `CopyState`, `RetryProps`, `DaemonReply`, `RawDaemonInfo`, `allowImportingTsExtensions` (+185 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1671 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **142 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LocalOnlyMiddleware` connect `Community 110` to `Community 10`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `load_project()` connect `Community 11` to `Community 129`, `Community 1`, `Community 4`, `Community 9`, `Community 10`, `Community 12`, `Community 149`, `Community 21`, `Community 155`, `Community 31`, `Community 34`, `Community 38`, `Community 40`, `Community 45`, `Community 49`, `Community 50`, `Community 53`, `Community 54`, `Community 64`, `Community 69`, `Community 75`, `Community 79`, `Community 83`, `Community 88`, `Community 92`, `Community 104`, `Community 126`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `RunLoop` connect `Community 1` to `Community 96`, `Community 34`, `Community 5`, `Community 166`, `Community 7`, `Community 12`, `Community 50`, `Community 51`, `Community 21`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `RunLog` (e.g. with `Attempt` and `AttemptKind`) actually correct?**
  _`RunLog` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CopyState`, `RetryProps`, `DaemonReply` to the rest of the system?**
  _190 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.03353802550779405 - nodes in this community are weakly interconnected._