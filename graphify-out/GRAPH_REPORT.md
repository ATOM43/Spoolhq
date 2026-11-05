# Graph Report - Project_Manager  (2026-11-05)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 6274 nodes · 17895 edges · 352 communities (177 shown, 175 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1497 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4e006095`
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
- Community 152
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
- Community 179
- Community 180
- Community 181
- Community 182
- Community 183
- Community 184
- Community 185
- Community 186
- Community 187
- Community 188
- Community 189
- Community 191
- Community 193
- Community 194
- Community 195
- Community 196
- Community 198
- Community 199
- Community 200
- Community 201
- Community 202
- Community 340
- Community 341
- Community 342

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 115 edges
2. `WorktreeManager` - 82 edges
3. `load_project()` - 82 edges
4. `RunRegistry` - 70 edges
5. `AgentPolicy` - 69 edges
6. `FakeRunner` - 68 edges
7. `ClaudeStreamParser` - 61 edges
8. `build_implementer_prompt()` - 57 edges
9. `Run` - 56 edges
10. `RunContext` - 52 edges

## Surprising Connections (you probably didn't know these)
- `schema()` --uses--> `Settings`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/core/config.py
- `schema()` --calls--> `create_app()`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/api/app.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `integrate()` --calls--> `IntegrationResult`  [INFERRED]
  daemon/tests/services/runloop/test_loop.py → daemon/src/spoolhq/services/runloop/integrator.py
