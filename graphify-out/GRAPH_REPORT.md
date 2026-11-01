# Graph Report - Project_Manager  (2026-11-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 6033 nodes · 17102 edges · 369 communities (189 shown, 180 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1483 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1c8afeb0`
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
- Community 188
- Community 189
- Community 190
- Community 191
- Community 192
- Community 193
- Community 194
- Community 195
- Community 196
- Community 197
- Community 198
- Community 199
- Community 200
- Community 201
- Community 202
- Community 203
- Community 204
- Community 205
- Community 206
- Community 208
- Community 211
- Community 213
- Community 214
- Community 215
- Community 217
- Community 218
- Community 357
- Community 358
- Community 359

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 109 edges
2. `WorktreeManager` - 82 edges
3. `load_project()` - 81 edges
4. `RunRegistry` - 70 edges
5. `AgentPolicy` - 69 edges
6. `FakeRunner` - 68 edges
7. `ClaudeStreamParser` - 61 edges
8. `Run` - 58 edges
9. `build_implementer_prompt()` - 57 edges
10. `RunContext` - 52 edges

## Surprising Connections (you probably didn't know these)
- `test_codex_not_logged_in_says_codex_login()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/runloop/test_integration.py → daemon/src/spoolhq/services/git/runner.py
- `test_error_without_stderr_has_no_colon()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/polling.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (369 total, 180 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (48): describe(), describe_worktrees(), set_command(), weighted_tokens(), store_api_key(), backend_names(), format_version(), parse_version() (+40 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (33): check_ticket_id(), _user_approved(), decode_cursor(), encode_cursor(), page_runs(), RunPage, attempt_dir_name(), _check_count() (+25 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (29): approve(), reject(), unblock(), _waiting(), last_merged(), HoldForIntegration, IntegrationStatus, Integrator (+21 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (43): agents(), AgentsView, BackendView, GraphifyView, describe_graphify(), _build(), cache_dir(), CodeMap (+35 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (30): fail(), hours(), settings(), table(), approve_command(), check_command(), describe_plan(), generate_command() (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (32): check_command(), check_path(), check_tool(), make_hook(), relative_pattern(), call_hook(), test_reviewer_and_planner_get_no_write_or_bash(), test_the_hook_allows_allowlisted_commands() (+24 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (45): apiError(), daemonDown(), daemonUp(), GET, Handler, notRunning(), POST, Project (+37 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (26): check_slug(), Project, approval_message(), _branch_of(), finish(), publish_tag(), recover_integrations(), _result() (+18 more)

### Community 8 - "Community 8"
Cohesion: 0.04
Nodes (53): dependencies, react, react-dom, engines, node, name, packageManager, private (+45 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (34): root, queryClient, QueryProvider(), SettingsDialog(), CommandsStep(), NewProjectButton(), HomePage(), renderHome() (+26 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (33): advance(), checked_out(), _clean_line(), commit(), conclude_merge(), conflict_files(), create_tag(), ensure_main_ready() (+25 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (53): load_ticket(), errors_for(), make_project(), replace_line(), save_and_read(), test_assignment_is_validated(), test_bad_file_name(), test_bad_project_name() (+45 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (24): branch_name(), default_branch_sha(), has_local_branch(), is_branch_name(), is_work_tree(), MissingBranchError, operation_in_progress(), check_git_version() (+16 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (46): raw(), run_log(), test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_cache_reads_count_a_tenth_toward_weighted_tokens(), test_closed_log_refuses_calls() (+38 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (8): AgentSdkRunner, policy_parts(), billing_error(), CliTransport, SdkRun, refusal(), required_parts(), test_billing_errors_are_recognised()

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (24): decide(), read_artifact(), agent_stopped(), attempt_once(), check_resolved(), commit(), drive(), _git() (+16 more)

### Community 17 - "Community 17"
Cohesion: 0.08
Nodes (19): TicketEdit, source_name(), TicketError, TicketValidationError, TicketMeta, find_ticket_file(), _id_sort_key(), InvalidTicket (+11 more)

### Community 18 - "Community 18"
Cohesion: 0.16
Nodes (34): LocalIntegrator, _assistant(), _init(), _result(), Transcripts, git(), hooked(), call() (+26 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (37): assert_gone(), endpoint_runner(), read_record(), Recorder, run(), runner(), test_a_custom_endpoint_never_gets_the_users_login(), test_a_remote_endpoint_without_a_token_is_refused() (+29 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (29): _force_utf8_streams(), main(), _stream(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app() (+21 more)

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (27): pre_tool_use(), client(), fake_backend(), fake_graphify(), free_port(), git_identity(), home(), isolated_git() (+19 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (41): build_implementer_prompt(), block(), fixture_inputs(), fixture_ticket(), test_negative_cap_is_refused(), test_no_map_no_block(), test_the_map_counts_against_the_budget(), test_the_map_is_cut_to_its_cap_least_connected_first() (+33 more)

### Community 23 - "Community 23"
Cohesion: 0.10
Nodes (26): require_if_match(), run_log(), settings(), workspace(), _conflict(), create_project(), get_project(), get_settings() (+18 more)

### Community 24 - "Community 24"
Cohesion: 0.06
Nodes (18): cap_excerpt(), ContextBudgetError, ContextError, PromptTemplateError, _clean(), code(), escape_closing_tag(), fenced() (+10 more)

### Community 25 - "Community 25"
Cohesion: 0.10
Nodes (21): remove_path(), dump(), loader(), check_template(), CheckResult, load_contract(), _message(), parse_contract() (+13 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (38): git_executable(), WorktreeManager, branches(), make_read_only(), marker(), real(), registered_paths(), test_commit_refuses_an_empty_message() (+30 more)

### Community 27 - "Community 27"
Cohesion: 0.15
Nodes (41): load_project(), del_path(), errors_for(), set_path(), test_a_template_must_be_a_block(), test_all_errors_are_reported_at_once(), test_bad_protected_path_patterns_are_refused(), test_bad_repo_in_yaml() (+33 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (7): branch_sha(), marker_key(), _norm(), RegisteredWorktree, same_path(), Worktree, WorktreeSession

### Community 29 - "Community 29"
Cohesion: 0.09
Nodes (35): ensure_clean(), ensure_no_operation_in_progress(), status_entries(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids() (+27 more)

### Community 30 - "Community 30"
Cohesion: 0.13
Nodes (28): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+20 more)

### Community 31 - "Community 31"
Cohesion: 0.09
Nodes (25): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+17 more)

### Community 32 - "Community 32"
Cohesion: 0.09
Nodes (14): RunRegistry, set_identity(), anonymise(), logged_in(), test_real_run_creates_a_file_and_is_denied_python(), test_real_review_names_the_missing_test(), jobs(), registry() (+6 more)

### Community 33 - "Community 33"
Cohesion: 0.09
Nodes (27): invokeMock, Agents, useAgents(), COALESCE_MS, lastSeq, useProjectEvents(), ProjectDetail, ProjectSummary (+19 more)

### Community 34 - "Community 34"
Cohesion: 0.09
Nodes (15): init(), serve(), _serve(), _Server, validate_project(), version(), load_or_create_token(), read_token() (+7 more)

### Community 35 - "Community 35"
Cohesion: 0.10
Nodes (27): editor_command(), run_editor(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment() (+19 more)

### Community 36 - "Community 36"
Cohesion: 0.18
Nodes (28): assert_refused(), read_only(), read_record(), refused_message(), run(), runner(), test_a_custom_endpoint_never_gets_the_users_login(), test_a_given_model_wins() (+20 more)

### Community 37 - "Community 37"
Cohesion: 0.17
Nodes (31): ClaudeStreamParser, assistant(), replay(), result(), test_accepted_modes_can_be_widened_by_the_adapter(), test_acting_before_init_is_a_violation(), test_api_retry_on_rate_limit_is_reported(), test_assistant_rate_limit_error_without_later_success() (+23 more)

### Community 38 - "Community 38"
Cohesion: 0.09
Nodes (13): FakeGates, Merging, codex_review(), set_roles(), test_a_ticket_runs_end_to_end_on_codex(), test_a_ticket_runs_end_to_end_on_the_agent_sdk(), sdk(), test_each_role_starts_its_own_backend() (+5 more)

### Community 39 - "Community 39"
Cohesion: 0.16
Nodes (25): kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt(), test_changes_requested_three_times_blocks() (+17 more)

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (17): Agents, BackendSettings, Budget, _check_backend(), _check_base_url(), _check_path_pattern(), Commands, ContextSettings (+9 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (18): App(), createItem(), getItem(), listItems(), Item, NewItem, ItemList(), CreateItemForm() (+10 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (21): build_argv(), install_dir(), permission_profile(), policy_parts(), _toml(), with_codex_home(), expected(), profile_of() (+13 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (22): build_argv(), child_env(), sandbox_settings(), AgentPolicy, test_policy_fields_are_untouched_by_credentials_list(), test_unusable_backend_raises_before_starting(), parent_env(), settings_json() (+14 more)

### Community 44 - "Community 44"
Cohesion: 0.09
Nodes (17): dumper(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node() (+9 more)

### Community 45 - "Community 45"
Cohesion: 0.17
Nodes (19): service_errors(), approve_ticket(), cancel_run(), current_run(), discard_ticket(), get_run(), list_runs(), _loop() (+11 more)

### Community 46 - "Community 46"
Cohesion: 0.12
Nodes (25): commit_message(), branch(), git_out(), head(), _squash(), _stage_link(), test_advance_fast_forwards_the_checked_out_branch(), test_advance_refuses_a_dirty_checkout() (+17 more)

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (22): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+14 more)

### Community 48 - "Community 48"
Cohesion: 0.13
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _control(), discard_command() (+7 more)

### Community 49 - "Community 49"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 50 - "Community 50"
Cohesion: 0.12
Nodes (19): capture(), on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact() (+11 more)

### Community 51 - "Community 51"
Cohesion: 0.20
Nodes (20): record(), run(), runner(), scenario(), test_a_billing_or_quota_error_blocks(), test_a_denied_call_is_reported_with_the_hooks_reason_and_logged(), test_a_failed_cli_reports_its_stderr(), test_a_local_endpoint_gets_the_dummy_token_not_the_key() (+12 more)

### Community 52 - "Community 52"
Cohesion: 0.12
Nodes (24): builtin_descriptions(), builtin_names(), builtin_root(), _clone(), _git(), is_git_url(), _is_path(), _label() (+16 more)

### Community 53 - "Community 53"
Cohesion: 0.09
Nodes (19): commit_file(), fake_claude_cmd(), fake_codex_cmd(), fake_sdk_cmd(), git_repo(), make_git_template(), make_github_remote(), make_template() (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.11
Nodes (9): _blocks(), epoch_to_datetime(), _int(), summarize(), _usage_counts(), usd_to_micro(), Started, test_epoch_conversion() (+1 more)

### Community 55 - "Community 55"
Cohesion: 0.12
Nodes (19): denials_except(), home_denials(), test_real_agent_sdk_run_creates_a_file_and_is_denied_ssh(), test_read_only_argv_has_only_the_read_tools(), test_read_only_policy_has_no_commands(), test_real_codex_run_creates_a_file_and_cannot_read_ssh(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules() (+11 more)

### Community 56 - "Community 56"
Cohesion: 0.13
Nodes (13): resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, clean(), check_done_when() (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.13
Nodes (24): CommandTestResult, CreateProject, fieldError(), Gate, GATES, loadSettings(), ProjectSettings, saveCommands() (+16 more)

### Community 58 - "Community 58"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 59 - "Community 59"
Cohesion: 0.10
Nodes (10): ApiClient, ApiError, DaemonNotRunning, _detail(), test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host() (+2 more)

### Community 60 - "Community 60"
Cohesion: 0.14
Nodes (15): GitHubClient, GitHubError, create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull() (+7 more)

### Community 61 - "Community 61"
Cohesion: 0.13
Nodes (19): AppRouter(), router, RootLayout(), routes, checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus() (+11 more)

### Community 62 - "Community 62"
Cohesion: 0.12
Nodes (16): test_list_templates(), test_list_templates_needs_the_token(), init(), test_a_copier_failure_is_reported(), test_a_failed_commit_removes_the_repo_and_workspace(), test_a_failed_workspace_empties_an_existing_folder(), test_a_file_as_repo_is_refused(), test_a_git_url_template_records_the_commit() (+8 more)

### Community 63 - "Community 63"
Cohesion: 0.11
Nodes (11): _authenticate(), _convert(), _Envelopes, events(), EventStreams, _send(), _stream(), listener() (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.11
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 65 - "Community 65"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 66 - "Community 66"
Cohesion: 0.10
Nodes (10): create_app(), config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), ensure_home(), home_dir(), Settings (+2 more)

### Community 67 - "Community 67"
Cohesion: 0.11
Nodes (20): keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total() (+12 more)

### Community 68 - "Community 68"
Cohesion: 0.20
Nodes (23): ReviewInputs, run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages(), test_cancelled_is_passed_through(), test_changes_requested_names_the_unmet_item() (+15 more)

### Community 69 - "Community 69"
Cohesion: 0.16
Nodes (17): close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(), stuck() (+9 more)

### Community 70 - "Community 70"
Cohesion: 0.09
Nodes (9): lifespan(), keep_for(), recover_all_integrations(), recover_all_worktrees(), list_workspaces(), WorkspaceRuns, main(), test_bus_of_an_empty_database_starts_at_zero() (+1 more)

### Community 71 - "Community 71"
Cohesion: 0.13
Nodes (12): approve_plan(), generate_plan(), _plans(), GeneratePlan, PlanApproved, PlanStarted, AttemptView, CurrentRun (+4 more)

### Community 72 - "Community 72"
Cohesion: 0.15
Nodes (10): get_ticket(), get_tickets(), put_ticket(), _read(), unblock_ticket(), InvalidTicketView, Note, TicketList (+2 more)

### Community 73 - "Community 73"
Cohesion: 0.10
Nodes (7): billing_for(), ClaudeCliRunner, fake_probe(), test_auth_status_that_is_not_json(), test_linux_needs_bubblewrap_and_socat(), test_macos_is_enforceable_and_others_are_not(), test_native_windows_is_refused()

### Community 74 - "Community 74"
Cohesion: 0.11
Nodes (15): ProjectValidationError, init_project(), _initial_yaml(), InitResult, parse_project(), _populate(), project_dir(), save_project() (+7 more)

### Community 75 - "Community 75"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 76 - "Community 76"
Cohesion: 0.13
Nodes (8): get_settings(), Settings, get_engine(), make_engine(), run(), url(), test_settings_read_the_environment(), test_migrations_create_and_drop_the_schema()

### Community 77 - "Community 77"
Cohesion: 0.20
Nodes (23): consistency_errors(), _location(), parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met() (+15 more)

### Community 78 - "Community 78"
Cohesion: 0.21
Nodes (14): ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note(), test_each_rule_alone_needs_a_person() (+6 more)

### Community 79 - "Community 79"
Cohesion: 0.20
Nodes (20): Usage, done(), feed(), item(), test_a_blocked_network_call_is_a_denial(), test_a_completed_turn_wins_over_earlier_errors(), test_a_failed_patch_changes_nothing(), test_a_failing_command_is_not_a_denial() (+12 more)

### Community 80 - "Community 80"
Cohesion: 0.10
Nodes (5): billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), codex()

### Community 81 - "Community 81"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 82 - "Community 82"
Cohesion: 0.12
Nodes (13): _kept(), esc(), render_planner_prompt(), Existing, _id_errors(), next_id(), _where(), assert_snapshot() (+5 more)

### Community 83 - "Community 83"
Cohesion: 0.15
Nodes (21): PlanProblem, validate_plan(), dashboard(), messages(), test_all_problems_are_reported_at_once(), test_critical_path_skips_done_tickets(), test_cycle_starts_at_its_lowest_id_wherever_the_walk_enters(), test_dashboard_critical_path() (+13 more)

### Community 84 - "Community 84"
Cohesion: 0.09
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 85 - "Community 85"
Cohesion: 0.11
Nodes (7): acquire_lock(), DaemonLock, holder(), LockHeld, _read_pid(), _try_lock(), _unlock()

### Community 86 - "Community 86"
Cohesion: 0.13
Nodes (17): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_clean_strips_ansi_and_crlf() (+9 more)

### Community 87 - "Community 87"
Cohesion: 0.16
Nodes (5): ahead_message(), Delivery, _failed(), _held(), pr_branch()

### Community 88 - "Community 88"
Cohesion: 0.25
Nodes (15): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_attempt_artifacts(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_history_pages_are_stable_under_inserts() (+7 more)

### Community 89 - "Community 89"
Cohesion: 0.19
Nodes (17): gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test(), test_failing_test() (+9 more)

### Community 90 - "Community 90"
Cohesion: 0.12
Nodes (8): _openapi(), health(), Health, create_app(), client(), test_session(), engine(), session()

### Community 91 - "Community 91"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 92 - "Community 92"
Cohesion: 0.17
Nodes (12): ContextInputs, DependencyView, GateFailure, PreviousAttempt, RenderedPrompt, ReviewNote, TicketView, code_map() (+4 more)

### Community 94 - "Community 94"
Cohesion: 0.15
Nodes (9): InvalidPlan, PlannerError, PlanResult, generate_plan(), finish(), _ignore(), read_spec(), check_plan() (+1 more)

### Community 95 - "Community 95"
Cohesion: 0.17
Nodes (14): sort_tickets(), explain_idle(), IdleReason, _ids(), next_ready(), _statuses(), _unmet(), waiting_on() (+6 more)

### Community 96 - "Community 96"
Cohesion: 0.21
Nodes (9): _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state(), test_dirty_checkout_after_a_cut_off_fast_forward_is_left_alone() (+1 more)

### Community 97 - "Community 97"
Cohesion: 0.15
Nodes (7): GateLine, ItemVerdict, ReviewResult, _ignore(), InvalidVerdict, ParsedItem, ParsedVerdict

### Community 98 - "Community 98"
Cohesion: 0.18
Nodes (12): acquire_daemon_lock(), DaemonAlreadyRunning, lock_path(), make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_second_acquire_names_the_holder() (+4 more)

### Community 100 - "Community 100"
Cohesion: 0.16
Nodes (13): RepoDocs, assert_snapshot(), fixture_text(), read_text(), base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries() (+5 more)

### Community 101 - "Community 101"
Cohesion: 0.18
Nodes (12): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_a_huge_body_is_capped(), test_md_escape() (+4 more)

### Community 102 - "Community 102"
Cohesion: 0.18
Nodes (11): require_valid(), critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours(), summary() (+3 more)

### Community 103 - "Community 103"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 104 - "Community 104"
Cohesion: 0.13
Nodes (8): DAEMON_HOST, DAEMON_START_COMMAND, DaemonConnectingPanel(), DaemonDownPanel(), DaemonErrorPanel(), explain(), PanelCard(), RetryProps

### Community 105 - "Community 105"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 106 - "Community 106"
Cohesion: 0.17
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 107 - "Community 107"
Cohesion: 0.28
Nodes (14): auth(), error(), etag(), test_create_project_from_an_unknown_template(), test_create_project_like_spool_init(), test_list_and_get_projects(), test_settings_edit_with_etags(), test_spec_edit_with_etags() (+6 more)

### Community 108 - "Community 108"
Cohesion: 0.10
Nodes (3): stop(), _signal_group(), StreamParser

### Community 109 - "Community 109"
Cohesion: 0.16
Nodes (8): ApiError, delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretValue, SecretView

### Community 110 - "Community 110"
Cohesion: 0.12
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 111 - "Community 111"
Cohesion: 0.15
Nodes (7): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState

### Community 112 - "Community 112"
Cohesion: 0.15
Nodes (5): _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 113 - "Community 113"
Cohesion: 0.18
Nodes (8): _check_not_newer(), connect(), _migrate(), RunLogError, state_db_path(), state_dir(), _statements(), _user_version()

### Community 114 - "Community 114"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 115 - "Community 115"
Cohesion: 0.13
Nodes (4): ResumeTimer, test_cancel_and_close_drop_the_schedule(), test_fires_once_at_reset_plus_a_minute(), test_the_polling_thread_fires_and_a_failing_callback_is_logged()

### Community 116 - "Community 116"
Cohesion: 0.22
Nodes (15): describe(), RuleHit, change(), decide(), test_a_project_list_replaces_the_default(), test_a_rename_hits_on_either_name(), test_delivery_mode(), test_describe_reads_stored_rules() (+7 more)

### Community 117 - "Community 117"
Cohesion: 0.14
Nodes (11): parse_done_when(), DoneItem, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants(), test_done_when_ignores_code_fences() (+3 more)

### Community 118 - "Community 118"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 119 - "Community 119"
Cohesion: 0.16
Nodes (10): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+2 more)

### Community 120 - "Community 120"
Cohesion: 0.13
Nodes (6): MemoryKeyring, stored_key(), test_a_local_endpoint_gets_the_dummy(), test_a_remote_endpoint_uses_the_environment_then_the_keychain(), test_an_unreadable_keychain_means_no_token(), test_store()

### Community 121 - "Community 121"
Cohesion: 0.18
Nodes (6): delete_secret(), secret_status(), SecretStatus, store_secret(), test_empty_values_and_an_unreadable_keychain(), test_environment_wins_over_the_keychain()

### Community 122 - "Community 122"
Cohesion: 0.22
Nodes (10): auth(), etag(), fixture_tickets(), test_conflicting_edit(), test_get_then_put_unchanged_is_byte_identical(), test_list_with_filters(), test_status_changes_follow_the_transition_table(), test_ticket_ids_are_checked_in_the_path() (+2 more)

### Community 123 - "Community 123"
Cohesion: 0.12
Nodes (5): describe(), print_run(), check_command(), describe_source(), list_command()

### Community 124 - "Community 124"
Cohesion: 0.16
Nodes (6): clean_title(), _not_blank(), one_line(), PlannedTicket, PlanOutput, test_one_line_drops_control_and_format_characters()

### Community 125 - "Community 125"
Cohesion: 0.13
Nodes (9): check_gate_command(), gate_env(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused() (+1 more)

### Community 126 - "Community 126"
Cohesion: 0.25
Nodes (14): parse_plan(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store(), test_ids_of_kept_tickets_cannot_be_reused() (+6 more)

### Community 127 - "Community 127"
Cohesion: 0.19
Nodes (13): check_transition(), parse_status(), make(), test_allowed_transitions_pass(), test_critical_path_ties_prefer_lower_ids(), test_disallowed_transition_messages(), test_disallowed_transitions_raise(), test_next_ready_skips_tickets_that_are_not_ready() (+5 more)

### Community 128 - "Community 128"
Cohesion: 0.24
Nodes (11): test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install() (+3 more)

### Community 129 - "Community 129"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 130 - "Community 130"
Cohesion: 0.11
Nodes (5): _client(), sync_command(), describe(), make_runner(), review_command()

### Community 131 - "Community 131"
Cohesion: 0.17
Nodes (5): _deps(), edit_command(), list_command(), set_status_command(), show_command()

### Community 132 - "Community 132"
Cohesion: 0.18
Nodes (8): slugify(), approve_plan(), draft_file_name(), load_existing(), _recorded(), _replace_all(), sha256(), write_plan()

### Community 133 - "Community 133"
Cohesion: 0.20
Nodes (10): FakeRunner, test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file() (+2 more)

### Community 134 - "Community 134"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 135 - "Community 135"
Cohesion: 0.19
Nodes (12): _api_routes(), test_bodies_over_1_mb_are_refused(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token() (+4 more)

### Community 136 - "Community 136"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 137 - "Community 137"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 138 - "Community 138"
Cohesion: 0.21
Nodes (11): test_init_existing_folder(), test_init_reports_every_problem(), test_init_template_ref_needs_a_template(), test_init_then_validate(), test_init_with_a_bad_template_creates_nothing(), test_init_with_a_git_template_prints_the_commit_first(), test_init_with_a_git_template_runs_no_global_git_hooks(), test_init_with_a_local_template() (+3 more)

### Community 139 - "Community 139"
Cohesion: 0.25
Nodes (7): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), _validation_error()

### Community 140 - "Community 140"
Cohesion: 0.20
Nodes (10): parse_worktree_list(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+2 more)

### Community 141 - "Community 141"
Cohesion: 0.16
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 142 - "Community 142"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 143 - "Community 143"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 144 - "Community 144"
Cohesion: 0.22
Nodes (12): AttemptFinishedData, AttemptStartedData, AuthMessage, _Data, EventEnvelope, IntegrateData, LogData, PolicyDecisionData (+4 more)

### Community 145 - "Community 145"
Cohesion: 0.22
Nodes (8): EditConflict, etag_of(), _lock(), read_with_etag(), write_if_match(), test_concurrent_edits_with_the_same_etag_let_one_win(), edit(), test_write_only_when_the_etag_matches()

### Community 146 - "Community 146"
Cohesion: 0.14
Nodes (6): _gate_word(), _items(), render_review_prompt(), review(), finish(), test_each_review_is_its_own_run()

### Community 147 - "Community 147"
Cohesion: 0.12
Nodes (16): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+8 more)

### Community 148 - "Community 148"
Cohesion: 0.22
Nodes (6): generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 149 - "Community 149"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 150 - "Community 150"
Cohesion: 0.13
Nodes (12): FileEdit, ToolCall, load(), parse(), test_api_billing_reports_cost_in_micro_usd(), test_error(), test_extra_tool_in_init_is_a_policy_violation(), test_max_turns() (+4 more)

### Community 151 - "Community 151"
Cohesion: 0.22
Nodes (9): ProcessResult, run_process(), _signal_group(), _stop_tree(), alive(), run(), test_invalid_utf8_and_crlf_are_cleaned_in_the_log(), test_output_cap_cuts_the_log_and_drains_the_process() (+1 more)

### Community 152 - "Community 152"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 153 - "Community 153"
Cohesion: 0.20
Nodes (7): as_record(), _compile(), delivery_mode(), evaluate(), _listed(), path_matches(), PolicyDecision

### Community 154 - "Community 154"
Cohesion: 0.22
Nodes (9): apply_transition(), edit_ticket(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line() (+1 more)

### Community 155 - "Community 155"
Cohesion: 0.22
Nodes (8): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd(), fixture_contract()

### Community 156 - "Community 156"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 157 - "Community 157"
Cohesion: 0.21
Nodes (7): github_token(), store_github_token(), test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins(), test_the_keychain()

### Community 158 - "Community 158"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 159 - "Community 159"
Cohesion: 0.21
Nodes (5): ChangedFile, parse_numstat(), staged_changes(), test_parse_numstat_with_a_rename_and_a_binary(), test_staged_changes_names_both_sides_of_a_rename()

### Community 160 - "Community 160"
Cohesion: 0.27
Nodes (7): auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template()

### Community 161 - "Community 161"
Cohesion: 0.20
Nodes (4): ProjectError, merge(), parse(), read()

### Community 162 - "Community 162"
Cohesion: 0.29
Nodes (5): Base, Item, create_item(), get_item(), list_items()

### Community 163 - "Community 163"
Cohesion: 0.16
Nodes (4): test_health(), Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token()

### Community 164 - "Community 164"
Cohesion: 0.23
Nodes (8): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 165 - "Community 165"
Cohesion: 0.22
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 167 - "Community 167"
Cohesion: 0.33
Nodes (9): make_plan(), test_a_failed_write_leaves_the_old_files(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members(), test_approving_twice_gives_nothing_to_approve() (+1 more)

### Community 168 - "Community 168"
Cohesion: 0.18
Nodes (9): createDemo(), GET, Handler, openDialog(), POST, PUT, renderButton(), SETTINGS (+1 more)

### Community 169 - "Community 169"
Cohesion: 0.29
Nodes (5): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from()

### Community 170 - "Community 170"
Cohesion: 0.38
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 171 - "Community 171"
Cohesion: 0.32
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 172 - "Community 172"
Cohesion: 0.35
Nodes (7): ask_hook(), main(), parse(), receive(), run(), send(), write_file()

### Community 174 - "Community 174"
Cohesion: 0.25
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 175 - "Community 175"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 177 - "Community 177"
Cohesion: 0.25
Nodes (4): id_key(), _and_list(), _find_cycles(), sort_ids()

### Community 178 - "Community 178"
Cohesion: 0.25
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 179 - "Community 179"
Cohesion: 0.33
Nodes (4): test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript()

### Community 180 - "Community 180"
Cohesion: 0.27
Nodes (5): allowed_env(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start(), test_windows_names_match_in_any_case()

### Community 183 - "Community 183"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 184 - "Community 184"
Cohesion: 0.31
Nodes (4): test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 185 - "Community 185"
Cohesion: 0.22
Nodes (5): api_key(), no_parent_key(), stored_key(), test_an_unreadable_keychain_means_no_key(), test_the_key_comes_from_the_environment_then_the_keychain()

### Community 186 - "Community 186"
Cohesion: 0.28
Nodes (5): available_runners(), make_runner(), test_codex_takes_the_endpoint_and_model(), test_the_agent_sdk_takes_the_endpoint_and_model(), test_the_built_in_backends()

### Community 189 - "Community 189"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 190 - "Community 190"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 194 - "Community 194"
Cohesion: 0.46
Nodes (5): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 195 - "Community 195"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 200 - "Community 200"
Cohesion: 0.29
Nodes (4): done_when_items(), render_draft(), to_node(), test_a_title_that_needs_quotes_stays_valid_yaml()

### Community 201 - "Community 201"
Cohesion: 0.43
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 203 - "Community 203"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 204 - "Community 204"
Cohesion: 0.29
Nodes (4): _fail_after_yaml(), test_failed_rename_leaves_nothing(), test_failure_mid_init_leaves_nothing(), test_missing_git_is_reported()

### Community 208 - "Community 208"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `Config`, `InvalidRequest`, `NotRunning` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2048 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **180 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_project()` connect `Community 27` to `Community 0`, `Community 128`, `Community 130`, `Community 2`, `Community 4`, `Community 129`, `Community 7`, `Community 14`, `Community 18`, `Community 148`, `Community 23`, `Community 30`, `Community 32`, `Community 161`, `Community 34`, `Community 38`, `Community 39`, `Community 40`, `Community 170`, `Community 47`, `Community 49`, `Community 62`, `Community 196`, `Community 70`, `Community 199`, `Community 74`, `Community 205`, `Community 78`, `Community 94`, `Community 96`, `Community 106`, `Community 107`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `RunLog` (e.g. with `page_runs()` and `recover_interrupted()`) actually correct?**
  _`RunLog` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `Config` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.030805260313457036 - nodes in this community are weakly interconnected._
- **Why does `RunLog` connect `Community 1` to `Community 32`, `Community 64`, `Community 2`, `Community 98`, `Community 4`, `Community 69`, `Community 70`, `Community 7`, `Community 164`, `Community 13`, `Community 78`, `Community 113`, `Community 50`, `Community 18`, `Community 23`, `Community 88`, `Community 156`, `Community 63`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03438697318007663 - nodes in this community are weakly interconnected._
- **Why does `AgentPolicy` connect `Community 43` to `Community 0`, `Community 68`, `Community 133`, `Community 203`, `Community 19`, `Community 179`, `Community 212`, `Community 55`, `Community 30`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._