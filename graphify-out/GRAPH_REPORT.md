# Graph Report - Project_Manager  (2026-11-05)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 6320 nodes · 18033 edges · 343 communities (168 shown, 175 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1501 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `806cb60d`
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
- Community 163
- Community 164
- Community 165
- Community 166
- Community 167
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
- Community 184
- Community 185
- Community 186
- Community 187
- Community 188
- Community 190
- Community 191
- Community 192
- Community 195
- Community 331
- Community 332
- Community 333

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 115 edges
2. `WorktreeManager` - 82 edges
3. `load_project()` - 82 edges
4. `RunRegistry` - 70 edges
5. `AgentPolicy` - 69 edges
6. `FakeRunner` - 68 edges
7. `ClaudeStreamParser` - 61 edges
8. `build_implementer_prompt()` - 60 edges
9. `Run` - 56 edges
10. `RunContext` - 52 edges

## Surprising Connections (you probably didn't know these)
- `schema()` --uses--> `Settings`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/core/config.py
- `schema()` --calls--> `create_app()`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/api/app.py
- `sdk()` --calls--> `AgentSdkRunner`  [INFERRED]
  daemon/tests/services/runloop/test_model.py → daemon/src/spoolhq/services/agents/agent_sdk.py
- `test_codex_not_logged_in_says_codex_login()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/polling.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
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
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (343 total, 175 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (29): AgentSdkRunner, check_path(), policy_parts(), stop(), billing_for(), format_version(), parse_version(), platform_reason() (+21 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (31): agents_command(), describe(), describe_roles(), describe_worktrees(), fail(), settings(), table(), describe() (+23 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (25): keep_for(), check_ticket_id(), _user_approved(), EventBus, attempt_dir_name(), _check_count(), _make_attempt_dir(), RunLog (+17 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (49): advance(), checked_out(), commit(), conclude_merge(), conflict_files(), create_tag(), ensure_main_ready(), _git() (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (35): describe_graphify(), _build(), CodeMap, _current(), _drop(), _refresh(), _remove_unused(), _save() (+27 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (22): Project, approve(), reject(), unblock(), _waiting(), HoldForIntegration, IntegrationStatus, Integrator (+14 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (40): slugify(), escape_closing_tag(), clean_title(), InvalidPlan, _not_blank(), one_line(), PlannedTicket, PlannerError (+32 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (48): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), _usage_counts(), usd_to_micro(), assistant(), load() (+40 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (34): CliTransport, billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), assert_refused(), read_only(), read_record() (+26 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (58): Agents, useAgents(), checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning (+50 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (54): useProjects(), settingsErrorLine(), useInterruptedRun(), MAX_CARDS, NeedsYouCard, needsYouCards(), NeedsYouKind, sentence() (+46 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (60): state_db_path(), state_dir(), seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first() (+52 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (25): ApiClient, ApiError, DaemonNotRunning, _detail(), init(), serve(), _serve(), _Server (+17 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (46): api_key(), no_parent_key(), test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript(), record(), run() (+38 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (24): decode_cursor(), encode_cursor(), page_runs(), RunPage, AttemptStatus, Event, EventKind, RunKind (+16 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (44): COALESCE_MS, EventSource, lastSeq, Probe(), subscribe, useProjectEvents(), ProjectDetail, ProjectSummary (+36 more)

### Community 16 - "Community 16"
Cohesion: 0.05
Nodes (35): check_command(), check_tool(), make_hook(), pre_tool_use(), relative_pattern(), policy(), user_home(), worktree() (+27 more)

### Community 17 - "Community 17"
Cohesion: 0.09
Nodes (60): list_tickets(), load_ticket(), read_ticket(), save_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets() (+52 more)

### Community 18 - "Community 18"
Cohesion: 0.04
Nodes (15): resolve_program(), ProcessResult, run_process(), _signal_group(), _stop_tree(), run_project(), sandbox_which(), set_identity() (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (41): ConfigError, load_settings(), _api_routes(), test_bodies_over_1_mb_are_refused(), test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected() (+33 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (20): weighted_tokens(), keep_end(), PolicyViolation, summarize(), temp_folders(), temp_worktree_refusal(), CodexStreamParser, _int() (+12 more)

### Community 21 - "Community 21"
Cohesion: 0.05
Nodes (53): dependencies, react, react-dom, engines, node, name, packageManager, private (+45 more)

### Community 22 - "Community 22"
Cohesion: 0.07
Nodes (48): PlanProblem, TransitionError, validate_plan(), apply_transition(), check_transition(), parse_status(), copy_dashboard(), dashboard() (+40 more)

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (30): require_if_match(), run_log(), settings(), workspace(), _conflict(), create_project(), get_project(), get_settings() (+22 more)

### Community 24 - "Community 24"
Cohesion: 0.14
Nodes (40): AgentPolicy, assert_gone(), endpoint_runner(), read_record(), Recorder, run(), runner(), test_a_custom_endpoint_never_gets_the_users_login() (+32 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (19): GitHubClient, GitHubError, _message(), create_pull(), get_pull(), _list(), list_review_comments(), list_reviews() (+11 more)

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (26): id_key(), PlanError, SchedulerError, _and_list(), _find_cycles(), require_valid(), sort_ids(), sort_tickets() (+18 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (20): write_atomic(), parse_done_when(), TicketEdit, TicketError, TicketValidationError, DoneItem, find_ticket_file(), _id_sort_key() (+12 more)

### Community 28 - "Community 28"
Cohesion: 0.10
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 29 - "Community 29"
Cohesion: 0.09
Nodes (31): auth(), error(), etag(), test_an_invalid_project_yaml_is_listed_with_its_first_problem(), test_create_project_from_an_unknown_template(), test_create_project_like_spool_init(), test_list_and_get_projects(), test_project_detail_says_why_nothing_can_run() (+23 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (42): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_ticket(), test_negative_cap_is_refused(), test_no_map_no_block(), test_the_map_counts_against_the_budget() (+34 more)

### Community 31 - "Community 31"
Cohesion: 0.06
Nodes (19): _client(), set_command(), sync_command(), store_api_key(), available_runners(), backend_names(), make_runner(), endpoint_token() (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.06
Nodes (24): github_token(), store_github_token(), auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from(), daemon_answering() (+16 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (42): git_executable(), WorktreeManager, run_git(), branches(), make_read_only(), marker(), real(), registered_paths() (+34 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (23): approval_message(), agent_stopped(), attempt_once(), check_resolved(), commit(), drive(), _git(), implement() (+15 more)

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (31): LocalIntegrator, RunRegistry, Transcripts, git(), hooked(), call(), kinds(), _linking() (+23 more)

### Community 36 - "Community 36"
Cohesion: 0.08
Nodes (22): finish(), last_merged(), _result(), tag_name(), waiting_message(), IntegrationResult, _get(), get_integration() (+14 more)

### Community 37 - "Community 37"
Cohesion: 0.10
Nodes (23): remove_path(), CheckResult, load_contract(), _message(), parse_contract(), TemplateContract, TemplateError, check_safe() (+15 more)

### Community 38 - "Community 38"
Cohesion: 0.08
Nodes (37): branch_name(), check_git_version(), GitResult, parse_git_version(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it() (+29 more)

### Community 39 - "Community 39"
Cohesion: 0.08
Nodes (28): ChangedFile, parse_numstat(), staged_changes(), decide(), as_record(), _compile(), delivery_mode(), describe() (+20 more)

### Community 40 - "Community 40"
Cohesion: 0.09
Nodes (26): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+18 more)

### Community 41 - "Community 41"
Cohesion: 0.09
Nodes (26): backendReady(), useDaemonSettings(), useVersion(), AccountsTab(), AgentsTab(), Backend, BackendStatus(), label() (+18 more)

### Community 42 - "Community 42"
Cohesion: 0.07
Nodes (8): marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, same_path(), Worktree, WorktreeSession, test_parse_worktree_list()

### Community 43 - "Community 43"
Cohesion: 0.09
Nodes (33): _clean_line(), commit_message(), is_junk(), is_secret(), _matches(), merge_head(), branch(), git_out() (+25 more)

### Community 44 - "Community 44"
Cohesion: 0.08
Nodes (19): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+11 more)

### Community 45 - "Community 45"
Cohesion: 0.09
Nodes (18): read_artifact(), ahead_message(), _failed(), _held(), pr_branch(), _done_when(), _gates(), md_escape() (+10 more)

### Community 46 - "Community 46"
Cohesion: 0.09
Nodes (35): CommandTestResult, CreateProject, fieldError(), Gate, GATES, loadSettings(), ProjectSettings, saveCommands() (+27 more)

### Community 47 - "Community 47"
Cohesion: 0.15
Nodes (24): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+16 more)

### Community 48 - "Community 48"
Cohesion: 0.07
Nodes (13): Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token(), example(), test_task_md_example_project_yaml_validates(), jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error() (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.14
Nodes (27): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+19 more)

### Community 50 - "Community 50"
Cohesion: 0.11
Nodes (20): save_project(), Delivery, ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits() (+12 more)

### Community 51 - "Community 51"
Cohesion: 0.08
Nodes (26): cap_excerpt(), keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec() (+18 more)

### Community 52 - "Community 52"
Cohesion: 0.07
Nodes (24): fake_backend(), fake_graphify(), free_port(), git_identity(), home(), isolated_git(), keychain(), no_graphify() (+16 more)

### Community 53 - "Community 53"
Cohesion: 0.15
Nodes (19): service_errors(), approve_ticket(), Artifact, cancel_run(), current_run(), discard_ticket(), get_artifact(), get_run() (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (22): cache_dir(), refresh(), FakeGraphify, plan_transcript(), builds(), pointer(), source(), test_a_busy_cache_gives_no_map() (+14 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (34): del_path(), errors_for(), set_path(), test_a_template_must_be_a_block(), test_all_errors_are_reported_at_once(), test_bad_protected_path_patterns_are_refused(), test_bad_repo_in_yaml(), test_bad_slug_is_refused() (+26 more)

### Community 56 - "Community 56"
Cohesion: 0.17
Nodes (25): kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt(), test_changes_requested_three_times_blocks() (+17 more)

### Community 57 - "Community 57"
Cohesion: 0.10
Nodes (21): build_argv(), install_dir(), permission_profile(), policy_parts(), _toml(), with_codex_home(), expected(), profile_of() (+13 more)

### Community 58 - "Community 58"
Cohesion: 0.09
Nodes (15): hours(), approve_command(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner() (+7 more)

### Community 59 - "Community 59"
Cohesion: 0.10
Nodes (17): dumper(), loader(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node() (+9 more)

### Community 60 - "Community 60"
Cohesion: 0.10
Nodes (16): _read(), show_command(), ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, GateFailure (+8 more)

### Community 61 - "Community 61"
Cohesion: 0.13
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _control(), discard_command() (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 63 - "Community 63"
Cohesion: 0.08
Nodes (19): SET_UP_FIRST, Backend, backends, GET, Handler, NOT_SET, PUT, renderDialog() (+11 more)

### Community 64 - "Community 64"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 65 - "Community 65"
Cohesion: 0.10
Nodes (22): build_argv(), check_worktree(), child_env(), sandbox_settings(), parent_env(), settings_json(), test_a_custom_endpoint_gets_spoolhqs_token_and_no_login(), test_api_billing_keeps_only_the_api_key() (+14 more)

### Community 66 - "Community 66"
Cohesion: 0.13
Nodes (19): capture(), on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact() (+11 more)

### Community 67 - "Community 67"
Cohesion: 0.10
Nodes (14): ApiError, delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretValue, SecretView (+6 more)

### Community 68 - "Community 68"
Cohesion: 0.10
Nodes (17): BackendSettings, Budget, _check_backend(), _check_base_url(), _check_path_pattern(), Commands, ContextSettings, GatesSettings (+9 more)

### Community 69 - "Community 69"
Cohesion: 0.16
Nodes (18): close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(), stuck() (+10 more)

### Community 70 - "Community 70"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 71 - "Community 71"
Cohesion: 0.12
Nodes (18): ClaudeCliRunner, test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable() (+10 more)

### Community 72 - "Community 72"
Cohesion: 0.22
Nodes (24): FakeRunner, ReviewInputs, run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages(), test_cancelled_is_passed_through() (+16 more)

### Community 73 - "Community 73"
Cohesion: 0.08
Nodes (14): HomePage(), daemonDown(), GET, Handler, notRunning(), POST, Project, projects (+6 more)

### Community 74 - "Community 74"
Cohesion: 0.16
Nodes (14): App(), createItem(), getItem(), listItems(), Item, NewItem, ItemList(), CreateItemForm() (+6 more)

### Community 75 - "Community 75"
Cohesion: 0.11
Nodes (10): FakeGates, Merging, main(), codex_review(), set_roles(), test_a_ticket_runs_end_to_end_on_codex(), codex(), test_a_ticket_runs_end_to_end_on_the_agent_sdk() (+2 more)

### Community 76 - "Community 76"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 77 - "Community 77"
Cohesion: 0.14
Nodes (16): _area_entries(), expand_index(), _inside(), _read(), read_repo_docs(), read_text(), decisions_block(), entry() (+8 more)

### Community 78 - "Community 78"
Cohesion: 0.11
Nodes (13): create_app(), lifespan(), check_git(), recover_all_integrations(), recover_all_worktrees(), make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree() (+5 more)

### Community 79 - "Community 79"
Cohesion: 0.15
Nodes (10): get_ticket(), get_tickets(), put_ticket(), _read(), unblock_ticket(), InvalidTicketView, Note, TicketList (+2 more)

### Community 80 - "Community 80"
Cohesion: 0.13
Nodes (17): check_command(), home_denials(), PolicyError, test_real_codex_run_creates_a_file_and_cannot_read_ssh(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused() (+9 more)

### Community 81 - "Community 81"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 82 - "Community 82"
Cohesion: 0.13
Nodes (10): _authenticate(), _convert(), _Envelopes, events(), EventStreams, _send(), _stream(), listener() (+2 more)

### Community 83 - "Community 83"
Cohesion: 0.20
Nodes (23): consistency_errors(), _location(), parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met() (+15 more)

### Community 84 - "Community 84"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 85 - "Community 85"
Cohesion: 0.11
Nodes (13): root, root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes (+5 more)

### Community 86 - "Community 86"
Cohesion: 0.09
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 87 - "Community 87"
Cohesion: 0.15
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 88 - "Community 88"
Cohesion: 0.19
Nodes (17): gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test(), test_failing_test() (+9 more)

### Community 89 - "Community 89"
Cohesion: 0.17
Nodes (13): init(), test_a_copier_failure_is_reported(), test_a_failed_commit_removes_the_repo_and_workspace(), test_a_failed_workspace_empties_an_existing_folder(), test_a_file_as_repo_is_refused(), test_a_git_url_template_records_the_commit(), test_a_non_empty_folder_is_refused_and_untouched(), test_a_template_without_a_test_command_is_rejected() (+5 more)

### Community 90 - "Community 90"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 92 - "Community 92"
Cohesion: 0.26
Nodes (15): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_attempt_artifacts(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_history_pages_are_stable_under_inserts() (+7 more)

### Community 93 - "Community 93"
Cohesion: 0.13
Nodes (8): JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token(), test_reconfiguring_replaces_handlers()

### Community 94 - "Community 94"
Cohesion: 0.18
Nodes (16): is_git_url(), _is_path(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder() (+8 more)

### Community 95 - "Community 95"
Cohesion: 0.21
Nodes (9): _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state(), test_dirty_checkout_after_a_cut_off_fast_forward_is_left_alone() (+1 more)

### Community 96 - "Community 96"
Cohesion: 0.17
Nodes (11): _check_decisions(), _decisions(), folders(), test_a_consistent_fixture_passes(), test_a_duplicated_number_fails(), test_a_mismatched_title_fails(), test_a_missing_number_fails(), test_an_entry_missing_from_the_area_files_fails() (+3 more)

### Community 97 - "Community 97"
Cohesion: 0.15
Nodes (7): GateLine, ItemVerdict, ReviewResult, _ignore(), InvalidVerdict, ParsedItem, ParsedVerdict

### Community 98 - "Community 98"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 99 - "Community 99"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 100 - "Community 100"
Cohesion: 0.16
Nodes (16): PATHS, RunAction, useRunAction(), formatUsage(), guidance(), idleReason(), PanelState, Tab (+8 more)

### Community 101 - "Community 101"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 102 - "Community 102"
Cohesion: 0.11
Nodes (6): code(), fenced(), _PromptLoader, PromptTemplate, render_template(), _template_line()

### Community 103 - "Community 103"
Cohesion: 0.15
Nodes (7): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState

### Community 104 - "Community 104"
Cohesion: 0.11
Nodes (15): init_project(), template_description(), workspace(), _fail_after_yaml(), test_an_unreadable_template_description(), test_failed_rename_leaves_nothing(), test_failure_mid_init_leaves_nothing(), test_init_creates_workspace() (+7 more)

### Community 105 - "Community 105"
Cohesion: 0.11
Nodes (3): _Job, PlanJobs, planner_code_map()

### Community 106 - "Community 106"
Cohesion: 0.10
Nodes (10): fake_claude_cmd(), fake_codex_cmd(), fake_sdk_cmd(), git_repo(), make_git_template(), make_github_remote(), make_template(), plan_project() (+2 more)

### Community 107 - "Community 107"
Cohesion: 0.15
Nodes (13): Agents, DaemonSettings, removeSecret(), SecretName, storeSecret(), useRefreshSecrets(), message(), SecretRow() (+5 more)

### Community 108 - "Community 108"
Cohesion: 0.18
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 109 - "Community 109"
Cohesion: 0.15
Nodes (5): _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 110 - "Community 110"
Cohesion: 0.13
Nodes (6): disabled_hooks_dir(), hook_and_signing_options(), neutral_cwd(), remote_env(), main(), problems()

### Community 111 - "Community 111"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 112 - "Community 112"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 113 - "Community 113"
Cohesion: 0.22
Nodes (10): auth(), etag(), fixture_tickets(), test_conflicting_edit(), test_get_then_put_unchanged_is_byte_identical(), test_list_with_filters(), test_status_changes_follow_the_transition_table(), test_ticket_ids_are_checked_in_the_path() (+2 more)

### Community 114 - "Community 114"
Cohesion: 0.21
Nodes (7): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), _validation_error()

### Community 115 - "Community 115"
Cohesion: 0.14
Nodes (5): version(), Version, health(), Health, create_app()

### Community 116 - "Community 116"
Cohesion: 0.19
Nodes (13): parse_ticket(), render_ticket(), make_plan(), test_a_draft_round_trips_through_the_ticket_store(), test_a_failed_write_leaves_the_old_files(), test_a_title_that_needs_quotes_stays_valid_yaml(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line() (+5 more)

### Community 117 - "Community 117"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 118 - "Community 118"
Cohesion: 0.14
Nodes (3): billing_error(), SdkRun, test_billing_errors_are_recognised()

### Community 119 - "Community 119"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 120 - "Community 120"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 121 - "Community 121"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 122 - "Community 122"
Cohesion: 0.21
Nodes (11): test_init_existing_folder(), test_init_reports_every_problem(), test_init_template_ref_needs_a_template(), test_init_then_validate(), test_init_with_a_bad_template_creates_nothing(), test_init_with_a_git_template_prints_the_commit_first(), test_init_with_a_git_template_runs_no_global_git_hooks(), test_init_with_a_local_template() (+3 more)

### Community 123 - "Community 123"
Cohesion: 0.20
Nodes (12): AttemptFinishedData, AttemptStartedData, AuthMessage, _Data, EventEnvelope, IntegrateData, LogData, PolicyDecisionData (+4 more)

### Community 124 - "Community 124"
Cohesion: 0.19
Nodes (8): AttemptView, CurrentRun, Discarded, MergedView, PhaseLine, PolicyView, Reject, RuleHitView

### Community 125 - "Community 125"
Cohesion: 0.12
Nodes (6): test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 126 - "Community 126"
Cohesion: 0.17
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 127 - "Community 127"
Cohesion: 0.21
Nodes (8): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements(), _user_version(), utc_now()

### Community 128 - "Community 128"
Cohesion: 0.17
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 129 - "Community 129"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 130 - "Community 130"
Cohesion: 0.12
Nodes (17): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+9 more)

### Community 131 - "Community 131"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 132 - "Community 132"
Cohesion: 0.23
Nodes (12): RepoDocs, fixture_text(), base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections() (+4 more)

### Community 133 - "Community 133"
Cohesion: 0.14
Nodes (6): _gate_word(), _items(), render_review_prompt(), review(), finish(), test_each_review_is_its_own_run()

### Community 134 - "Community 134"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 135 - "Community 135"
Cohesion: 0.15
Nodes (3): _openapi(), health(), Health

### Community 136 - "Community 136"
Cohesion: 0.16
Nodes (9): check_gate_command(), gate_env(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused() (+1 more)

### Community 137 - "Community 137"
Cohesion: 0.23
Nodes (9): GateResult, GateStatus, clean(), _not_run(), _run_gate(), run_gates(), try_command(), test_clean_strips_ansi_and_crlf() (+1 more)

### Community 138 - "Community 138"
Cohesion: 0.23
Nodes (8): EditConflict, etag_of(), _lock(), read_with_etag(), write_if_match(), test_concurrent_edits_with_the_same_etag_let_one_win(), edit(), test_write_only_when_the_etag_matches()

### Community 139 - "Community 139"
Cohesion: 0.18
Nodes (9): _initial_yaml(), load_project(), parse_project(), _populate(), _validate(), test_load_missing_project(), test_load_missing_yaml(), test_load_refuses_path_tricks() (+1 more)

### Community 140 - "Community 140"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 141 - "Community 141"
Cohesion: 0.22
Nodes (8): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd(), fixture_contract()

### Community 142 - "Community 142"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 143 - "Community 143"
Cohesion: 0.30
Nodes (6): approve_plan(), generate_plan(), _plans(), GeneratePlan, PlanApproved, PlanStarted

### Community 144 - "Community 144"
Cohesion: 0.26
Nodes (8): branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing(), test_worktree_of_a_killed_process_is_recovered()

### Community 145 - "Community 145"
Cohesion: 0.22
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 146 - "Community 146"
Cohesion: 0.19
Nodes (4): DoneWhenCheck, GateFailureData, GateRun, check_done_when()

### Community 148 - "Community 148"
Cohesion: 0.26
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 149 - "Community 149"
Cohesion: 0.38
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 150 - "Community 150"
Cohesion: 0.21
Nodes (6): allowed_env(), child_env(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start(), test_windows_names_match_in_any_case()

### Community 151 - "Community 151"
Cohesion: 0.32
Nodes (4): agents(), AgentsView, BackendView, GraphifyView

### Community 152 - "Community 152"
Cohesion: 0.26
Nodes (6): latest_phase(), project_totals(), Totals, test_an_empty_log_has_no_usage_and_no_activity(), test_last_activity_is_the_latest_event_and_the_step_its_phase(), test_usage_sums_tokens_and_cost_across_runs()

### Community 154 - "Community 154"
Cohesion: 0.26
Nodes (5): Base, client(), test_session(), engine(), session()

### Community 155 - "Community 155"
Cohesion: 0.24
Nodes (5): commit_file(), manager(), wt_repo(), wt_root(), test_real_review_names_the_missing_test()

### Community 156 - "Community 156"
Cohesion: 0.24
Nodes (9): test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file(), test_token_budget() (+1 more)

### Community 157 - "Community 157"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 158 - "Community 158"
Cohesion: 0.27
Nodes (3): get_engine(), get_session(), make_engine()

### Community 159 - "Community 159"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 160 - "Community 160"
Cohesion: 0.25
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 161 - "Community 161"
Cohesion: 0.20
Nodes (4): clock(), FixedClock, test_killed_daemon_leaves_an_interrupted_run(), test_recovery_scope()

### Community 162 - "Community 162"
Cohesion: 0.29
Nodes (5): generated(), just(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 164 - "Community 164"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 165 - "Community 165"
Cohesion: 0.44
Nodes (4): Item, create_item(), get_item(), list_items()

### Community 166 - "Community 166"
Cohesion: 0.27
Nodes (5): run_ticket(), setup(), test_hello_with_and_without_the_code_map(), model_calls(), test_real_run_implements_and_approves_a_tiny_ticket()

### Community 169 - "Community 169"
Cohesion: 0.25
Nodes (5): dump(), parse(), read(), to_plain(), _record_git_source()

### Community 170 - "Community 170"
Cohesion: 0.39
Nodes (6): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_one_line_drops_control_and_format_characters(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 171 - "Community 171"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 172 - "Community 172"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 177 - "Community 177"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `Config`, `InvalidRequest`, `NotRunning` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2123 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **175 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 2` to `Community 1`, `Community 3`, `Community 5`, `Community 11`, `Community 14`, `Community 23`, `Community 152`, `Community 25`, `Community 161`, `Community 35`, `Community 36`, `Community 44`, `Community 47`, `Community 50`, `Community 66`, `Community 69`, `Community 78`, `Community 82`, `Community 92`, `Community 105`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `RunLog` (e.g. with `page_runs()` and `recover_interrupted()`) actually correct?**
  _`RunLog` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `Config` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.03132832080200501 - nodes in this community are weakly interconnected._
- **Why does `CodexStreamParser` connect `Community 20` to `Community 0`, `Community 8`, `Community 13`, `Community 7`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03058064516129032 - nodes in this community are weakly interconnected._
- **Why does `ensure_home()` connect `Community 12` to `Community 110`, `Community 19`, `Community 78`, `Community 135`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._