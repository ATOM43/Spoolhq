# Graph Report - Project_Manager  (2026-11-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 7453 nodes · 21803 edges · 347 communities (197 shown, 150 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1836 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0d5208b7`
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
- Community 187
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
- Community 207
- Community 208
- Community 209
- Community 210
- Community 211
- Community 212
- Community 213
- Community 214
- Community 215
- Community 338
- Community 339
- Community 340

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 142 edges
2. `RunRegistry` - 105 edges
3. `AgentPolicy` - 103 edges
4. `load_project()` - 94 edges
5. `Transcripts` - 85 edges
6. `FakeRunner` - 82 edges
7. `WorktreeManager` - 82 edges
8. `ClaudeStreamParser` - 71 edges
9. `react` - 64 edges
10. `RunContext` - 61 edges

## Surprising Connections (you probably didn't know these)
- `schema()` --uses--> `Settings`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/core/config.py
- `schema()` --calls--> `create_app()`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/api/app.py
- `integrate()` --calls--> `IntegrationResult`  [INFERRED]
  daemon/tests/services/runloop/test_loop.py → daemon/src/spoolhq/services/runloop/integrator.py
- `runner()` --calls--> `FakeRunner`  [INFERRED]
  daemon/src/spoolhq/devtools/fake_runner.py → daemon/src/spoolhq/services/agents/fake.py
