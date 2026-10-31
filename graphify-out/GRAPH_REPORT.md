# Graph Report - Project_Manager  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 5320 nodes · 14577 edges · 345 communities (161 shown, 184 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1143 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `01dd791c`
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
- Community 134
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
- Community 153
- Community 154
- Community 155
- Community 156
- Community 157
- Community 158
- Community 159
- Community 160
- Community 161
- Community 162
- Community 163
- Community 164
- Community 165
- Community 166
- Community 167
- Community 168
- Community 169
- Community 170
- Community 171
- Community 172
- Community 173
- Community 174
- Community 175
- Community 176
- Community 177
- Community 178
- Community 180
- Community 184
- Community 188
- Community 330
- Community 331
- Community 332

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 87 edges
2. `WorktreeManager` - 78 edges
3. `load_project()` - 73 edges
4. `AgentPolicy` - 68 edges
5. `ClaudeStreamParser` - 62 edges
6. `run_git()` - 55 edges
7. `FakeRunner` - 54 edges
8. `run_git()` - 49 edges
9. `build_implementer_prompt()` - 48 edges
10. `load_ticket()` - 45 edges

## Surprising Connections (you probably didn't know these)
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/runloop/test_integration.py → daemon/src/spoolhq/services/git/runner.py
- `integrate()` --calls--> `IntegrationResult`  [INFERRED]
  daemon/tests/services/runloop/test_loop.py → daemon/src/spoolhq/services/runloop/integrator.py
- `sdk()` --calls--> `AgentSdkRunner`  [INFERRED]
  daemon/tests/services/runloop/test_model.py → daemon/src/spoolhq/services/agents/agent_sdk.py
