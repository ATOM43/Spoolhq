# Graph Report - Project_Manager  (2026-11-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 7306 nodes · 21175 edges · 350 communities (195 shown, 155 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1761 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `104df2dc`
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
- Community 206
- Community 207
- Community 208
- Community 209
- Community 210
- Community 211
- Community 213
- Community 339
- Community 340
- Community 341

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 139 edges
2. `load_project()` - 93 edges
3. `RunRegistry` - 86 edges
4. `WorktreeManager` - 80 edges
5. `AgentPolicy` - 80 edges
6. `FakeRunner` - 77 edges
7. `ClaudeStreamParser` - 72 edges
8. `react` - 64 edges
9. `Transcripts` - 59 edges
10. `build_implementer_prompt()` - 58 edges

## Surprising Connections (you probably didn't know these)
- `schema()` --calls--> `create_app()`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/api/app.py
- `test_client_connection_refused()` --calls--> `ApiClient`  [INFERRED]
  daemon/tests/cli/test_main.py → daemon/src/spoolhq/cli/client.py
- `schema()` --uses--> `Settings`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/core/config.py
- `unblock()` --calls--> `RunLoopError`  [INFERRED]
  daemon/tests/api/test_tickets.py → daemon/src/spoolhq/services/runloop/model.py
- `test_error_without_stderr_has_no_colon()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py

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

## Communities (350 total, 155 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (51): agents_command(), describe(), describe_roles(), describe_worktrees(), fail(), hours(), settings(), table() (+43 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (109): Artifact, DiffFile, DiffReport, GateReport, GatesReport, load(), PATHS, Report (+101 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (83): COALESCE_MS, EventSource, lastSeq, Probe(), subscribe, useProjectEvents(), RunRow, useRunHistory() (+75 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (79): _body(), create_ticket(), NewTicket, PlanError, PlanProblem, SchedulerError, TicketEditError, TicketLockedError (+71 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (79): parse_done_when(), run_editor(), start_edit(), TicketEdit, source_name(), TicketError, TicketValidationError, DoneItem (+71 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (43): weighted_tokens(), policy_parts(), format_version(), parse_version(), probe(), check_worktree(), existing_stubs(), expand_home() (+35 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (67): Plan, PlanProblem, problemLabel(), useApprovePlan(), useGeneratePlan(), usePlan(), asTyped(), BodyParts (+59 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (33): approval_message(), _result(), HoldForIntegration, IntegrationResult, Integrator, agent_stopped(), attempt_once(), check_resolved() (+25 more)

### Community 8 - "Community 8"
Cohesion: 0.04
Nodes (21): keep_for(), check_ticket_id(), _user_approved(), _set_run(), page_events(), _starts(), attempt_dir_name(), _make_attempt_dir() (+13 more)

### Community 9 - "Community 9"
Cohesion: 0.03
Nodes (47): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, BODIES (+39 more)

### Community 10 - "Community 10"
Cohesion: 0.04
Nodes (33): ProcessResult, run_process(), _signal_group(), _stop_tree(), _wait(), is_test(), main(), oversized() (+25 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (57): Agents, useAgents(), checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning (+49 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (27): decode_cursor(), encode_cursor(), EventPage, page_runs(), RunPage, RunStats, _check_count(), AttemptStatus (+19 more)

### Community 13 - "Community 13"
Cohesion: 0.05
Nodes (52): RunLimits, useCurrentRun(), useRunLimits(), nextAttemptLine(), NOTE_MAX, NoteKind, useSendNote(), NoteDialog() (+44 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (50): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), line_counts(), _lines(), result_text(), _usage_counts() (+42 more)

### Community 15 - "Community 15"
Cohesion: 0.05
Nodes (24): RollbackView, StepView, init(), Job, roll_back(), Rollback, Runner, Step (+16 more)

### Community 16 - "Community 16"
Cohesion: 0.05
Nodes (46): _header(), _path(), _split_files(), trim_diff(), GateLine, ItemVerdict, ReviewResult, _gate_word() (+38 more)

### Community 17 - "Community 17"
Cohesion: 0.05
Nodes (59): state_db_path(), state_dir(), seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first() (+51 more)

### Community 18 - "Community 18"
Cohesion: 0.05
Nodes (23): ApiClient, ApiError, DaemonNotRunning, _detail(), _dev_fake_runner(), serve(), _serve(), _Server (+15 more)

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (12): approve(), reject(), unblock(), _waiting(), RunLoop, Active, Flags, NotFoundError (+4 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (46): api_key(), no_parent_key(), test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript(), record(), run() (+38 more)

### Community 21 - "Community 21"
Cohesion: 0.04
Nodes (35): test_health(), Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token(), test_agents_reports_the_fake_runner(), builtin_fixture(), client(), clock() (+27 more)

### Community 22 - "Community 22"
Cohesion: 0.07
Nodes (43): NewProjectButton(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants, Card(), CardAction() (+35 more)

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (28): pr_branch(), _branch_of(), finish(), _hint(), last_merged(), publish_tag(), recover_integrations(), tag_name() (+20 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (33): require_if_match(), run_log(), settings(), workspace(), put(), _conflict(), create_project(), _creating() (+25 more)

### Community 25 - "Community 25"
Cohesion: 0.06
Nodes (44): ProjectDetail, ProjectSummary, useProject(), useProjects(), loadSpec(), saveSpec(), SPEC_FILE, SpecFile (+36 more)

### Community 26 - "Community 26"
Cohesion: 0.08
Nodes (49): cancelJob(), cleanupToast(), CreateRequest, fieldError(), Job, JobStep, POLL_MS, startJob() (+41 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (42): assert_gone(), endpoint_runner(), fake_probe(), read_record(), Recorder, run(), runner(), test_a_custom_endpoint_never_gets_the_users_login() (+34 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (25): service_errors(), approve_ticket(), _artifact(), cancel_run(), current_run(), discard_ticket(), get_diff(), get_gates() (+17 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (33): decide(), read_artifact(), _pr_state(), ticket_runs(), TicketGit, TicketRuns, retries_used(), NotBlockedError (+25 more)

### Community 30 - "Community 30"
Cohesion: 0.10
Nodes (43): GateFailure, build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), test_no_map_no_block() (+35 more)

### Community 31 - "Community 31"
Cohesion: 0.07
Nodes (23): slugify(), branch_name(), _recover_one(), RecoveryEntry, check_git_version(), command_error(), disabled_hooks_dir(), git_env() (+15 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (45): git_executable(), WorktreeManager, commit_file(), run_git(), branches(), make_read_only(), marker(), real() (+37 more)

### Community 33 - "Community 33"
Cohesion: 0.07
Nodes (23): dump(), dumper(), loader(), merge(), parse(), read(), to_node(), to_plain() (+15 more)

### Community 34 - "Community 34"
Cohesion: 0.08
Nodes (22): check_gate_command(), gate_env(), resolve_program(), split_command(), DoneWhenCheck, GateFailureData, GateResult, GateRun (+14 more)

### Community 35 - "Community 35"
Cohesion: 0.05
Nodes (16): EventBus, Subscription, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get() (+8 more)

### Community 36 - "Community 36"
Cohesion: 0.07
Nodes (10): _clear_read_only_and_retry(), marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, remove_path(), same_path(), Worktree (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.09
Nodes (38): Listener, listeners, openSettings(), SettingsTab, useOpenRequests(), Agents, backendReady(), DaemonSettings (+30 more)

### Community 38 - "Community 38"
Cohesion: 0.14
Nodes (44): load_project(), del_path(), errors_for(), set_path(), test_a_template_must_be_a_block(), test_a_workspace_can_be_written_before_its_repo(), test_all_errors_are_reported_at_once(), test_bad_protected_path_patterns_are_refused() (+36 more)

### Community 39 - "Community 39"
Cohesion: 0.11
Nodes (21): Delivery, RunRegistry, make_loop(), ManualClock, decisions(), log_of(), remote(), run_case() (+13 more)

### Community 40 - "Community 40"
Cohesion: 0.09
Nodes (25): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+17 more)

### Community 41 - "Community 41"
Cohesion: 0.07
Nodes (15): billing_for(), ClaudeCliRunner, platform_reason(), BackendInfo, test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line() (+7 more)

### Community 42 - "Community 42"
Cohesion: 0.06
Nodes (41): engines, node, name, packageManager, private, type, version, description (+33 more)

### Community 43 - "Community 43"
Cohesion: 0.20
Nodes (31): LocalIntegrator, Transcripts, git(), hooked(), call(), kinds(), _linking(), local() (+23 more)

### Community 44 - "Community 44"
Cohesion: 0.09
Nodes (35): ensure_clean(), status_entries(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes() (+27 more)

### Community 45 - "Community 45"
Cohesion: 0.15
Nodes (29): assert_refused(), read_only(), read_record(), refused_message(), run(), runner(), temps(), test_a_custom_endpoint_never_gets_the_users_login() (+21 more)

### Community 46 - "Community 46"
Cohesion: 0.14
Nodes (28): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+20 more)

### Community 47 - "Community 47"
Cohesion: 0.09
Nodes (17): ChangedFile, parse_numstat(), staged_changes(), branch_sha(), default_branch_sha(), DirtyRepoError, ensure_no_operation_in_progress(), has_local_branch() (+9 more)

### Community 48 - "Community 48"
Cohesion: 0.10
Nodes (16): check_template(), CheckResult, load_contract(), _message(), parse_contract(), _Strict, TemplateCommands, TemplateContract (+8 more)

### Community 49 - "Community 49"
Cohesion: 0.14
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 50 - "Community 50"
Cohesion: 0.09
Nodes (29): keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total() (+21 more)

### Community 51 - "Community 51"
Cohesion: 0.16
Nodes (26): FakeRunner, ReviewInputs, test_each_review_is_its_own_run(), OutcomeRunner, run(), test_approve(), test_budget_defaults_and_overrides(), run() (+18 more)

### Community 52 - "Community 52"
Cohesion: 0.08
Nodes (16): Agents, BackendSettings, Budget, _check_base_url(), _check_path_pattern(), Commands, ContextSettings, GatesSettings (+8 more)

### Community 53 - "Community 53"
Cohesion: 0.08
Nodes (20): _assistant(), clock(), _init(), make(), project(), registry(), repo(), _result() (+12 more)

### Community 54 - "Community 54"
Cohesion: 0.07
Nodes (15): cap_excerpt(), PreviousAttempt, _clean(), code(), escape_closing_tag(), fenced(), normalize_newlines(), _previous_vars() (+7 more)

### Community 55 - "Community 55"
Cohesion: 0.09
Nodes (15): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+7 more)

### Community 56 - "Community 56"
Cohesion: 0.10
Nodes (20): capture(), on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact() (+12 more)

### Community 57 - "Community 57"
Cohesion: 0.11
Nodes (13): logged_in(), FakeGates, Merging, codex_review(), set_roles(), test_a_ticket_runs_end_to_end_on_codex(), test_a_ticket_runs_end_to_end_on_the_agent_sdk(), test_each_role_starts_its_own_backend() (+5 more)

### Community 58 - "Community 58"
Cohesion: 0.15
Nodes (27): add(), auth(), edit(), etag(), fixture_tickets(), test_a_new_ticket_gets_the_next_number_and_its_file(), test_a_new_ticket_is_ready_or_draft_with_a_waiting_plan(), test_a_refused_new_ticket_is_422_with_the_field_and_writes_nothing() (+19 more)

### Community 59 - "Community 59"
Cohesion: 0.07
Nodes (5): billing_error(), CliTransport, SdkRun, stop(), test_billing_errors_are_recognised()

### Community 60 - "Community 60"
Cohesion: 0.13
Nodes (28): is_junk(), is_secret(), _matches(), merge_head(), merge_in(), branch(), git_out(), head() (+20 more)

### Community 61 - "Community 61"
Cohesion: 0.11
Nodes (19): build_argv(), install_dir(), permission_profile(), _toml(), with_codex_home(), expected(), profile_of(), standalone_install() (+11 more)

### Community 62 - "Community 62"
Cohesion: 0.10
Nodes (24): diff_report(), DiffFile, DiffReport, _file(), GateReport, gates_report(), GatesReport, _header_path() (+16 more)

### Community 63 - "Community 63"
Cohesion: 0.07
Nodes (8): billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), child_env(), test_child_env_is_an_allowlist(), test_real_codex_run_creates_a_file_and_cannot_read_ssh(), codex()

### Community 64 - "Community 64"
Cohesion: 0.22
Nodes (22): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+14 more)

### Community 65 - "Community 65"
Cohesion: 0.13
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _control(), discard_command() (+7 more)

### Community 66 - "Community 66"
Cohesion: 0.11
Nodes (19): advance(), checked_out(), commit(), conclude_merge(), conflict_files(), create_tag(), ensure_main_ready(), _git() (+11 more)

### Community 67 - "Community 67"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 68 - "Community 68"
Cohesion: 0.10
Nodes (15): dev_agents(), runner(), fill_verdict(), auth(), _check_reports(), dev_client(), make(), dev_project() (+7 more)

### Community 69 - "Community 69"
Cohesion: 0.12
Nodes (17): GitHubClient, GitHubError, create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull() (+9 more)

### Community 70 - "Community 70"
Cohesion: 0.20
Nodes (24): kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt(), test_changes_requested_three_times_blocks() (+16 more)

### Community 71 - "Community 71"
Cohesion: 0.11
Nodes (16): check_command(), check_path(), check_tool(), make_hook(), pre_tool_use(), relative_pattern(), call_hook(), test_reviewer_and_planner_get_no_write_or_bash() (+8 more)

### Community 72 - "Community 72"
Cohesion: 0.13
Nodes (25): editor_command(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores(), test_edit_interrupted_restores() (+17 more)

### Community 73 - "Community 73"
Cohesion: 0.12
Nodes (18): AgentRunner, adapter(), AdapterCase, agent_sdk(), claude_cli(), codex_cli(), fake(), run() (+10 more)

### Community 74 - "Community 74"
Cohesion: 0.09
Nodes (9): test_direct_push_and_a_pull_request_on_github(), jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once(), test_one_plan_per_project_at_a_time() (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.09
Nodes (15): create_app(), lifespan(), _openapi(), check_git(), recover_all_integrations(), recover_all_worktrees(), test_create_app_uses_token_file(), make_repo() (+7 more)

### Community 76 - "Community 76"
Cohesion: 0.10
Nodes (17): ProjectValidationError, check_slug(), Project, has_spec(), init_project(), _initial_yaml(), InitResult, list_workspaces() (+9 more)

### Community 77 - "Community 77"
Cohesion: 0.16
Nodes (18): close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(), stuck() (+10 more)

### Community 78 - "Community 78"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 79 - "Community 79"
Cohesion: 0.11
Nodes (21): build_argv(), child_env(), sandbox_settings(), parent_env(), settings_json(), test_a_custom_endpoint_gets_spoolhqs_token_and_no_login(), test_api_billing_keeps_only_the_api_key(), test_argv_is_exactly_the_documented_command_line() (+13 more)

### Community 80 - "Community 80"
Cohesion: 0.08
Nodes (6): keep_end(), Outcome, Session, _signal_group(), _stream(), StreamParser

### Community 81 - "Community 81"
Cohesion: 0.11
Nodes (19): useDismissJob(), useInterruptedRun(), MAX_CARDS, NeedsYouCard, needsYouCards(), NeedsYouKind, sentence(), TicketLike (+11 more)

### Community 82 - "Community 82"
Cohesion: 0.17
Nodes (18): create(), git_state(), jobs_for(), snapshot(), source_fields(), states(), test_a_commit_without_an_identity_fails_and_rolls_back(), test_a_failing_test_command_names_its_field() (+10 more)

### Community 83 - "Community 83"
Cohesion: 0.21
Nodes (19): cache_dir(), refresh(), FakeGraphify, builds(), pointer(), source(), test_a_busy_cache_gives_no_map(), test_a_cache_from_another_version_is_discarded() (+11 more)

### Community 84 - "Community 84"
Cohesion: 0.11
Nodes (10): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), problem_view(), _validation_error() (+2 more)

### Community 85 - "Community 85"
Cohesion: 0.13
Nodes (18): denials_except(), home_denials(), policy(), user_home(), worktree(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home() (+10 more)

### Community 86 - "Community 86"
Cohesion: 0.19
Nodes (17): auth(), _ended(), finished(), post(), refused(), test_a_failing_test_command_and_its_rollback(), test_a_project_being_created_is_reported_as_creating(), test_a_read_only_path_the_rollback_cant_delete_is_listed() (+9 more)

### Community 87 - "Community 87"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 88 - "Community 88"
Cohesion: 0.11
Nodes (10): _authenticate(), _convert(), _Envelopes, events(), EventStreams, _send(), _stream(), listener() (+2 more)

### Community 89 - "Community 89"
Cohesion: 0.12
Nodes (17): _clean_line(), commit_message(), _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section() (+9 more)

### Community 90 - "Community 90"
Cohesion: 0.13
Nodes (11): _check(), check_secret(), SecretCheck, answer(), handler(), fail(), test_a_redirect_is_not_followed(), test_each_provider_gets_one_read_only_call() (+3 more)

### Community 91 - "Community 91"
Cohesion: 0.12
Nodes (23): AgentDeniedData, AgentFileEditData, AgentMessageData, AgentRateLimitData, AgentToolCallData, AgentToolResultData, AgentUsageData, AgentWarningData (+15 more)

### Community 92 - "Community 92"
Cohesion: 0.11
Nodes (12): _area_entries(), expand_index(), _inside(), _read(), ContextBudgetError, ContextError, PromptTemplateError, DependencyView (+4 more)

### Community 93 - "Community 93"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 94 - "Community 94"
Cohesion: 0.12
Nodes (8): delete_secret(), _lookup(), read_secret(), secret_status(), SecretStatus, store_secret(), test_empty_values_and_an_unreadable_keychain(), test_environment_wins_over_the_keychain()

### Community 95 - "Community 95"
Cohesion: 0.11
Nodes (7): version(), Version, _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 96 - "Community 96"
Cohesion: 0.11
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 97 - "Community 97"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 98 - "Community 98"
Cohesion: 0.17
Nodes (19): gates(), test_all_passing(), test_an_unset_command_is_skipped_and_the_run_still_passes(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+11 more)

### Community 99 - "Community 99"
Cohesion: 0.17
Nodes (15): AgentPolicy, test_policy_fields_are_untouched_by_credentials_list(), test_unusable_backend_raises_before_starting(), test_a_cancel_during_the_delay_stops_the_run(), test_a_sequence_replays_one_transcript_per_run(), test_a_write_outside_the_worktree_is_refused_as_a_policy_error(), test_cancel(), test_cycle_starts_the_sequence_again() (+7 more)

### Community 100 - "Community 100"
Cohesion: 0.15
Nodes (14): _check_decisions(), _decisions(), folders(), _script(), test_a_consistent_fixture_passes(), test_a_duplicated_number_fails(), test_a_mismatched_title_fails(), test_a_missing_number_fails() (+6 more)

### Community 101 - "Community 101"
Cohesion: 0.14
Nodes (12): get_tickets(), AttemptView, InvalidTicketView, Note, TicketActivityView, TicketAttemptView, TicketDetail, TicketGitView (+4 more)

### Community 102 - "Community 102"
Cohesion: 0.21
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 103 - "Community 103"
Cohesion: 0.26
Nodes (18): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_a_run_finishing_between_pages_is_not_repeated(), test_attempt_artifacts(), test_attempt_reports(), test_current_with_no_run() (+10 more)

### Community 104 - "Community 104"
Cohesion: 0.09
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 105 - "Community 105"
Cohesion: 0.15
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 106 - "Community 106"
Cohesion: 0.13
Nodes (17): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_clean_strips_ansi_and_crlf() (+9 more)

### Community 107 - "Community 107"
Cohesion: 0.12
Nodes (9): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements(), _user_version(), WorkspaceRuns (+1 more)

### Community 108 - "Community 108"
Cohesion: 0.20
Nodes (12): createItem(), getItem(), listItems(), Item, NewItem, ItemList(), CreateItemForm(), submit() (+4 more)

### Community 109 - "Community 109"
Cohesion: 0.25
Nodes (15): check(), refused(), request(), test_a_duplicate_name_is_refused(), test_a_good_name_passes(), test_a_new_repo_needs_a_new_or_empty_folder(), test_a_symlinked_target_is_refused(), test_a_template_only_for_a_template_source() (+7 more)

### Community 110 - "Community 110"
Cohesion: 0.13
Nodes (11): describe_graphify(), _build(), find_command(), Graphify, GraphifyError, _kill_tree(), probe(), run() (+3 more)

### Community 111 - "Community 111"
Cohesion: 0.12
Nodes (9): github_token(), store_github_token(), MemoryKeyring, stored_key(), test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins() (+1 more)

### Community 112 - "Community 112"
Cohesion: 0.23
Nodes (16): _Job, auth(), get_plan(), plan_client(), test_a_clean_approve_makes_the_drafts_ready(), test_an_invalid_ticket_file_is_a_problem(), test_approve_with_problems_is_409_and_changes_nothing(), test_each_problem_has_its_code_and_ticket_ids() (+8 more)

### Community 113 - "Community 113"
Cohesion: 0.25
Nodes (15): auth(), error(), etag(), test_an_invalid_project_yaml_is_listed_with_its_first_problem(), test_list_and_get_projects(), test_project_detail_says_why_nothing_can_run(), test_settings_edit_with_etags(), test_spec_edit_with_etags() (+7 more)

### Community 114 - "Community 114"
Cohesion: 0.14
Nodes (3): AgentSdkRunner, test_real_agent_sdk_run_creates_a_file_and_is_denied_ssh(), sdk()

### Community 115 - "Community 115"
Cohesion: 0.11
Nodes (7): dotted_path(), format_errors(), _message(), _model_at(), _number(), split_error(), test_split_error()

### Community 116 - "Community 116"
Cohesion: 0.23
Nodes (17): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+9 more)

### Community 117 - "Community 117"
Cohesion: 0.21
Nodes (9): _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state(), test_dirty_checkout_after_a_cut_off_fast_forward_is_left_alone() (+1 more)

### Community 118 - "Community 118"
Cohesion: 0.18
Nodes (3): summarize(), CodexStreamParser, _int()

### Community 119 - "Community 119"
Cohesion: 0.20
Nodes (12): read_repo_docs(), read_text(), decisions_block(), entry(), outside_paths(), test_entries_follow_number_order_not_index_order(), test_missing_area_file_and_entry_keep_the_title_with_one_warning(), test_missing_notes_are_none() (+4 more)

### Community 120 - "Community 120"
Cohesion: 0.14
Nodes (8): PlanInvalid, approve_plan(), _invalid_problem(), plan_problems(), _recorded(), _replace_all(), sha256(), write_plan()

### Community 121 - "Community 121"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 122 - "Community 122"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 123 - "Community 123"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 124 - "Community 124"
Cohesion: 0.18
Nodes (9): CodeMap, _current(), _drop(), _refresh(), _remove_unused(), _save(), summary(), test_a_report_without_known_sections_is_empty() (+1 more)

### Community 125 - "Community 125"
Cohesion: 0.19
Nodes (15): is_git_url(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder(), test_a_local_git_repository_at_a_ref() (+7 more)

### Community 126 - "Community 126"
Cohesion: 0.15
Nodes (9): check_secret_route(), delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretTest, SecretValue (+1 more)

### Community 127 - "Community 127"
Cohesion: 0.10
Nodes (5): describe(), print_run(), run_command(), check_command(), describe_source()

### Community 128 - "Community 128"
Cohesion: 0.20
Nodes (9): id_key(), InvalidPlan, PlanOutput, draft_file_name(), Existing, check_plan(), CheckedPlan, _id_errors() (+1 more)

### Community 129 - "Community 129"
Cohesion: 0.10
Nodes (14): CREATED_TOAST, GET, Handler, Job, JOB_ID, NAMES, openDialog(), Panel() (+6 more)

### Community 130 - "Community 130"
Cohesion: 0.18
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 131 - "Community 131"
Cohesion: 0.21
Nodes (14): test_a_git_template_check_runs_no_global_git_hooks(), test_init_an_empty_repo_on_a_branch(), test_init_an_existing_repo_then_validate(), test_init_existing_folder(), test_init_from_a_git_template_at_a_ref(), test_init_from_a_local_folder_template(), test_init_from_a_template_fills_its_commands(), test_init_refuses_a_bad_branch_name() (+6 more)

### Community 132 - "Community 132"
Cohesion: 0.12
Nodes (8): ContextInputs, _slots(), code_map(), implementer_prompt(), planner_code_map(), previous_attempt(), _read(), test_negative_cap_is_refused()

### Community 133 - "Community 133"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 134 - "Community 134"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 135 - "Community 135"
Cohesion: 0.16
Nodes (10): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+2 more)

### Community 136 - "Community 136"
Cohesion: 0.17
Nodes (9): CurrentRun, Discarded, MergedView, PhaseLine, PolicyView, Reject, RuleHitView, RunList (+1 more)

### Community 137 - "Community 137"
Cohesion: 0.16
Nodes (10): builtin_contracts(), builtin_names(), builtin_root(), _clone(), _git(), _is_path(), _label(), test_list_templates() (+2 more)

### Community 138 - "Community 138"
Cohesion: 0.13
Nodes (8): test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_logs_the_fake_runner_and_passes_its_agents(), test_serve_refuses_non_loopback_host(), test_serve_refuses_the_fake_runner_frozen_or_unknown(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 139 - "Community 139"
Cohesion: 0.25
Nodes (9): generate(), test_a_copier_failure_is_reported(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_template_without_a_test_command_is_rejected(), test_an_empty_existing_folder_is_used(), test_tasks_from_an_include_are_refused_by_copier_and_never_run(), test_the_users_copier_trust_list_is_ignored() (+1 more)

### Community 140 - "Community 140"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 141 - "Community 141"
Cohesion: 0.25
Nodes (9): approve_plan(), generate_plan(), get_plan(), _plans(), GeneratePlan, PlanApproved, PlanProblemView, PlanStarted (+1 more)

### Community 142 - "Community 142"
Cohesion: 0.24
Nodes (4): is_ancestor(), ahead_message(), _failed(), _held()

### Community 143 - "Community 143"
Cohesion: 0.20
Nodes (7): PlannerError, PlanResult, generate_plan(), finish(), _ignore(), read_spec(), load_existing()

### Community 144 - "Community 144"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 145 - "Community 145"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 146 - "Community 146"
Cohesion: 0.11
Nodes (18): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+10 more)

### Community 147 - "Community 147"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 148 - "Community 148"
Cohesion: 0.19
Nodes (4): clean_title(), _not_blank(), one_line(), PlannedTicket

### Community 149 - "Community 149"
Cohesion: 0.20
Nodes (8): edit_lock(), EditConflict, etag_of(), read_with_etag(), write_if_match(), test_concurrent_edits_with_the_same_etag_let_one_win(), edit(), test_write_only_when_the_etag_matches()

### Community 150 - "Community 150"
Cohesion: 0.18
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 151 - "Community 151"
Cohesion: 0.21
Nodes (12): _api_routes(), test_bodies_over_1_mb_are_refused(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token() (+4 more)

### Community 152 - "Community 152"
Cohesion: 0.24
Nodes (7): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from(), test_testing_a_secret_needs_the_token_and_a_known_name(), test_testing_a_secret_never_returns_or_logs_it()

### Community 153 - "Community 153"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 154 - "Community 154"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 155 - "Community 155"
Cohesion: 0.24
Nodes (9): recover_worktrees(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+1 more)

### Community 156 - "Community 156"
Cohesion: 0.22
Nodes (6): generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 157 - "Community 157"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 158 - "Community 158"
Cohesion: 0.28
Nodes (6): ApiError, cancel_job(), dismiss_job(), get_job(), _jobs(), JobView

### Community 159 - "Community 159"
Cohesion: 0.17
Nodes (9): _kept(), esc(), render_planner_prompt(), assert_snapshot(), test_a_project_can_override_the_prompt(), test_template_syntax_and_closing_tags_in_the_spec_are_plain_text(), test_the_prompt_for_the_dashboard_spec(), test_the_prompt_with_kept_tickets_and_a_template() (+1 more)

### Community 161 - "Community 161"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 162 - "Community 162"
Cohesion: 0.22
Nodes (5): create_app(), client(), test_session(), engine(), session()

### Community 163 - "Community 163"
Cohesion: 0.36
Nodes (9): add_tickets(), test_a_starter_spec_is_left_out_and_a_real_one_renders_as_before(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override() (+1 more)

### Community 164 - "Community 164"
Cohesion: 0.31
Nodes (5): Base, Item, create_item(), get_item(), list_items()

### Community 165 - "Community 165"
Cohesion: 0.27
Nodes (7): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd()

### Community 166 - "Community 166"
Cohesion: 0.24
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 167 - "Community 167"
Cohesion: 0.33
Nodes (9): make_plan(), test_a_failed_write_leaves_the_old_files(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members(), test_approving_twice_gives_nothing_to_approve() (+1 more)

### Community 168 - "Community 168"
Cohesion: 0.20
Nodes (7): available_runners(), backend_names(), make_runner(), _check_backend(), test_codex_takes_the_endpoint_and_model(), test_the_agent_sdk_takes_the_endpoint_and_model(), test_the_built_in_backends()

### Community 169 - "Community 169"
Cohesion: 0.24
Nodes (3): get_engine(), get_session(), make_engine()

### Community 170 - "Community 170"
Cohesion: 0.44
Nodes (7): auth(), _get(), _log(), test_1200_events_come_in_pages_of_500_500_and_200(), test_a_limit_over_2000_is_refused(), test_attempt_n_gives_its_window_with_the_run_level_events(), test_unknown_run_or_attempt_is_404()

### Community 172 - "Community 172"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 174 - "Community 174"
Cohesion: 0.24
Nodes (4): test_a_local_endpoint_gets_the_dummy(), test_a_remote_endpoint_uses_the_environment_then_the_keychain(), test_an_unreadable_keychain_means_no_token(), test_store()

### Community 175 - "Community 175"
Cohesion: 0.27
Nodes (5): allowed_env(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start(), test_windows_names_match_in_any_case()

### Community 176 - "Community 176"
Cohesion: 0.38
Nodes (4): agents(), AgentsView, BackendView, GraphifyView

### Community 179 - "Community 179"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 180 - "Community 180"
Cohesion: 0.31
Nodes (4): App(), root, HomePage(), react-dom

### Community 181 - "Community 181"
Cohesion: 0.27
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 182 - "Community 182"
Cohesion: 0.28
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 183 - "Community 183"
Cohesion: 0.31
Nodes (4): test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 184 - "Community 184"
Cohesion: 0.36
Nodes (3): list_templates(), TemplateCommandsView, TemplateView

### Community 185 - "Community 185"
Cohesion: 0.33
Nodes (3): _generated_at(), plan_overview(), PlanOverview

### Community 187 - "Community 187"
Cohesion: 0.36
Nodes (5): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_startup_recovers_and_skips_a_corrupt_database()

### Community 188 - "Community 188"
Cohesion: 0.39
Nodes (6): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_one_line_drops_control_and_format_characters(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 189 - "Community 189"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 190 - "Community 190"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 193 - "Community 193"
Cohesion: 0.25
Nodes (5): done_when_items(), render_draft(), render_ticket(), test_a_draft_round_trips_through_the_ticket_store(), test_a_title_that_needs_quotes_stays_valid_yaml()

### Community 194 - "Community 194"
Cohesion: 0.32
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 196 - "Community 196"
Cohesion: 0.43
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 198 - "Community 198"
Cohesion: 0.48
Nodes (3): manager(), wt_repo(), wt_root()

### Community 199 - "Community 199"
Cohesion: 0.29
Nodes (4): _fail_after_yaml(), test_failed_rename_leaves_nothing(), test_failure_mid_init_leaves_nothing(), test_missing_git_is_reported()

### Community 204 - "Community 204"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 207 - "Community 207"
Cohesion: 0.53
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 208 - "Community 208"
Cohesion: 0.40
Nodes (4): Markdown(), PLUGINS, react-markdown, remark-gfm

### Community 209 - "Community 209"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 213 - "Community 213"
Cohesion: 0.67
Nodes (3): dependencies, react, react-dom

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `Config`, `InvalidRequest`, `NotRunning` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2414 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **155 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 8` to `Community 0`, `Community 5`, `Community 7`, `Community 12`, `Community 143`, `Community 17`, `Community 19`, `Community 23`, `Community 24`, `Community 29`, `Community 35`, `Community 39`, `Community 40`, `Community 170`, `Community 43`, `Community 49`, `Community 53`, `Community 56`, `Community 58`, `Community 187`, `Community 75`, `Community 77`, `Community 88`, `Community 103`, `Community 107`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `RunLog` (e.g. with `recover_interrupted()` and `RunRegistry`) actually correct?**
  _`RunLog` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `Config` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.027163198247535596 - nodes in this community are weakly interconnected._
- **Why does `load_project()` connect `Community 38` to `Community 0`, `Community 130`, `Community 131`, `Community 140`, `Community 143`, `Community 19`, `Community 21`, `Community 24`, `Community 28`, `Community 156`, `Community 33`, `Community 163`, `Community 39`, `Community 41`, `Community 43`, `Community 46`, `Community 49`, `Community 52`, `Community 57`, `Community 64`, `Community 67`, `Community 68`, `Community 70`, `Community 74`, `Community 75`, `Community 76`, `Community 82`, `Community 101`, `Community 113`, `Community 117`, `Community 127`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 70 inferred relationships involving `load_project()` (e.g. with `_load()` and `_settings_data()`) actually correct?**
  _`load_project()` has 70 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.030960204454180358 - nodes in this community are weakly interconnected._