- `sdk()` --calls--> `AgentSdkRunner`  [INFERRED]
  daemon/tests/services/runloop/test_model.py → daemon/src/spoolhq/services/agents/agent_sdk.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/polling.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/totals.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (352 total, 175 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (34): approve(), decide(), read_artifact(), reject(), unblock(), _waiting(), _hint(), last_merged() (+26 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (34): agents_command(), describe(), describe_roles(), describe_worktrees(), ApiClient, ApiError, DaemonNotRunning, _detail() (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (27): _kill_tree(), run(), test_serve_accepts_the_event_websocket(), test_serve_starts_and_serves_docs(), wait_for_health(), sandbox_which(), set_identity(), main() (+19 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (64): build_argv(), install_dir(), permission_profile(), _toml(), with_codex_home(), denials_except(), home_denials(), test_read_only_argv_has_only_the_read_tools() (+56 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (49): events(), test_health(), Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token(), close_code(), connect(), emit() (+41 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (48): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), _usage_counts(), usd_to_micro(), assistant(), load() (+40 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (31): policy_parts(), billing_for(), format_version(), parse_version(), platform_reason(), probe(), check_worktree(), existing_stubs() (+23 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (36): ProjectError, ProjectValidationError, EditConflict, Agents, BackendSettings, Budget, _check_base_url(), _check_path_pattern() (+28 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (41): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+33 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (56): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, Ticket, ticketsQuery() (+48 more)

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (59): state_db_path(), state_dir(), seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first() (+51 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (15): _user_approved(), attempt_dir_name(), _check_count(), _make_attempt_dir(), RunLog, Attempt, Run, latest_phase() (+7 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (38): describe_graphify(), _build(), cache_dir(), CodeMap, _current(), _drop(), refresh(), _refresh() (+30 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (24): decode_cursor(), encode_cursor(), page_runs(), RunPage, AttemptStatus, Event, EventKind, RunKind (+16 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (41): dumper(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node(), parse_yaml() (+33 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (47): ProjectDetail, saveSpec(), CurrentRun, useCurrentRun(), PATHS, RunAction, useRunAction(), formatUsage() (+39 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (36): advance(), checked_out(), _clean_line(), commit(), conclude_merge(), conflict_files(), ensure_main_ready(), _git() (+28 more)

### Community 17 - "Community 17"
Cohesion: 0.05
Nodes (30): disabled_hooks_path(), check_ticket_id(), slugify(), branch_name(), _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry (+22 more)

### Community 18 - "Community 18"
Cohesion: 0.06
Nodes (42): ConfigError, load_settings(), _api_routes(), test_bodies_over_1_mb_are_refused(), test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected() (+34 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (45): AgentPolicy, assert_gone(), endpoint_runner(), fake_probe(), read_record(), Recorder, run(), runner() (+37 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (58): list_tickets(), load_ticket(), save_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read() (+50 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (25): tag_exists(), approval_message(), _result(), HoldForIntegration, IntegrationResult, agent_stopped(), attempt_once(), check_resolved() (+17 more)

### Community 22 - "Community 22"
Cohesion: 0.04
Nodes (27): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, HomePage() (+19 more)

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (22): parse_done_when(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError, DoneItem, find_ticket_file() (+14 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (28): id_key(), PlanError, SchedulerError, TransitionError, _find_cycles(), require_valid(), sort_ids(), sort_tickets() (+20 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (19): weighted_tokens(), keep_end(), PolicyViolation, summarize(), CodexStreamParser, _int(), check_command(), FileEdit (+11 more)

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (50): init_project(), load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_all_errors_are_reported_at_once() (+42 more)

### Community 27 - "Community 27"
Cohesion: 0.09
Nodes (44): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text(), test_negative_cap_is_refused() (+36 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (31): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+23 more)

### Community 29 - "Community 29"
Cohesion: 0.06
Nodes (26): create_tag(), is_ancestor(), Project, _branch_of(), finish(), publish_tag(), recover_integrations(), _set_run() (+18 more)

### Community 30 - "Community 30"
Cohesion: 0.06
Nodes (19): github_token(), store_github_token(), delete_secret(), secret_status(), SecretStatus, store_secret(), MemoryKeyring, stored_key() (+11 more)

### Community 31 - "Community 31"
Cohesion: 0.07
Nodes (19): GitHubClient, GitHubError, _message(), create_pull(), get_pull(), _list(), list_review_comments(), list_reviews() (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (29): api_key(), no_parent_key(), test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript(), record(), run() (+21 more)

### Community 33 - "Community 33"
Cohesion: 0.07
Nodes (17): AgentSdkRunner, check_command(), check_path(), check_tool(), make_hook(), relative_pattern(), call_hook(), test_reviewer_and_planner_get_no_write_or_bash() (+9 more)

### Community 34 - "Community 34"
Cohesion: 0.12
Nodes (43): WorktreeManager, test_interrupted_run_keeps_its_worktree(), commit_file(), run_git(), branches(), make_read_only(), marker(), real() (+35 more)

### Community 35 - "Community 35"
Cohesion: 0.05
Nodes (16): EventBus, Subscription, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get() (+8 more)

### Community 36 - "Community 36"
Cohesion: 0.07
Nodes (37): Agents, backendReady(), DaemonSettings, removeSecret(), SecretName, storeSecret(), useDaemonSettings(), useRefreshSecrets() (+29 more)

### Community 37 - "Community 37"
Cohesion: 0.11
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 38 - "Community 38"
Cohesion: 0.08
Nodes (37): ensure_clean(), ensure_no_operation_in_progress(), operation_in_progress(), status_entries(), GitResult, fake_version(), run_git(), start_conflicting_merge() (+29 more)

### Community 39 - "Community 39"
Cohesion: 0.17
Nodes (34): LocalIntegrator, _assistant(), _init(), _result(), Transcripts, git(), hooked(), call() (+26 more)

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (32): pre_tool_use(), fake_backend(), fake_graphify(), free_port(), git_identity(), home(), isolated_git(), keychain() (+24 more)

### Community 41 - "Community 41"
Cohesion: 0.10
Nodes (27): settings(), put(), _conflict(), create_project(), get_project(), get_settings(), get_spec(), list_projects() (+19 more)

### Community 42 - "Community 42"
Cohesion: 0.08
Nodes (39): PlanProblem, _and_list(), validate_plan(), check_transition(), parse_status(), dashboard(), make(), messages() (+31 more)

### Community 43 - "Community 43"
Cohesion: 0.09
Nodes (26): NO_PROJECTS, ProjectsSection(), cn(), buttonVariants, Card(), CardAction(), CardContent(), CardDescription() (+18 more)

### Community 44 - "Community 44"
Cohesion: 0.06
Nodes (42): engines, node, name, packageManager, private, type, version, description (+34 more)

### Community 45 - "Community 45"
Cohesion: 0.07
Nodes (19): clock(), FakeGates, make_loop(), make(), Merging, project(), registry(), repo() (+11 more)

### Community 46 - "Community 46"
Cohesion: 0.07
Nodes (8): marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, same_path(), Worktree, WorktreeSession, test_parse_worktree_list()

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (28): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+20 more)

### Community 48 - "Community 48"
Cohesion: 0.06
Nodes (5): billing_error(), CliTransport, SdkRun, stop(), test_billing_errors_are_recognised()

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (15): loader(), CheckResult, load_contract(), _message(), parse_contract(), TemplateContract, TemplateError, check_safe() (+7 more)

### Community 50 - "Community 50"
Cohesion: 0.07
Nodes (10): available_runners(), make_runner(), billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), test_codex_takes_the_endpoint_and_model(), test_the_agent_sdk_takes_the_endpoint_and_model() (+2 more)

### Community 51 - "Community 51"
Cohesion: 0.10
Nodes (15): hours(), approve_command(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner() (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.08
Nodes (11): create_app(), lifespan(), _openapi(), health(), version(), Health, Version, check_git() (+3 more)

### Community 53 - "Community 53"
Cohesion: 0.11
Nodes (19): on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact(), clock(), FixedClock (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.07
Nodes (12): _cost(), list_command(), _policy(), _run_log(), show_command(), _tokens(), _deps(), edit_command() (+4 more)

### Community 55 - "Community 55"
Cohesion: 0.10
Nodes (14): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+6 more)

### Community 56 - "Community 56"
Cohesion: 0.10
Nodes (21): keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total() (+13 more)

### Community 57 - "Community 57"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 58 - "Community 58"
Cohesion: 0.12
Nodes (25): commit_message(), branch(), git_out(), head(), _squash(), _stage_link(), test_advance_fast_forwards_the_checked_out_branch(), test_advance_refuses_a_dirty_checkout() (+17 more)

### Community 59 - "Community 59"
Cohesion: 0.19
Nodes (24): kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt(), test_changes_requested_three_times_blocks() (+16 more)

### Community 60 - "Community 60"
Cohesion: 0.15
Nodes (28): CommandTestResult, CreateProject, fieldError(), Gate, GATES, loadSettings(), ProjectSettings, saveCommands() (+20 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (18): Delivery, ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note() (+10 more)

### Community 62 - "Community 62"
Cohesion: 0.10
Nodes (21): build_argv(), child_env(), sandbox_settings(), Budget, parent_env(), settings_json(), test_a_custom_endpoint_gets_spoolhqs_token_and_no_login(), test_api_billing_keeps_only_the_api_key() (+13 more)

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (26): FakeRunner, ReviewInputs, test_detect(), test_policy_violation(), run(), test_approve(), test_budget_defaults_and_overrides(), run() (+18 more)

### Community 64 - "Community 64"
Cohesion: 0.10
Nodes (17): ProcessResult, run_process(), _signal_group(), _stop_tree(), set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names() (+9 more)

### Community 65 - "Community 65"
Cohesion: 0.11
Nodes (14): all_command(), approve_command(), _base(), _call(), cancel_command(), _control(), discard_command(), _follow() (+6 more)

### Community 66 - "Community 66"
Cohesion: 0.12
Nodes (22): COALESCE_MS, EventSource, lastSeq, Probe(), subscribe, useProjectEvents(), ProjectSummary, useProject() (+14 more)

### Community 67 - "Community 67"
Cohesion: 0.13
Nodes (17): adapter(), AdapterCase, agent_sdk(), claude_cli(), codex_cli(), fake(), run(), record() (+9 more)

### Community 68 - "Community 68"
Cohesion: 0.09
Nodes (17): BODIES, invokeMock, apiError(), createDemo(), GET, Handler, openDialog(), POST (+9 more)

### Community 69 - "Community 69"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 70 - "Community 70"
Cohesion: 0.08
Nodes (14): cap_excerpt(), _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines(), _previous_vars(), _PromptLoader (+6 more)

### Community 71 - "Community 71"
Cohesion: 0.07
Nodes (8): describe(), print_run(), run_command(), init(), validate_project(), check_command(), describe_source(), list_command()

### Community 72 - "Community 72"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 73 - "Community 73"
Cohesion: 0.13
Nodes (14): ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, GateFailure, PreviousAttempt, RenderedPrompt (+6 more)

### Community 74 - "Community 74"
Cohesion: 0.12
Nodes (12): PlannerError, PlanResult, generate_plan(), finish(), _ignore(), read_spec(), approve_plan(), load_existing() (+4 more)

### Community 75 - "Community 75"
Cohesion: 0.25
Nodes (15): service_errors(), approve_ticket(), cancel_run(), current_run(), discard_ticket(), get_run(), _loop(), pause_run() (+7 more)

### Community 76 - "Community 76"
Cohesion: 0.15
Nodes (10): get_ticket(), get_tickets(), put_ticket(), _read(), unblock_ticket(), InvalidTicketView, Note, TicketList (+2 more)

### Community 77 - "Community 77"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 78 - "Community 78"
Cohesion: 0.14
Nodes (19): useInterruptedRun(), MAX_CARDS, NeedsYouCard, needsYouCards(), NeedsYouKind, sentence(), TicketLike, time() (+11 more)

### Community 79 - "Community 79"
Cohesion: 0.14
Nodes (12): ClaudeCliRunner, test_backends_are_separated_by_a_blank_line(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version(), test_lists_the_installed_backend(), test_nothing_installed_says_how_to_install(), test_project_shows_each_roles_backend_model_and_endpoint() (+4 more)

### Community 80 - "Community 80"
Cohesion: 0.13
Nodes (8): _authenticate(), _convert(), _Envelopes, EventStreams, _send(), _stream(), listener(), _until_disconnect()

### Community 81 - "Community 81"
Cohesion: 0.09
Nodes (4): Session, _signal_group(), _stream(), StreamParser

### Community 82 - "Community 82"
Cohesion: 0.14
Nodes (14): PlanOutput, _kept(), esc(), render_planner_prompt(), draft_file_name(), Existing, check_plan(), CheckedPlan (+6 more)

### Community 83 - "Community 83"
Cohesion: 0.11
Nodes (10): ItemVerdict, ReviewResult, _gate_word(), _ignore(), _items(), render_review_prompt(), review(), capture() (+2 more)

### Community 84 - "Community 84"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 85 - "Community 85"
Cohesion: 0.13
Nodes (10): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements(), _user_version(), utc_now() (+2 more)

### Community 86 - "Community 86"
Cohesion: 0.24
Nodes (18): auth(), error(), etag(), test_an_invalid_project_yaml_is_listed_with_its_first_problem(), test_create_project_from_an_unknown_template(), test_create_project_like_spool_init(), test_list_and_get_projects(), test_project_detail_says_why_nothing_can_run() (+10 more)

### Community 87 - "Community 87"
Cohesion: 0.09
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 88 - "Community 88"
Cohesion: 0.15
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 89 - "Community 89"
Cohesion: 0.24
Nodes (21): parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason() (+13 more)

### Community 90 - "Community 90"
Cohesion: 0.19
Nodes (17): gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test(), test_failing_test() (+9 more)

### Community 91 - "Community 91"
Cohesion: 0.18
Nodes (14): init(), test_a_copier_failure_is_reported(), test_a_failed_commit_removes_the_repo_and_workspace(), test_a_failed_workspace_empties_an_existing_folder(), test_a_file_as_repo_is_refused(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_non_empty_folder_is_refused_and_untouched() (+6 more)

### Community 92 - "Community 92"
Cohesion: 0.09
Nodes (10): set_command(), sync_command(), describe(), make_runner(), review_command(), store_api_key(), backend_names(), keyring_key() (+2 more)

### Community 93 - "Community 93"
Cohesion: 0.13
Nodes (10): list_runs(), AttemptView, CurrentRun, Discarded, MergedView, PhaseLine, PolicyView, Reject (+2 more)

### Community 94 - "Community 94"
Cohesion: 0.19
Nodes (10): DoneWhenCheck, GateResult, GateRun, GateStatus, check_done_when(), _not_run(), _run_gate(), run_gates() (+2 more)

### Community 95 - "Community 95"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 96 - "Community 96"
Cohesion: 0.13
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 97 - "Community 97"
Cohesion: 0.16
Nodes (9): ApiError, require_if_match(), delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretValue (+1 more)

### Community 98 - "Community 98"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 99 - "Community 99"
Cohesion: 0.23
Nodes (11): createItem(), getItem(), listItems(), Item, NewItem, ItemList(), CreateItemForm(), submit() (+3 more)

### Community 100 - "Community 100"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 101 - "Community 101"
Cohesion: 0.19
Nodes (15): is_git_url(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder(), test_a_local_git_repository_at_a_ref() (+7 more)

### Community 102 - "Community 102"
Cohesion: 0.10
Nodes (6): test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 103 - "Community 103"
Cohesion: 0.18
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 104 - "Community 104"
Cohesion: 0.15
Nodes (10): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+2 more)

### Community 105 - "Community 105"
Cohesion: 0.15
Nodes (5): _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 106 - "Community 106"
Cohesion: 0.13
Nodes (10): check_gate_command(), gate_env(), resolve_program(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument() (+2 more)

### Community 107 - "Community 107"
Cohesion: 0.22
Nodes (15): describe(), RuleHit, change(), decide(), test_a_project_list_replaces_the_default(), test_a_rename_hits_on_either_name(), test_delivery_mode(), test_describe_reads_stored_rules() (+7 more)

### Community 108 - "Community 108"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 109 - "Community 109"
Cohesion: 0.21
Nodes (7): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), _validation_error()

### Community 110 - "Community 110"
Cohesion: 0.17
Nodes (12): _clear_read_only_and_retry(), remove_path(), builtin_descriptions(), builtin_names(), builtin_root(), _clone(), _git(), _is_path() (+4 more)

### Community 111 - "Community 111"
Cohesion: 0.25
Nodes (14): parse_plan(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store(), test_ids_of_kept_tickets_cannot_be_reused() (+6 more)

### Community 112 - "Community 112"
Cohesion: 0.12
Nodes (9): fake_claude_cmd(), fake_codex_cmd(), fake_sdk_cmd(), git_repo(), make_git_template(), make_github_remote(), make_template(), push_elsewhere() (+1 more)

### Community 113 - "Community 113"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 114 - "Community 114"
Cohesion: 0.17
Nodes (5): clean_title(), _not_blank(), one_line(), PlannedTicket, test_one_line_drops_control_and_format_characters()

### Community 115 - "Community 115"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 116 - "Community 116"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 117 - "Community 117"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 118 - "Community 118"
Cohesion: 0.26
Nodes (9): RunRegistry, jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once(), test_one_plan_per_project_at_a_time() (+1 more)

### Community 119 - "Community 119"
Cohesion: 0.21
Nodes (11): test_init_existing_folder(), test_init_reports_every_problem(), test_init_template_ref_needs_a_template(), test_init_then_validate(), test_init_with_a_bad_template_creates_nothing(), test_init_with_a_git_template_prints_the_commit_first(), test_init_with_a_git_template_runs_no_global_git_hooks(), test_init_with_a_local_template() (+3 more)

### Community 120 - "Community 120"
Cohesion: 0.17
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 121 - "Community 121"
Cohesion: 0.19
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 122 - "Community 122"
Cohesion: 0.18
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 123 - "Community 123"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 124 - "Community 124"
Cohesion: 0.12
Nodes (17): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+9 more)

### Community 125 - "Community 125"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 126 - "Community 126"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 127 - "Community 127"
Cohesion: 0.22
Nodes (12): AttemptFinishedData, AttemptStartedData, AuthMessage, _Data, EventEnvelope, IntegrateData, LogData, PolicyDecisionData (+4 more)

### Community 128 - "Community 128"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 129 - "Community 129"
Cohesion: 0.23
Nodes (7): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_serve_refuses_while_another_daemon_holds_the_lock(), test_startup_recovers_and_skips_a_corrupt_database(), test_startup_without_a_projects_folder_serves()

### Community 130 - "Community 130"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 131 - "Community 131"
Cohesion: 0.30
Nodes (6): approve_plan(), generate_plan(), _plans(), GeneratePlan, PlanApproved, PlanStarted

### Community 132 - "Community 132"
Cohesion: 0.18
Nodes (4): configure_logging(), JsonFormatter, PlainFormatter, _Redactor

### Community 133 - "Community 133"
Cohesion: 0.27
Nodes (10): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning() (+2 more)

### Community 134 - "Community 134"
Cohesion: 0.22
Nodes (5): create_app(), client(), test_session(), engine(), session()

### Community 135 - "Community 135"
Cohesion: 0.22
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 137 - "Community 137"
Cohesion: 0.31
Nodes (5): Base, Item, create_item(), get_item(), list_items()

### Community 138 - "Community 138"
Cohesion: 0.33
Nodes (9): make_plan(), test_a_failed_write_leaves_the_old_files(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members(), test_approving_twice_gives_nothing_to_approve() (+1 more)

### Community 139 - "Community 139"
Cohesion: 0.22
Nodes (7): Agents, useAgents(), AgentsTab(), Backend, BackendStatus(), label(), LABELS

### Community 140 - "Community 140"
Cohesion: 0.29
Nodes (5): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from()

### Community 141 - "Community 141"
Cohesion: 0.27
Nodes (5): just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 142 - "Community 142"
Cohesion: 0.23
Nodes (5): ChangedFile, parse_numstat(), staged_changes(), test_parse_numstat_with_a_rename_and_a_binary(), test_staged_changes_names_both_sides_of_a_rename()

### Community 143 - "Community 143"
Cohesion: 0.38
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 144 - "Community 144"
Cohesion: 0.18
Nodes (5): consistency_errors(), InvalidVerdict, _location(), ParsedItem, ParsedVerdict

### Community 145 - "Community 145"
Cohesion: 0.32
Nodes (4): agents(), AgentsView, BackendView, GraphifyView

### Community 147 - "Community 147"
Cohesion: 0.24
Nodes (3): get_engine(), get_session(), make_engine()

### Community 148 - "Community 148"
Cohesion: 0.27
Nodes (7): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 149 - "Community 149"
Cohesion: 0.25
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 150 - "Community 150"
Cohesion: 0.29
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 151 - "Community 151"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 152 - "Community 152"
Cohesion: 0.22
Nodes (3): clean(), _Log, test_clean_strips_ansi_and_crlf()

### Community 153 - "Community 153"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 154 - "Community 154"
Cohesion: 0.25
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 155 - "Community 155"
Cohesion: 0.27
Nodes (5): allowed_env(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start(), test_windows_names_match_in_any_case()

### Community 156 - "Community 156"
Cohesion: 0.33
Nodes (5): log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token(), test_reconfiguring_replaces_handlers()

### Community 157 - "Community 157"
Cohesion: 0.24
Nodes (4): run_log(), workspace(), Artifact, get_artifact()

### Community 159 - "Community 159"
Cohesion: 0.33
Nodes (7): etag_of(), _lock(), read_with_etag(), write_if_match(), test_concurrent_edits_with_the_same_etag_let_one_win(), edit(), test_write_only_when_the_etag_matches()

### Community 160 - "Community 160"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 161 - "Community 161"
Cohesion: 0.27
Nodes (5): run_ticket(), setup(), test_hello_with_and_without_the_code_map(), model_calls(), test_real_run_implements_and_approves_a_tiny_ticket()

### Community 162 - "Community 162"
Cohesion: 0.31
Nodes (3): describe(), StatusPill(), TopBar()

### Community 165 - "Community 165"
Cohesion: 0.47
Nodes (7): apply_transition(), copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 166 - "Community 166"
Cohesion: 0.39
Nodes (6): branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_with_no_root_does_nothing(), test_worktree_of_a_killed_process_is_recovered()

### Community 167 - "Community 167"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 168 - "Community 168"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 172 - "Community 172"
Cohesion: 0.32
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 173 - "Community 173"
Cohesion: 0.46
Nodes (5): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 174 - "Community 174"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 175 - "Community 175"
Cohesion: 0.38
Nodes (3): App(), root, react-dom

### Community 176 - "Community 176"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 177 - "Community 177"
Cohesion: 0.48
Nodes (3): manager(), wt_repo(), wt_root()

### Community 179 - "Community 179"
Cohesion: 0.40
Nodes (3): GateLine, inputs(), worktree()

### Community 181 - "Community 181"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 184 - "Community 184"
Cohesion: 0.33
Nodes (5): test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_writes_outside_the_worktree_are_skipped()

### Community 185 - "Community 185"
Cohesion: 0.53
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 186 - "Community 186"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 188 - "Community 188"
Cohesion: 0.40
Nodes (3): done_when_items(), render_draft(), test_a_title_that_needs_quotes_stays_valid_yaml()

### Community 201 - "Community 201"
Cohesion: 0.67
Nodes (3): dependencies, react, react-dom

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `Config`, `InvalidRequest`, `NotRunning` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2112 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **175 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 11` to `Community 0`, `Community 1`, `Community 129`, `Community 4`, `Community 10`, `Community 13`, `Community 17`, `Community 148`, `Community 29`, `Community 157`, `Community 31`, `Community 34`, `Community 35`, `Community 164`, `Community 39`, `Community 52`, `Community 53`, `Community 61`, `Community 80`, `Community 85`, `Community 97`, `Community 118`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `RunLog` (e.g. with `page_runs()` and `recover_interrupted()`) actually correct?**
  _`RunLog` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `Config` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0364963503649635 - nodes in this community are weakly interconnected._
- **Why does `load_project()` connect `Community 26` to `Community 0`, `Community 1`, `Community 7`, `Community 141`, `Community 14`, `Community 143`, `Community 28`, `Community 161`, `Community 37`, `Community 39`, `Community 41`, `Community 45`, `Community 47`, `Community 178`, `Community 51`, `Community 52`, `Community 59`, `Community 61`, `Community 71`, `Community 74`, `Community 79`, `Community 86`, `Community 91`, `Community 92`, `Community 103`, `Community 113`, `Community 118`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03958416633346661 - nodes in this community are weakly interconnected._
- **Why does `WorktreeManager` connect `Community 34` to `Community 0`, `Community 1`, `Community 38`, `Community 166`, `Community 108`, `Community 46`, `Community 16`, `Community 17`, `Community 18`, `Community 177`, `Community 52`, `Community 148`, `Community 58`, `Community 29`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._