- `codex()` --calls--> `CodexCliRunner`  [INFERRED]
  daemon/tests/services/runloop/test_model.py → daemon/src/spoolhq/services/agents/codex_cli.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/delivery.py -> daemon/src/spoolhq/services/runloop/approval.py`
- 3-file cycle: `daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/integration.py -> daemon/src/spoolhq/services/runloop/approval.py`
- 3-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/polling.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/delivery.py -> daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/integration.py -> daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runloop/approval.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/delivery.py -> daemon/src/spoolhq/services/runloop/integration.py -> daemon/src/spoolhq/services/runloop/approval.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (345 total, 184 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (47): ChangedFile, parse_numstat(), staged_changes(), is_ancestor(), tag_exists(), branch_name(), delete_branch(), _network() (+39 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (18): format_version(), parse_version(), platform_reason(), probe(), BackendInfo, Budget, RunResult, Session (+10 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (50): LocalIntegrator, bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice() (+42 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (50): api_key(), ask_hook(), main(), parse(), receive(), run(), send(), write_file() (+42 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (47): build_argv(), install_dir(), permission_profile(), _toml(), with_codex_home(), assert_refused(), read_only(), read_record() (+39 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (50): advance(), checked_out(), commit(), commit_message(), conclude_merge(), conflict_files(), ensure_main_ready(), _git() (+42 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (18): weighted_tokens(), permission_modes(), keep_end(), PolicyViolation, CodexStreamParser, _int(), check_command(), FileEdit (+10 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (27): format_errors(), write_atomic(), parse_done_when(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError (+19 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (7): Project, reject(), _waiting(), RunLoop, NotFoundError, RunLoopError, user_errors()

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (27): create_tag(), fetch(), github_repo(), _branch_of(), finish(), last_merged(), publish_tag(), recover_integrations() (+19 more)

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (28): client(), clock(), fake_backend(), fake_claude_cmd(), fake_codex_cmd(), fake_sdk_cmd(), FixedClock, fixture_contract() (+20 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (55): load_ticket(), save_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated() (+47 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (16): check_ticket_id(), branch_sha(), command_error(), GitResult, BranchConflictError, marker_key(), _norm(), parse_worktree_list() (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (15): HoldForIntegration, IntegrationResult, IntegrationStatus, Integrator, active_message(), take_run_lock(), Active, Agents (+7 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (41): ClaudeStreamParser, assistant(), load(), parse(), replay(), result(), test_accepted_modes_can_be_widened_by_the_adapter(), test_acting_before_init_is_a_violation() (+33 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (39): default_branch_sha(), DirtyRepoError, ensure_clean(), ensure_no_operation_in_progress(), MissingBranchError, operation_in_progress(), OperationInProgressError, RepoNotReadyError (+31 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (14): fail(), settings(), table(), _client(), _cost(), list_command(), _policy(), _run_log() (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.09
Nodes (27): sync(), approve_plan(), generate_plan(), _plans(), approve_ticket(), cancel_run(), current_run(), discard_ticket() (+19 more)

### Community 18 - "Community 18"
Cohesion: 0.06
Nodes (44): dependencies, react, react-dom, engines, node, name, packageManager, private (+36 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (42): git_executable(), WorktreeManager, run_git(), branches(), make_read_only(), marker(), real(), registered_paths() (+34 more)

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (5): _check_count(), RunLog, Attempt, AttemptKind, Run

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (11): AgentSdkRunner, billing_for(), build_argv(), check_worktree(), existing_stubs(), expand_home(), _remove_empty_tree(), remove_new_stubs() (+3 more)

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (16): AttemptStatus, EventKind, RunKind, RunStatus, record_policy(), open_pull_requests(), set_pull_request(), recover_interrupted() (+8 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (28): approval_message(), approve(), decide(), read_artifact(), _user_approved(), as_record(), _compile(), delivery_mode() (+20 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (38): GateFailure, build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text() (+30 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 26 - "Community 26"
Cohesion: 0.06
Nodes (15): allowed_env(), policy_parts(), billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), child_env(), policy_parts() (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (37): AgentPolicy, assert_gone(), endpoint_runner(), read_record(), run(), runner(), test_a_custom_endpoint_never_gets_the_users_login(), test_a_remote_endpoint_without_a_token_is_refused() (+29 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (24): describe_source(), _clear_read_only_and_retry(), remove_path(), CheckResult, load_contract(), TemplateContract, TemplateError, check_safe() (+16 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (41): load_project(), del_path(), errors_for(), set_path(), test_a_template_must_be_a_block(), test_all_errors_are_reported_at_once(), test_bad_protected_path_patterns_are_refused(), test_bad_repo_in_yaml() (+33 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (28): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+20 more)

### Community 31 - "Community 31"
Cohesion: 0.07
Nodes (17): cap_excerpt(), ContextBudgetError, ContextError, PromptTemplateError, _clean(), code(), escape_closing_tag(), fenced() (+9 more)

### Community 32 - "Community 32"
Cohesion: 0.09
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 33 - "Community 33"
Cohesion: 0.09
Nodes (35): PlanProblem, _and_list(), validate_plan(), test_real_plan_for_a_small_cli_tool_validates(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once() (+27 more)

### Community 34 - "Community 34"
Cohesion: 0.11
Nodes (22): _find_cycles(), require_valid(), sort_ids(), sort_tickets(), critical_path(), CriticalPath, _hours(), PlanSummary (+14 more)

### Community 35 - "Community 35"
Cohesion: 0.15
Nodes (17): GitHubPoller, fake(), FakeGitHub, git(), leaks(), log_of(), start(), status() (+9 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (29): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+21 more)

### Community 37 - "Community 37"
Cohesion: 0.09
Nodes (19): check_command(), check_path(), check_tool(), make_hook(), pre_tool_use(), relative_pattern(), policy(), user_home() (+11 more)

### Community 38 - "Community 38"
Cohesion: 0.07
Nodes (13): auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template(), anonymise() (+5 more)

### Community 39 - "Community 39"
Cohesion: 0.06
Nodes (5): billing_error(), CliTransport, SdkRun, stop(), test_billing_errors_are_recognised()

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (16): Agents, BackendSettings, Budget, _check_base_url(), check_github_url(), Commands, ContextSettings, GatesSettings (+8 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (18): agent_stopped(), attempt_once(), check_resolved(), commit(), drive(), _git(), implement(), integrate() (+10 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (15): hours(), approve_command(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner() (+7 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (27): keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total(), Trimmed (+19 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (18): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, holder(), lock_path(), LockHeld, _read_pid(), _try_lock() (+10 more)

### Community 45 - "Community 45"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 46 - "Community 46"
Cohesion: 0.14
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _current_run_id(), discard_command() (+7 more)

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 48 - "Community 48"
Cohesion: 0.08
Nodes (11): dump(), loader(), merge(), parse(), read(), to_plain(), _message(), parse_contract() (+3 more)

### Community 49 - "Community 49"
Cohesion: 0.08
Nodes (9): create_app(), lifespan(), health(), Health, check_git(), keep_for(), recover_all_integrations(), recover_all_worktrees() (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.10
Nodes (15): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState, branches() (+7 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (16): App(), root, createItem(), getItem(), listItems(), Item, NewItem, ItemList() (+8 more)

### Community 52 - "Community 52"
Cohesion: 0.21
Nodes (25): failing(), kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt() (+17 more)

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (16): dumper(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node(), parse_yaml() (+8 more)

### Community 54 - "Community 54"
Cohesion: 0.10
Nodes (11): init(), serve(), validate_project(), version(), load_or_create_token(), read_token(), token_path(), test_empty_token_file_is_replaced() (+3 more)

### Community 55 - "Community 55"
Cohesion: 0.17
Nodes (24): ReviewInputs, OutcomeRunner, run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages(), test_cancelled_is_passed_through() (+16 more)

### Community 56 - "Community 56"
Cohesion: 0.10
Nodes (18): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+10 more)

### Community 57 - "Community 57"
Cohesion: 0.13
Nodes (18): on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact(), attempt() (+10 more)

### Community 58 - "Community 58"
Cohesion: 0.12
Nodes (12): _assistant(), clock(), _init(), make_loop(), make(), project(), registry(), repo() (+4 more)

### Community 60 - "Community 60"
Cohesion: 0.13
Nodes (14): id_key(), InvalidPlan, PlanOutput, render_planner_prompt(), Existing, check_plan(), CheckedPlan, _id_errors() (+6 more)

### Community 61 - "Community 61"
Cohesion: 0.11
Nodes (8): _blocks(), epoch_to_datetime(), _int(), summarize(), _usage_counts(), usd_to_micro(), test_epoch_conversion(), test_usd_conversion_is_exact()

### Community 62 - "Community 62"
Cohesion: 0.14
Nodes (16): GitHubClient, GitHubError, create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull() (+8 more)

### Community 63 - "Community 63"
Cohesion: 0.10
Nodes (17): PlanError, SchedulerError, TransitionError, apply_transition(), check_transition(), parse_status(), TransitionResult, copy_dashboard() (+9 more)

### Community 64 - "Community 64"
Cohesion: 0.12
Nodes (27): test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_cache_reads_count_a_tenth_toward_weighted_tokens(), test_empty_folder_left_by_an_uncommitted_attempt_is_reused(), test_ended_run_takes_no_attempts(), test_event_with_an_attempt_of_another_run_is_refused() (+19 more)

### Community 65 - "Community 65"
Cohesion: 0.14
Nodes (17): adapter(), AdapterCase, agent_sdk(), claude_cli(), codex_cli(), fake(), run(), record() (+9 more)

### Community 66 - "Community 66"
Cohesion: 0.11
Nodes (19): child_env(), sandbox_settings(), parent_env(), settings_json(), test_a_custom_endpoint_gets_spoolhqs_token_and_no_login(), test_api_billing_keeps_only_the_api_key(), test_argv_is_exactly_the_documented_command_line(), test_child_env_is_an_allowlist() (+11 more)

### Community 67 - "Community 67"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 68 - "Community 68"
Cohesion: 0.11
Nodes (10): ApiClient, ApiError, DaemonNotRunning, _detail(), test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host() (+2 more)

### Community 69 - "Community 69"
Cohesion: 0.11
Nodes (16): ProjectValidationError, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate(), project_dir(), save_project() (+8 more)

### Community 70 - "Community 70"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 71 - "Community 71"
Cohesion: 0.11
Nodes (9): endpoint_token(), keyring_key(), missing_token(), token_var(), test_real_agent_sdk_run_creates_a_file_and_is_denied_ssh(), test_a_local_endpoint_gets_the_dummy(), test_a_remote_endpoint_uses_the_environment_then_the_keychain(), test_an_unreadable_keychain_means_no_token() (+1 more)

### Community 72 - "Community 72"
Cohesion: 0.12
Nodes (8): Merging, codex_review(), set_roles(), test_a_ticket_runs_end_to_end_on_codex(), codex(), test_a_ticket_runs_end_to_end_on_the_agent_sdk(), sdk(), test_each_role_starts_its_own_backend()

### Community 73 - "Community 73"
Cohesion: 0.08
Nodes (8): set_command(), sync_command(), _read(), show_command(), describe(), make_runner(), review_command(), store_api_key()

### Community 74 - "Community 74"
Cohesion: 0.15
Nodes (10): resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when(), _not_run() (+2 more)

### Community 75 - "Community 75"
Cohesion: 0.12
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 76 - "Community 76"
Cohesion: 0.16
Nodes (10): FakeGates, _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state() (+2 more)

### Community 77 - "Community 77"
Cohesion: 0.11
Nodes (10): GateLine, ItemVerdict, ReviewResult, _gate_word(), _ignore(), _items(), render_review_prompt(), review() (+2 more)

### Community 78 - "Community 78"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 79 - "Community 79"
Cohesion: 0.17
Nodes (14): init(), test_a_copier_failure_is_reported(), test_a_failed_commit_removes_the_repo_and_workspace(), test_a_failed_workspace_empties_an_existing_folder(), test_a_file_as_repo_is_refused(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_non_empty_folder_is_refused_and_untouched() (+6 more)

### Community 80 - "Community 80"
Cohesion: 0.15
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 81 - "Community 81"
Cohesion: 0.24
Nodes (21): parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason() (+13 more)

### Community 82 - "Community 82"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 83 - "Community 83"
Cohesion: 0.18
Nodes (15): denials_except(), home_denials(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket(), test_extra_stack_commands_are_allowed() (+7 more)

### Community 84 - "Community 84"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 85 - "Community 85"
Cohesion: 0.18
Nodes (3): _hint(), _result(), waiting_message()

### Community 87 - "Community 87"
Cohesion: 0.15
Nodes (6): get_settings(), get_engine(), make_engine(), run(), url(), test_migrations_create_and_drop_the_schema()

### Community 88 - "Community 88"
Cohesion: 0.33
Nodes (11): decisions(), log_of(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note(), test_each_rule_alone_needs_a_person(), test_failing_gates_never_ask_the_reviewer_or_the_policy(), test_hold_mode_with_a_remote_waits_locally_then_opens_a_pr() (+3 more)

### Community 89 - "Community 89"
Cohesion: 0.17
Nodes (15): is_git_url(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder(), test_a_local_git_repository_at_a_ref() (+7 more)

### Community 90 - "Community 90"
Cohesion: 0.11
Nodes (4): version(), Version, _is_api_path(), LocalOnlyMiddleware

### Community 91 - "Community 91"
Cohesion: 0.15
Nodes (9): slugify(), PlannerError, approve_plan(), draft_file_name(), load_existing(), _recorded(), _replace_all(), sha256() (+1 more)

### Community 92 - "Community 92"
Cohesion: 0.14
Nodes (11): FakeRunner, test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file() (+3 more)

### Community 93 - "Community 93"
Cohesion: 0.13
Nodes (10): _header(), _path(), _split_files(), trim_diff(), inputs(), worktree(), file_diff(), test_headers_alone_over_the_limit_still_fit() (+2 more)

### Community 94 - "Community 94"
Cohesion: 0.13
Nodes (10): store_endpoint_token(), github_token(), store_github_token(), MemoryKeyring, test_store(), test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token() (+2 more)

### Community 95 - "Community 95"
Cohesion: 0.16
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 96 - "Community 96"
Cohesion: 0.13
Nodes (11): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+3 more)

### Community 97 - "Community 97"
Cohesion: 0.15
Nodes (7): config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), ensure_home(), home_dir(), Settings

### Community 98 - "Community 98"
Cohesion: 0.13
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 99 - "Community 99"
Cohesion: 0.16
Nodes (11): ContextInputs, DependencyView, PreviousAttempt, RenderedPrompt, RepoDocs, ReviewNote, TicketView, implementer_prompt() (+3 more)

### Community 100 - "Community 100"
Cohesion: 0.13
Nodes (6): _clean_line(), clean_title(), _not_blank(), one_line(), PlannedTicket, check_slug()

### Community 101 - "Community 101"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 102 - "Community 102"
Cohesion: 0.18
Nodes (12): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_a_huge_body_is_capped(), test_md_escape() (+4 more)

### Community 103 - "Community 103"
Cohesion: 0.13
Nodes (5): ResumeTimer, ManualClock, test_cancel_and_close_drop_the_schedule(), test_fires_once_at_reset_plus_a_minute(), test_the_polling_thread_fires_and_a_failing_callback_is_logged()

### Community 104 - "Community 104"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 105 - "Community 105"
Cohesion: 0.25
Nodes (16): fake_tool_cmd(), gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+8 more)

### Community 106 - "Community 106"
Cohesion: 0.21
Nodes (5): ahead_message(), Delivery, _failed(), _held(), pr_branch()

### Community 107 - "Community 107"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 108 - "Community 108"
Cohesion: 0.16
Nodes (16): state_db_path(), state_dir(), raw(), test_closed_log_refuses_calls(), test_daemon_instance_must_not_be_empty(), test_fresh_database_has_version_7_and_all_tables(), test_naive_clock_raises(), test_newer_schema_is_refused() (+8 more)

### Community 109 - "Community 109"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 110 - "Community 110"
Cohesion: 0.16
Nodes (5): _deps(), edit_command(), list_command(), set_status_command(), show_command()

### Community 111 - "Community 111"
Cohesion: 0.13
Nodes (9): check_gate_command(), gate_env(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused() (+1 more)

### Community 112 - "Community 112"
Cohesion: 0.22
Nodes (8): test_backends_are_separated_by_a_blank_line(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_lists_the_installed_backend(), test_nothing_installed_says_how_to_install(), test_project_warns_about_a_codex_reviewer(), test_the_agent_sdk_shows_its_versions_the_key_and_the_parts(), use()

### Community 113 - "Community 113"
Cohesion: 0.16
Nodes (9): test_health(), make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped() (+1 more)

### Community 114 - "Community 114"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 115 - "Community 115"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 116 - "Community 116"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 117 - "Community 117"
Cohesion: 0.18
Nodes (6): generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 118 - "Community 118"
Cohesion: 0.21
Nodes (11): test_init_existing_folder(), test_init_reports_every_problem(), test_init_template_ref_needs_a_template(), test_init_then_validate(), test_init_with_a_bad_template_creates_nothing(), test_init_with_a_git_template_prints_the_commit_first(), test_init_with_a_git_template_runs_no_global_git_hooks(), test_init_with_a_local_template() (+3 more)

### Community 119 - "Community 119"
Cohesion: 0.20
Nodes (8): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements(), _user_version(), test_timestamps_are_utc_with_milliseconds()

### Community 120 - "Community 120"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 121 - "Community 121"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 122 - "Community 122"
Cohesion: 0.26
Nodes (7): auth(), follow(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_refusals_carry_the_message(), test_run_through_the_api_merges_into_main()

### Community 123 - "Community 123"
Cohesion: 0.18
Nodes (9): test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401() (+1 more)

### Community 124 - "Community 124"
Cohesion: 0.28
Nodes (8): plan_transcript(), jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once(), test_one_plan_per_project_at_a_time()

### Community 125 - "Community 125"
Cohesion: 0.22
Nodes (9): ProcessResult, run_process(), _signal_group(), _stop_tree(), alive(), run(), test_invalid_utf8_and_crlf_are_cleaned_in_the_log(), test_output_cap_cuts_the_log_and_drains_the_process() (+1 more)

### Community 126 - "Community 126"
Cohesion: 0.16
Nodes (4): dotted_path(), _message(), _model_at(), _number()

### Community 127 - "Community 127"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 128 - "Community 128"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 129 - "Community 129"
Cohesion: 0.18
Nodes (7): ClaudeCliRunner, fake_probe(), test_auth_status_that_is_not_json(), test_linux_needs_bubblewrap_and_socat(), test_macos_is_enforceable_and_others_are_not(), test_native_windows_is_refused(), test_real_run_creates_a_file_and_is_denied_python()

### Community 130 - "Community 130"
Cohesion: 0.16
Nodes (5): PlanResult, generate_plan(), finish(), _ignore(), read_spec()

### Community 131 - "Community 131"
Cohesion: 0.22
Nodes (5): create_app(), client(), test_session(), engine(), session()

### Community 132 - "Community 132"
Cohesion: 0.29
Nodes (5): Base, Item, create_item(), get_item(), list_items()

### Community 133 - "Community 133"
Cohesion: 0.22
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 134 - "Community 134"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 135 - "Community 135"
Cohesion: 0.15
Nodes (4): agents_command(), describe(), describe_roles(), describe_worktrees()

### Community 137 - "Community 137"
Cohesion: 0.18
Nodes (4): main(), start(), test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 138 - "Community 138"
Cohesion: 0.33
Nodes (9): make_plan(), test_a_failed_write_leaves_the_old_files(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members(), test_approving_twice_gives_nothing_to_approve() (+1 more)

### Community 139 - "Community 139"
Cohesion: 0.23
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 140 - "Community 140"
Cohesion: 0.18
Nodes (5): consistency_errors(), InvalidVerdict, _location(), ParsedItem, ParsedVerdict

### Community 141 - "Community 141"
Cohesion: 0.20
Nodes (7): available_runners(), backend_names(), make_runner(), _check_backend(), test_codex_takes_the_endpoint_and_model(), test_the_agent_sdk_takes_the_endpoint_and_model(), test_the_built_in_backends()

### Community 142 - "Community 142"
Cohesion: 0.29
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 143 - "Community 143"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 144 - "Community 144"
Cohesion: 0.24
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 145 - "Community 145"
Cohesion: 0.22
Nodes (3): clean(), _Log, test_clean_strips_ansi_and_crlf()

### Community 146 - "Community 146"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 147 - "Community 147"
Cohesion: 0.25
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 148 - "Community 148"
Cohesion: 0.33
Nodes (6): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder()

### Community 149 - "Community 149"
Cohesion: 0.20
Nodes (3): print_run(), check_command(), list_command()

### Community 150 - "Community 150"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 154 - "Community 154"
Cohesion: 0.50
Nodes (6): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 155 - "Community 155"
Cohesion: 0.25
Nodes (3): Recorder, test_cancel(), test_unexpected_tool_in_init_stops_the_run()

### Community 156 - "Community 156"
Cohesion: 0.39
Nodes (6): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_one_line_drops_control_and_format_characters(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 158 - "Community 158"
Cohesion: 0.32
Nodes (3): Settings, test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 159 - "Community 159"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 162 - "Community 162"
Cohesion: 0.29
Nodes (4): done_when_items(), render_draft(), to_node(), test_a_title_that_needs_quotes_stays_valid_yaml()

### Community 163 - "Community 163"
Cohesion: 0.29
Nodes (4): _fail_after_yaml(), test_failed_rename_leaves_nothing(), test_failure_mid_init_leaves_nothing(), test_missing_git_is_reported()

### Community 165 - "Community 165"
Cohesion: 0.29
Nodes (4): run_log(), test_committed_events_are_published_in_order(), test_concurrent_appends_get_increasing_ids(), test_failed_insert_publishes_nothing()

### Community 166 - "Community 166"
Cohesion: 0.43
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 167 - "Community 167"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 169 - "Community 169"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 170 - "Community 170"
Cohesion: 0.33
Nodes (3): bare(), someone_pushes(), token()

### Community 171 - "Community 171"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **190 isolated node(s):** `CopyState`, `RetryProps`, `DaemonReply`, `RawDaemonInfo`, `eslint` (+185 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1857 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **184 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ClaudeStreamParser` connect `Community 14` to `Community 1`, `Community 129`, `Community 66`, `Community 6`, `Community 39`, `Community 21`, `Community 152`, `Community 61`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `Community 19` to `Community 0`, `Community 5`, `Community 38`, `Community 9`, `Community 12`, `Community 109`, `Community 16`, `Community 49`, `Community 50`, `Community 113`, `Community 144`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `RunLog` connect `Community 20` to `Community 9`, `Community 10`, `Community 137`, `Community 16`, `Community 22`, `Community 23`, `Community 160`, `Community 44`, `Community 174`, `Community 175`, `Community 49`, `Community 183`, `Community 184`, `Community 57`, `Community 59`, `Community 75`, `Community 108`, `Community 113`, `Community 127`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `RunLog` (e.g. with `Attempt` and `AttemptKind`) actually correct?**
  _`RunLog` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CopyState`, `RetryProps`, `DaemonReply` to the rest of the system?**
  _190 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.041666666666666664 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.04598490048043926 - nodes in this community are weakly interconnected._