- `test_codex_not_logged_in_says_codex_login()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py

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
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/totals.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/policy.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (347 total, 150 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.02
Nodes (55): agents_command(), describe(), describe_roles(), describe_worktrees(), fail(), hours(), settings(), table() (+47 more)

### Community 1 - "Community 1"
Cohesion: 0.02
Nodes (104): AppRouter(), router, RootLayout(), routes, BODIES, invokeMock, COALESCE_MS, EventSource (+96 more)

### Community 2 - "Community 2"
Cohesion: 0.03
Nodes (113): Artifact, DiffFile, DiffReport, GateReport, load(), PATHS, Report, ReviewReport (+105 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (43): weighted_tokens(), check_path(), format_version(), parse_version(), platform_reason(), probe(), check_worktree(), existing_stubs() (+35 more)

### Community 4 - "Community 4"
Cohesion: 0.03
Nodes (43): DaemonLock, approve(), read_artifact(), reject(), unblock(), _waiting(), _pr_state(), ticket_runs() (+35 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (62): parse_numstat(), staged_changes(), advance(), checked_out(), commit(), conclude_merge(), conflict_files(), create_tag() (+54 more)

### Community 6 - "Community 6"
Cohesion: 0.03
Nodes (44): EventBus, _get(), get_integration(), Integration, IntegrationState, last_integration(), open_integrations(), pull_request_integration() (+36 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (42): keep_for(), _tokens(), _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements() (+34 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (67): Plan, PlanProblem, problemLabel(), useApprovePlan(), useGeneratePlan(), usePlan(), asTyped(), BodyParts (+59 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (50): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), line_counts(), _lines(), result_text(), _usage_counts() (+42 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (33): refusal(), approval_message(), ahead_message(), Delivery, _failed(), _held(), pr_branch(), _result() (+25 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (50): build_argv(), sandbox_settings(), build_argv(), install_dir(), permission_profile(), policy_parts(), refusal(), required_parts() (+42 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (69): cancelJob(), cleanupToast(), CreateRequest, fieldError(), Inspection, inspectRepo(), Job, JobStep (+61 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (56): no_parent_key(), record(), run(), runner(), scenario(), stored_key(), test_a_billing_or_quota_error_blocks(), test_a_denied_call_is_reported_with_the_hooks_reason_and_logged() (+48 more)

### Community 14 - "Community 14"
Cohesion: 0.04
Nodes (50): OpenSettingsLink(), HomePage(), renderHome(), remoteHost(), PATHS, RunAction, useRunAction(), formatUsage() (+42 more)

### Community 15 - "Community 15"
Cohesion: 0.05
Nodes (56): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+48 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (32): id_key(), InvalidPlan, PlanInvalid, PlannedTicket, PlannerError, PlanOutput, PlanResult, generate_plan() (+24 more)

### Community 17 - "Community 17"
Cohesion: 0.05
Nodes (23): ApiClient, ApiError, DaemonNotRunning, _detail(), _dev_fake_runner(), serve(), _serve(), _Server (+15 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (46): root, queryClient, QueryProvider(), cn(), Button(), buttonVariants, Card(), CardAction() (+38 more)

### Community 19 - "Community 19"
Cohesion: 0.05
Nodes (29): find_command(), _kill_tree(), probe(), run(), ProcessResult, run_process(), _signal_group(), _stop_tree() (+21 more)

### Community 20 - "Community 20"
Cohesion: 0.05
Nodes (21): clock(), FakeGates, make_loop(), make(), project(), registry(), transcripts(), worktrees() (+13 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (59): list_tickets(), load_ticket(), save_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read() (+51 more)

### Community 22 - "Community 22"
Cohesion: 0.05
Nodes (44): GatesReport, useCurrentRun(), attemptSummary(), CheckTone, gatesLine(), lastAttempt(), reviewLine(), VERDICT (+36 more)

### Community 23 - "Community 23"
Cohesion: 0.07
Nodes (39): FakeRunner, ReviewInputs, daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges() (+31 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (46): test_an_unreadable_keychain_means_no_key(), assert_gone(), endpoint_runner(), fake_probe(), read_record(), Recorder, run(), runner() (+38 more)

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (48): PlanProblem, _and_list(), validate_plan(), apply_transition(), check_transition(), edit_ticket(), parse_status(), copy_dashboard() (+40 more)

### Community 26 - "Community 26"
Cohesion: 0.06
Nodes (43): default_branch_sha(), DirtyRepoError, ensure_clean(), ensure_no_operation_in_progress(), is_work_tree(), MissingBranchError, operation_in_progress(), OperationInProgressError (+35 more)

### Community 27 - "Community 27"
Cohesion: 0.14
Nodes (40): LocalIntegrator, _assistant(), _init(), _result(), Transcripts, git(), hooked(), call() (+32 more)

### Community 28 - "Community 28"
Cohesion: 0.06
Nodes (25): edit_lock(), EditConflict, etag_of(), read_with_etag(), write_if_match(), Agents, BackendSettings, Budget (+17 more)

### Community 29 - "Community 29"
Cohesion: 0.06
Nodes (17): check_ticket_id(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError, TicketMeta, find_ticket_file() (+9 more)

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (27): PlanError, SchedulerError, TicketEditError, TransitionError, _find_cycles(), require_valid(), sort_ids(), sort_tickets() (+19 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (49): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_a_workspace_can_be_written_before_its_repo(), test_all_errors_are_reported_at_once() (+41 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (43): GateFailure, build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), test_no_map_no_block() (+35 more)

### Community 33 - "Community 33"
Cohesion: 0.09
Nodes (25): service_errors(), approve_ticket(), cancel_run(), current_run(), discard_ticket(), get_diff(), get_gates(), get_review() (+17 more)

### Community 34 - "Community 34"
Cohesion: 0.11
Nodes (44): git_executable(), WorktreeManager, commit_file(), run_git(), branches(), make_read_only(), marker(), real() (+36 more)

### Community 35 - "Community 35"
Cohesion: 0.06
Nodes (22): _force_utf8_streams(), main(), _Log, FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app() (+14 more)

### Community 36 - "Community 36"
Cohesion: 0.09
Nodes (28): require_if_match(), put(), _conflict(), create_project(), _creating(), get_project(), get_settings(), get_spec() (+20 more)

### Community 37 - "Community 37"
Cohesion: 0.07
Nodes (9): _clear_read_only_and_retry(), marker_key(), _norm(), RegisteredWorktree, remove_path(), same_path(), Worktree, WorktreeSession (+1 more)

### Community 38 - "Community 38"
Cohesion: 0.09
Nodes (37): Listener, listeners, openSettings(), SettingsTab, useOpenRequests(), Agents, backendReady(), DaemonSettings (+29 more)

### Community 39 - "Community 39"
Cohesion: 0.07
Nodes (19): _header(), _path(), _split_files(), trim_diff(), GateLine, ItemVerdict, ReviewResult, _gate_word() (+11 more)

### Community 40 - "Community 40"
Cohesion: 0.07
Nodes (20): check_command(), check_tool(), make_hook(), pre_tool_use(), relative_pattern(), stop(), home(), policy() (+12 more)

### Community 41 - "Community 41"
Cohesion: 0.06
Nodes (41): engines, node, name, packageManager, private, type, version, description (+33 more)

### Community 42 - "Community 42"
Cohesion: 0.09
Nodes (29): ChangedFile, decide(), _user_approved(), as_record(), _compile(), delivery_mode(), describe(), evaluate() (+21 more)

### Community 43 - "Community 43"
Cohesion: 0.09
Nodes (23): ProjectError, ProjectValidationError, Project, has_spec(), init_project(), _initial_yaml(), InitResult, list_workspaces() (+15 more)

### Community 44 - "Community 44"
Cohesion: 0.07
Nodes (5): AgentSdkRunner, policy_parts(), billing_error(), CliTransport, SdkRun

### Community 45 - "Community 45"
Cohesion: 0.14
Nodes (28): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+20 more)

### Community 46 - "Community 46"
Cohesion: 0.10
Nodes (29): fake_backend(), fake_graphify(), free_port(), git_identity(), isolated_git(), keychain(), no_graphify(), projects_dir() (+21 more)

### Community 47 - "Community 47"
Cohesion: 0.09
Nodes (20): run_log(), settings(), workspace(), _artifact(), get_ticket(), get_tickets(), post_ticket(), put_ticket() (+12 more)

### Community 48 - "Community 48"
Cohesion: 0.09
Nodes (27): child_env(), denials_except(), home_denials(), parent_env(), test_a_custom_endpoint_gets_spoolhqs_token_and_no_login(), test_api_billing_keeps_only_the_api_key(), test_child_env_is_an_allowlist(), test_default_mode_needs_the_scrub_variable_and_no_prompts() (+19 more)

### Community 49 - "Community 49"
Cohesion: 0.06
Nodes (17): allowed_env(), api_key(), child_env(), token_var(), delete_secret(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start() (+9 more)

### Community 50 - "Community 50"
Cohesion: 0.09
Nodes (25): cap_excerpt(), keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec() (+17 more)

### Community 51 - "Community 51"
Cohesion: 0.15
Nodes (26): Merging, kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt() (+18 more)

### Community 52 - "Community 52"
Cohesion: 0.14
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 53 - "Community 53"
Cohesion: 0.12
Nodes (26): RunRegistry, plant_repo_settings(), repo(), checkpoint(), jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage() (+18 more)

### Community 54 - "Community 54"
Cohesion: 0.15
Nodes (30): add(), auth(), edit(), etag(), fixture_tickets(), test_a_cli_and_an_api_create_at_once_get_different_ids(), test_a_held_tickets_lock_fails_with_a_fixed_message(), test_a_new_ticket_gets_the_next_number_and_its_file() (+22 more)

### Community 55 - "Community 55"
Cohesion: 0.10
Nodes (19): loader(), CheckResult, load_contract(), _message(), parse_contract(), _Strict, TemplateCommands, TemplateContract (+11 more)

### Community 56 - "Community 56"
Cohesion: 0.11
Nodes (13): gate_env(), resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when() (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (18): ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note(), test_each_rule_alone_needs_a_person() (+10 more)

### Community 58 - "Community 58"
Cohesion: 0.10
Nodes (24): diff_report(), DiffFile, DiffReport, _file(), GateReport, gates_report(), GatesReport, _header_path() (+16 more)

### Community 59 - "Community 59"
Cohesion: 0.09
Nodes (17): dumper(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node() (+9 more)

### Community 60 - "Community 60"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 61 - "Community 61"
Cohesion: 0.12
Nodes (26): _clean_line(), commit_message(), branch(), git_out(), head(), _squash(), _stage_link(), test_advance_fast_forwards_the_checked_out_branch() (+18 more)

### Community 62 - "Community 62"
Cohesion: 0.13
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _control(), discard_command() (+7 more)

### Community 63 - "Community 63"
Cohesion: 0.09
Nodes (20): useDismissJob(), useInterruptedRun(), MAX_CARDS, NeedsYouCard, needsYouCards(), NeedsYouKind, sentence(), TicketLike (+12 more)

### Community 64 - "Community 64"
Cohesion: 0.12
Nodes (18): AgentRunner, adapter(), AdapterCase, agent_sdk(), claude_cli(), codex_cli(), fake(), run() (+10 more)

### Community 65 - "Community 65"
Cohesion: 0.24
Nodes (23): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+15 more)

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (21): cache_dir(), refresh(), FakeGraphify, builds(), pointer(), source(), test_a_busy_cache_gives_no_map(), test_a_cache_from_another_version_is_discarded() (+13 more)

### Community 67 - "Community 67"
Cohesion: 0.08
Nodes (5): billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), test_real_codex_run_creates_a_file_and_cannot_read_ssh()

### Community 68 - "Community 68"
Cohesion: 0.09
Nodes (8): available_runners(), backend_names(), make_runner(), billing_for(), ClaudeCliRunner, test_codex_takes_the_endpoint_and_model(), test_the_agent_sdk_takes_the_endpoint_and_model(), test_the_built_in_backends()

### Community 69 - "Community 69"
Cohesion: 0.13
Nodes (20): capture(), capture(), on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files() (+12 more)

### Community 70 - "Community 70"
Cohesion: 0.16
Nodes (18): close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(), stuck() (+10 more)

### Community 71 - "Community 71"
Cohesion: 0.13
Nodes (22): Agents, useAgents(), ProjectDetail, ProjectSummary, useProject(), useProjects(), loadSpec(), saveSpec() (+14 more)

### Community 72 - "Community 72"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 73 - "Community 73"
Cohesion: 0.12
Nodes (27): test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_cache_reads_count_a_tenth_toward_weighted_tokens(), test_empty_folder_left_by_an_uncommitted_attempt_is_reused(), test_ended_run_takes_no_attempts(), test_event_with_an_attempt_of_another_run_is_refused() (+19 more)

### Community 74 - "Community 74"
Cohesion: 0.09
Nodes (13): _read(), show_command(), ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, PreviousAttempt (+5 more)

### Community 75 - "Community 75"
Cohesion: 0.13
Nodes (16): _area_entries(), expand_index(), _inside(), _read(), read_repo_docs(), read_text(), decisions_block(), entry() (+8 more)

### Community 76 - "Community 76"
Cohesion: 0.13
Nodes (18): fetch(), github_repo(), push(), bare(), git(), _ssh_commands(), test_a_push_behind_the_remote_is_moved_not_forced(), test_a_refused_push_raises_with_the_hook_output() (+10 more)

### Community 77 - "Community 77"
Cohesion: 0.18
Nodes (17): auth(), _ended(), finished(), post(), refused(), test_a_failing_test_command_and_its_rollback(), test_a_project_being_created_is_reported_as_creating(), test_a_read_only_path_the_rollback_cant_delete_is_listed() (+9 more)

### Community 78 - "Community 78"
Cohesion: 0.10
Nodes (21): state_db_path(), state_dir(), _make_attempt_dir(), raw(), run_log(), test_closed_log_refuses_calls(), test_committed_events_are_published_in_order(), test_concurrent_appends_get_increasing_ids() (+13 more)

### Community 79 - "Community 79"
Cohesion: 0.08
Nodes (8): run_project(), sandbox_which(), set_identity(), anonymise(), logged_in(), test_real_run_creates_a_file_and_is_denied_python(), test_real_review_names_the_missing_test(), schema()

### Community 80 - "Community 80"
Cohesion: 0.18
Nodes (18): create(), git_state(), jobs_for(), snapshot(), source_fields(), states(), test_a_commit_without_an_identity_fails_and_rolls_back(), test_a_failing_test_command_names_its_field() (+10 more)

### Community 81 - "Community 81"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 82 - "Community 82"
Cohesion: 0.11
Nodes (10): _authenticate(), _convert(), _Envelopes, events(), EventStreams, _send(), _stream(), listener() (+2 more)

### Community 83 - "Community 83"
Cohesion: 0.13
Nodes (12): _check(), check_secret(), SecretCheck, store_secret(), answer(), handler(), fail(), test_a_redirect_is_not_followed() (+4 more)

### Community 84 - "Community 84"
Cohesion: 0.12
Nodes (5): Job, CreationJobs, UnknownJobError, CreateProject, StackCommands

### Community 85 - "Community 85"
Cohesion: 0.10
Nodes (13): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+5 more)

### Community 86 - "Community 86"
Cohesion: 0.09
Nodes (7): sync(), version(), GitHubSync, Version, health(), Health, create_app()

### Community 87 - "Community 87"
Cohesion: 0.09
Nodes (7): _generated_at(), plan_overview(), PlanOverview, _invalid_problem(), plan_problems(), _Job, PlanJobs

### Community 88 - "Community 88"
Cohesion: 0.08
Nodes (14): builtin_fixture(), client(), fake_claude_cmd(), fake_codex_cmd(), fake_sdk_cmd(), git_repo(), make_git_template(), make_github_remote() (+6 more)

### Community 89 - "Community 89"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 90 - "Community 90"
Cohesion: 0.13
Nodes (12): _check_branch(), _check_existing(), _check_new(), check_request(), Checked, _commands(), CreationError, current_branch() (+4 more)

### Community 91 - "Community 91"
Cohesion: 0.20
Nodes (23): consistency_errors(), _location(), parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met() (+15 more)

### Community 92 - "Community 92"
Cohesion: 0.12
Nodes (18): build_excerpt(), take(), clean(), _clip(), failing_tests(), first_failure(), _priority(), split_lines() (+10 more)

### Community 94 - "Community 94"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 95 - "Community 95"
Cohesion: 0.17
Nodes (19): gates(), test_all_passing(), test_an_unset_command_is_skipped_and_the_run_still_passes(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+11 more)

### Community 96 - "Community 96"
Cohesion: 0.15
Nodes (14): _check_decisions(), _decisions(), folders(), _script(), test_a_consistent_fixture_passes(), test_a_duplicated_number_fails(), test_a_mismatched_title_fails(), test_a_missing_number_fails() (+6 more)

### Community 97 - "Community 97"
Cohesion: 0.21
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 98 - "Community 98"
Cohesion: 0.21
Nodes (20): plan(), snapshot(), test_a_backend_that_cant_exclude_the_repos_settings_is_refused(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused(), test_a_run_that_does_not_complete_writes_nothing(), test_a_valid_retry_writes_the_plan(), test_an_unknown_project_is_refused() (+12 more)

### Community 99 - "Community 99"
Cohesion: 0.26
Nodes (18): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_a_run_finishing_between_pages_is_not_repeated(), test_attempt_artifacts(), test_attempt_reports(), test_current_with_no_run() (+10 more)

### Community 100 - "Community 100"
Cohesion: 0.09
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 101 - "Community 101"
Cohesion: 0.12
Nodes (10): clean_title(), _not_blank(), one_line(), check_slug(), parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_one_line_drops_control_and_format_characters() (+2 more)

### Community 102 - "Community 102"
Cohesion: 0.20
Nodes (12): createItem(), getItem(), listItems(), Item, NewItem, ItemList(), CreateItemForm(), submit() (+4 more)

### Community 103 - "Community 103"
Cohesion: 0.18
Nodes (12): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_a_hooks_path_outside_the_repo_never_runs(), test_default_hooks_folder_never_runs() (+4 more)

### Community 104 - "Community 104"
Cohesion: 0.15
Nodes (9): ApiError, problem_view(), cancel_job(), dismiss_job(), get_job(), _jobs(), JobView, RollbackView (+1 more)

### Community 105 - "Community 105"
Cohesion: 0.12
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 106 - "Community 106"
Cohesion: 0.15
Nodes (21): AgentDeniedData, AgentFileEditData, AgentMessageData, AgentRateLimitData, AgentToolCallData, AgentToolResultData, AgentUsageData, AgentWarningData (+13 more)

### Community 107 - "Community 107"
Cohesion: 0.11
Nodes (7): dotted_path(), format_errors(), _message(), _model_at(), _number(), split_error(), test_split_error()

### Community 108 - "Community 108"
Cohesion: 0.27
Nodes (15): check(), refused(), request(), test_a_duplicate_name_is_refused(), test_a_good_name_passes(), test_a_new_repo_needs_a_new_or_empty_folder(), test_a_symlinked_target_is_refused(), test_a_template_only_for_a_template_source() (+7 more)

### Community 109 - "Community 109"
Cohesion: 0.25
Nodes (15): auth(), error(), etag(), test_an_invalid_project_yaml_is_listed_with_its_first_problem(), test_list_and_get_projects(), test_project_detail_says_why_nothing_can_run(), test_settings_edit_with_etags(), test_spec_edit_with_etags() (+7 more)

### Community 110 - "Community 110"
Cohesion: 0.20
Nodes (10): auth(), _check_reports(), dev_client(), dev_project(), run_next(), test_a_hand_added_ticket_runs_without_a_spec(), test_a_scenario_writing_outside_the_worktree_blocks(), test_blocked_fails_the_gates_every_time() (+2 more)

### Community 111 - "Community 111"
Cohesion: 0.19
Nodes (14): create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull(), PullRequest, Review (+6 more)

### Community 112 - "Community 112"
Cohesion: 0.23
Nodes (17): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+9 more)

### Community 113 - "Community 113"
Cohesion: 0.25
Nodes (15): auth(), get_plan(), plan_client(), test_a_clean_approve_makes_the_drafts_ready(), test_an_invalid_ticket_file_is_a_problem(), test_approve_with_problems_is_409_and_changes_nothing(), test_each_problem_has_its_code_and_ticket_ids(), test_every_plan_route_needs_the_token() (+7 more)

### Community 114 - "Community 114"
Cohesion: 0.21
Nodes (9): _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state(), test_dirty_checkout_after_a_cut_off_fast_forward_is_left_alone() (+1 more)

### Community 115 - "Community 115"
Cohesion: 0.18
Nodes (12): acquire_daemon_lock(), DaemonAlreadyRunning, lock_path(), make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_second_acquire_names_the_holder() (+4 more)

### Community 116 - "Community 116"
Cohesion: 0.18
Nodes (3): summarize(), CodexStreamParser, _int()

### Community 117 - "Community 117"
Cohesion: 0.13
Nodes (3): GitHubClient, GitHubError, _message()

### Community 118 - "Community 118"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 120 - "Community 120"
Cohesion: 0.18
Nodes (12): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_a_huge_body_is_capped(), test_md_escape() (+4 more)

### Community 121 - "Community 121"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 122 - "Community 122"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 123 - "Community 123"
Cohesion: 0.20
Nodes (10): test_billing_errors_are_recognised(), generate(), test_a_copier_failure_is_reported(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_template_without_a_test_command_is_rejected(), test_an_empty_existing_folder_is_used(), test_tasks_from_an_include_are_refused_by_copier_and_never_run() (+2 more)

### Community 124 - "Community 124"
Cohesion: 0.19
Nodes (15): is_git_url(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder(), test_a_local_git_repository_at_a_ref() (+7 more)

### Community 125 - "Community 125"
Cohesion: 0.20
Nodes (10): describe_graphify(), _build(), CodeMap, _current(), _drop(), _refresh(), _remove_unused(), _save() (+2 more)

### Community 126 - "Community 126"
Cohesion: 0.21
Nodes (12): test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install() (+4 more)

### Community 127 - "Community 127"
Cohesion: 0.21
Nodes (14): test_a_git_template_check_runs_no_global_git_hooks(), test_init_an_empty_repo_on_a_branch(), test_init_an_existing_repo_then_validate(), test_init_existing_folder(), test_init_from_a_git_template_at_a_ref(), test_init_from_a_local_folder_template(), test_init_from_a_template_fills_its_commands(), test_init_refuses_a_bad_branch_name() (+6 more)

### Community 128 - "Community 128"
Cohesion: 0.16
Nodes (9): check_secret_route(), delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretTest, SecretValue (+1 more)

### Community 129 - "Community 129"
Cohesion: 0.15
Nodes (5): _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 130 - "Community 130"
Cohesion: 0.19
Nodes (12): settings_files(), _dependencies(), detect_commands(), DetectedCommands, _first(), _from_package_json(), _from_pyproject(), _from_rules() (+4 more)

### Community 131 - "Community 131"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 132 - "Community 132"
Cohesion: 0.24
Nodes (10): assert_no_checks_worktree(), check_command(), jobs_for(), python_repo(), request(), test_a_failing_baseline_is_the_repos_own_failure(), test_cancel_removes_the_checks_worktree(), test_checks_leave_the_checkout_untouched() (+2 more)

### Community 133 - "Community 133"
Cohesion: 0.12
Nodes (5): code(), _PromptLoader, PromptTemplate, render_template(), _template_line()

### Community 134 - "Community 134"
Cohesion: 0.15
Nodes (6): check_safe(), init_repo(), _record_git_source(), render(), unsafe_message(), generated()

### Community 135 - "Community 135"
Cohesion: 0.13
Nodes (7): create_app(), lifespan(), _openapi(), check_git(), recover_all_integrations(), recover_all_worktrees(), test_create_app_uses_token_file()

### Community 136 - "Community 136"
Cohesion: 0.17
Nodes (9): CurrentRun, Discarded, MergedView, PhaseLine, PolicyView, Reject, RuleHitView, RunList (+1 more)

### Community 137 - "Community 137"
Cohesion: 0.17
Nodes (6): _Cancelled, checks_worktree(), _Failed, _remove_worktree(), Runner, Step

### Community 138 - "Community 138"
Cohesion: 0.15
Nodes (10): parse_done_when(), DoneItem, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants(), test_done_when_ignores_code_fences() (+2 more)

### Community 139 - "Community 139"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 140 - "Community 140"
Cohesion: 0.25
Nodes (10): inspect_repo(), test_a_clean_repo(), test_a_dirty_repo_lists_its_files(), test_a_github_origin(), test_a_symlinked_justfile_is_not_read(), test_agent_settings_are_listed(), test_detected_commands(), test_inspect_never_runs_a_command() (+2 more)

### Community 141 - "Community 141"
Cohesion: 0.25
Nodes (9): approve_plan(), generate_plan(), get_plan(), _plans(), GeneratePlan, PlanApproved, PlanProblemView, PlanStarted (+1 more)

### Community 142 - "Community 142"
Cohesion: 0.18
Nodes (8): slugify(), ticket_ids(), _body(), create_ticket(), NewTicket, _tickets_lock(), _used_ids(), TicketLockedError

### Community 143 - "Community 143"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 144 - "Community 144"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 145 - "Community 145"
Cohesion: 0.11
Nodes (18): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+10 more)

### Community 146 - "Community 146"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 147 - "Community 147"
Cohesion: 0.20
Nodes (10): parse_worktree_list(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+2 more)

### Community 148 - "Community 148"
Cohesion: 0.17
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 149 - "Community 149"
Cohesion: 0.21
Nodes (12): _api_routes(), test_bodies_over_1_mb_are_refused(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token() (+4 more)

### Community 150 - "Community 150"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 151 - "Community 151"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 152 - "Community 152"
Cohesion: 0.27
Nodes (7): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), _validation_error()

### Community 153 - "Community 153"
Cohesion: 0.13
Nodes (6): acquire_lock(), holder(), LockHeld, _read_pid(), _try_lock(), _unlock()

### Community 154 - "Community 154"
Cohesion: 0.23
Nodes (12): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning() (+4 more)

### Community 155 - "Community 155"
Cohesion: 0.22
Nodes (7): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from(), test_testing_a_secret_needs_the_token_and_a_known_name(), test_testing_a_secret_never_returns_or_logs_it()

### Community 156 - "Community 156"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 157 - "Community 157"
Cohesion: 0.16
Nodes (7): escape_closing_tag(), fenced(), _kept(), esc(), test_escaping_is_case_insensitive_and_spacing_tolerant(), example(), test_task_md_example_project_yaml_validates()

### Community 158 - "Community 158"
Cohesion: 0.18
Nodes (6): test_client_reports_a_server_that_is_not_spoolhq(), test_serve_logs_the_fake_runner_and_passes_its_agents(), test_serve_refuses_non_loopback_host(), test_serve_refuses_the_fake_runner_frozen_or_unknown(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 159 - "Community 159"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 160 - "Community 160"
Cohesion: 0.21
Nodes (7): github_token(), store_github_token(), test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins(), test_the_keychain()

### Community 161 - "Community 161"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 162 - "Community 162"
Cohesion: 0.19
Nodes (6): _lookup(), read_secret(), secret_status(), SecretStatus, test_empty_values_and_an_unreadable_keychain(), test_environment_wins_over_the_keychain()

### Community 164 - "Community 164"
Cohesion: 0.23
Nodes (8): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 165 - "Community 165"
Cohesion: 0.30
Nodes (10): make_plan(), test_a_failed_write_leaves_the_old_files(), test_a_title_that_needs_quotes_stays_valid_yaml(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members() (+2 more)

### Community 166 - "Community 166"
Cohesion: 0.17
Nodes (5): changed_settings(), is_settings_path(), only_spoolhq_settings(), test_settings_files_and_changed_settings(), test_settings_paths()

### Community 168 - "Community 168"
Cohesion: 0.18
Nodes (8): check_gate_command(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused(), test_unclosed_quote_is_refused()

### Community 170 - "Community 170"
Cohesion: 0.24
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 171 - "Community 171"
Cohesion: 0.23
Nodes (5): test_health(), auth(), test_a_refused_path_names_the_path_field(), test_inspect_a_repo(), test_inspect_needs_the_token()

### Community 172 - "Community 172"
Cohesion: 0.26
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 173 - "Community 173"
Cohesion: 0.32
Nodes (5): merge_one(), run(), show(), test_existing_notes_files_are_only_appended_to(), test_missing_notes_files_are_created_at_the_first_merge()

### Community 174 - "Community 174"
Cohesion: 0.38
Nodes (8): add_tickets(), test_a_starter_spec_is_left_out_and_a_real_one_renders_as_before(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 175 - "Community 175"
Cohesion: 0.32
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 176 - "Community 176"
Cohesion: 0.21
Nodes (4): Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token(), test_agents_reports_the_fake_runner()

### Community 177 - "Community 177"
Cohesion: 0.44
Nodes (7): auth(), _get(), _log(), test_1200_events_come_in_pages_of_500_500_and_200(), test_a_limit_over_2000_is_refused(), test_attempt_n_gives_its_window_with_the_run_level_events(), test_unknown_run_or_attempt_is_404()

### Community 178 - "Community 178"
Cohesion: 0.22
Nodes (3): get_engine(), make_engine(), test_migrations_create_and_drop_the_schema()

### Community 179 - "Community 179"
Cohesion: 0.24
Nodes (3): summary(), test_a_report_without_known_sections_is_empty(), test_keeps_the_map_and_drops_the_rest()

### Community 180 - "Community 180"
Cohesion: 0.27
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 182 - "Community 182"
Cohesion: 0.24
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 183 - "Community 183"
Cohesion: 0.38
Nodes (4): agents(), AgentsView, BackendView, GraphifyView

### Community 184 - "Community 184"
Cohesion: 0.33
Nodes (4): inspect(), DetectedCommandsView, InspectRepo, RepoInspectionView

### Community 185 - "Community 185"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 186 - "Community 186"
Cohesion: 0.31
Nodes (4): App(), root, HomePage(), react-dom

### Community 187 - "Community 187"
Cohesion: 0.27
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 188 - "Community 188"
Cohesion: 0.36
Nodes (3): list_templates(), TemplateCommandsView, TemplateView

### Community 189 - "Community 189"
Cohesion: 0.47
Nodes (4): Item, create_item(), get_item(), list_items()

### Community 190 - "Community 190"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 191 - "Community 191"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 192 - "Community 192"
Cohesion: 0.36
Nodes (5): just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 196 - "Community 196"
Cohesion: 0.36
Nodes (4): client(), test_session(), engine(), session()

### Community 197 - "Community 197"
Cohesion: 0.32
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 199 - "Community 199"
Cohesion: 0.25
Nodes (5): _cycle(), _duplicate(), _estimate(), revised(), test_invalid_output_is_retried_with_the_errors_then_fails()

### Community 201 - "Community 201"
Cohesion: 0.29
Nodes (3): dev_agents(), runner(), make()

### Community 202 - "Community 202"
Cohesion: 0.43
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 204 - "Community 204"
Cohesion: 0.48
Nodes (3): manager(), wt_repo(), wt_root()

### Community 207 - "Community 207"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 209 - "Community 209"
Cohesion: 0.40
Nodes (4): Markdown(), PLUGINS, react-markdown, remark-gfm

### Community 210 - "Community 210"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 214 - "Community 214"
Cohesion: 0.67
Nodes (3): dependencies, react, react-dom

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `Config`, `InvalidRequest`, `NotRunning` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2454 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **150 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 6` to `Community 0`, `Community 3`, `Community 4`, `Community 5`, `Community 7`, `Community 10`, `Community 142`, `Community 16`, `Community 20`, `Community 27`, `Community 159`, `Community 164`, `Community 42`, `Community 47`, `Community 177`, `Community 52`, `Community 53`, `Community 54`, `Community 57`, `Community 65`, `Community 195`, `Community 69`, `Community 70`, `Community 78`, `Community 82`, `Community 85`, `Community 99`, `Community 115`, `Community 119`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `RunLog` (e.g. with `recover_interrupted()` and `RunRegistry`) actually correct?**
  _`RunLog` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `Config` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.022885400494508653 - nodes in this community are weakly interconnected._
- **Why does `load_project()` connect `Community 31` to `Community 0`, `Community 4`, `Community 135`, `Community 139`, `Community 142`, `Community 16`, `Community 20`, `Community 23`, `Community 27`, `Community 28`, `Community 36`, `Community 43`, `Community 45`, `Community 174`, `Community 47`, `Community 51`, `Community 52`, `Community 53`, `Community 57`, `Community 192`, `Community 65`, `Community 74`, `Community 205`, `Community 79`, `Community 80`, `Community 87`, `Community 215`, `Community 98`, `Community 109`, `Community 110`, `Community 114`, `Community 126`, `Community 127`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `RunRegistry` (e.g. with `RunLogError` and `RunLog`) actually correct?**
  _`RunRegistry` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.01771091220719863 - nodes in this community are weakly interconnected._