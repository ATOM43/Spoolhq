# Graph Report - Project_Manager  (2026-11-06)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 6628 nodes · 18795 edges · 362 communities (191 shown, 171 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1578 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1a57d601`
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
- Community 212
- Community 213
- Community 214
- Community 215
- Community 216
- Community 217
- Community 350
- Community 351
- Community 352

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 114 edges
2. `load_project()` - 89 edges
3. `WorktreeManager` - 82 edges
4. `RunRegistry` - 69 edges
5. `AgentPolicy` - 69 edges
6. `FakeRunner` - 68 edges
7. `ClaudeStreamParser` - 61 edges
8. `build_implementer_prompt()` - 60 edges
9. `RunContext` - 51 edges
10. `run_git()` - 50 edges

## Surprising Connections (you probably didn't know these)
- `schema()` --uses--> `Settings`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/core/config.py
- `schema()` --calls--> `create_app()`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/api/app.py
- `test_codex_not_logged_in_says_codex_login()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `test_detect()` --calls--> `FakeRunner`  [INFERRED]
  daemon/tests/services/agents/test_fake.py → daemon/src/spoolhq/services/agents/fake.py

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

## Communities (362 total, 171 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (31): ChangedFile, approve(), decide(), read_artifact(), reject(), unblock(), _waiting(), IntegrationStatus (+23 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (50): advance(), checked_out(), commit(), conclude_merge(), conflict_files(), create_tag(), ensure_main_ready(), _git() (+42 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (29): AgentSdkRunner, policy_parts(), billing_for(), format_version(), parse_version(), platform_reason(), probe(), check_worktree() (+21 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (29): weighted_tokens(), available_runners(), backend_names(), make_runner(), keep_end(), PolicyViolation, summarize(), CodexStreamParser (+21 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (28): agents_command(), describe(), describe_roles(), describe_worktrees(), fail(), hours(), settings(), table() (+20 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (32): temp_folders(), temp_worktree_refusal(), find_command(), _kill_tree(), probe(), run(), ProcessResult, run_process() (+24 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (48): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), _usage_counts(), usd_to_micro(), assistant(), load() (+40 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (38): approval_message(), _result(), HoldForIntegration, IntegrationResult, agent_stopped(), attempt_once(), check_resolved(), commit() (+30 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (37): slugify(), clean_title(), InvalidPlan, _not_blank(), one_line(), PlannedTicket, PlannerError, PlanOutput (+29 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (26): utc_now(), decode_cursor(), encode_cursor(), page_runs(), RunPage, AttemptKind, AttemptStatus, Event (+18 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (46): api_key(), no_parent_key(), test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript(), record(), run() (+38 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (22): logged_in(), clock(), FakeGates, make_loop(), make(), Merging, project(), registry() (+14 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (51): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+43 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (23): dotted_path(), format_errors(), edit_ticket(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError (+15 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (46): ClaudeCliRunner, AgentPolicy, assert_gone(), endpoint_runner(), fake_probe(), read_record(), Recorder, run() (+38 more)

### Community 15 - "Community 15"
Cohesion: 0.04
Nodes (40): Backend, backends, GET, Handler, NOT_SET, POST, PUT, renderDialog() (+32 more)

### Community 16 - "Community 16"
Cohesion: 0.05
Nodes (15): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, BranchConflictError, marker_key(), _norm(), parse_worktree_list() (+7 more)

### Community 17 - "Community 17"
Cohesion: 0.08
Nodes (50): cancelJob(), cleanupToast(), CreateRequest, fieldError(), Job, JobStep, POLL_MS, startJob() (+42 more)

### Community 18 - "Community 18"
Cohesion: 0.06
Nodes (48): state_db_path(), FailingCommit, raw(), run_log(), test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise() (+40 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (55): load_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated(), test_bad_file_name() (+47 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (28): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+20 more)

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (30): builtin_fixture(), client(), clock(), fake_backend(), fake_claude_cmd(), fake_codex_cmd(), fake_graphify(), fake_sdk_cmd() (+22 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (28): id_key(), PlanError, SchedulerError, TransitionError, _and_list(), _find_cycles(), require_valid(), sort_ids() (+20 more)

### Community 23 - "Community 23"
Cohesion: 0.07
Nodes (42): Listener, listeners, openSettings(), SettingsTab, useOpenRequests(), Agents, backendReady(), DaemonSettings (+34 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (31): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+23 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (46): PlanProblem, validate_plan(), apply_transition(), check_transition(), parse_status(), copy_dashboard(), dashboard(), make() (+38 more)

### Community 26 - "Community 26"
Cohesion: 0.08
Nodes (38): Agents, useAgents(), COALESCE_MS, EventSource, lastSeq, Probe(), subscribe, useProjectEvents() (+30 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (23): keep_for(), EventBus, RunLog, test_interrupted_run_keeps_its_worktree(), test_tickets_show_the_pull_request(), FixedClock, bus(), drain() (+15 more)

### Community 28 - "Community 28"
Cohesion: 0.10
Nodes (43): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_ticket(), test_negative_cap_is_refused(), test_no_map_no_block(), test_the_map_counts_against_the_budget() (+35 more)

### Community 29 - "Community 29"
Cohesion: 0.06
Nodes (7): check_ticket_id(), _user_approved(), attempt_dir_name(), _check_count(), _make_attempt_dir(), Attempt, Run

### Community 30 - "Community 30"
Cohesion: 0.09
Nodes (35): cn(), formatTime(), formatTokens(), formatUsage(), timeAgo(), Button(), buttonVariants, Card() (+27 more)

### Community 31 - "Community 31"
Cohesion: 0.09
Nodes (28): require_if_match(), run_log(), settings(), workspace(), create_project(), _creating(), get_project(), get_settings() (+20 more)

### Community 32 - "Community 32"
Cohesion: 0.16
Nodes (34): LocalIntegrator, _assistant(), _init(), _result(), Transcripts, git(), hooked(), call() (+26 more)

### Community 33 - "Community 33"
Cohesion: 0.11
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (44): load_project(), del_path(), errors_for(), set_path(), test_a_template_must_be_a_block(), test_a_workspace_can_be_written_before_its_repo(), test_all_errors_are_reported_at_once(), test_bad_protected_path_patterns_are_refused() (+36 more)

### Community 35 - "Community 35"
Cohesion: 0.08
Nodes (36): branch_name(), ensure_clean(), status_entries(), GitResult, fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it() (+28 more)

### Community 36 - "Community 36"
Cohesion: 0.13
Nodes (41): WorktreeManager, run_git(), branches(), make_read_only(), marker(), real(), registered_paths(), sha() (+33 more)

### Community 37 - "Community 37"
Cohesion: 0.07
Nodes (23): HomePage(), renderHome(), PATHS, RunAction, useRunAction(), formatUsage(), guidance(), idleReason() (+15 more)

### Community 38 - "Community 38"
Cohesion: 0.08
Nodes (27): cap_excerpt(), keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec() (+19 more)

### Community 39 - "Community 39"
Cohesion: 0.07
Nodes (40): engines, node, name, packageManager, private, type, version, description (+32 more)

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (28): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+20 more)

### Community 41 - "Community 41"
Cohesion: 0.11
Nodes (19): describe_source(), check_template(), CheckResult, load_contract(), TemplateContract, TemplateError, check_safe(), init_repo() (+11 more)

### Community 42 - "Community 42"
Cohesion: 0.15
Nodes (29): assert_refused(), read_only(), read_record(), refused_message(), run(), runner(), temps(), test_a_custom_endpoint_never_gets_the_users_login() (+21 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (14): load_or_create_token(), read_token(), token_path(), config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), ensure_home() (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.08
Nodes (17): Agents, BackendSettings, Budget, _check_base_url(), _check_path_pattern(), check_slug(), Commands, ContextSettings (+9 more)

### Community 45 - "Community 45"
Cohesion: 0.10
Nodes (28): _clean_line(), commit_message(), unresolved_files(), branch(), git_out(), head(), _squash(), _stage_link() (+20 more)

### Community 46 - "Community 46"
Cohesion: 0.09
Nodes (16): GateLine, ItemVerdict, ReviewResult, _gate_word(), _ignore(), _items(), render_review_prompt(), review() (+8 more)

### Community 47 - "Community 47"
Cohesion: 0.16
Nodes (19): service_errors(), approve_ticket(), Artifact, cancel_run(), current_run(), discard_ticket(), get_artifact(), get_run() (+11 more)

### Community 48 - "Community 48"
Cohesion: 0.09
Nodes (18): Agents, auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template() (+10 more)

### Community 49 - "Community 49"
Cohesion: 0.10
Nodes (17): dumper(), loader(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node() (+9 more)

### Community 50 - "Community 50"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _control(), discard_command() (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.10
Nodes (16): check_command(), check_path(), check_tool(), make_hook(), pre_tool_use(), relative_pattern(), call_hook(), test_reviewer_and_planner_get_no_write_or_bash() (+8 more)

### Community 53 - "Community 53"
Cohesion: 0.12
Nodes (17): GitHubClient, GitHubError, create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull() (+9 more)

### Community 54 - "Community 54"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 55 - "Community 55"
Cohesion: 0.11
Nodes (19): build_argv(), install_dir(), permission_profile(), policy_parts(), _toml(), with_codex_home(), expected(), profile_of() (+11 more)

### Community 56 - "Community 56"
Cohesion: 0.10
Nodes (22): build_argv(), child_env(), sandbox_settings(), parent_env(), settings_json(), test_a_custom_endpoint_gets_spoolhqs_token_and_no_login(), test_api_billing_keeps_only_the_api_key(), test_argv_is_exactly_the_documented_command_line() (+14 more)

### Community 57 - "Community 57"
Cohesion: 0.19
Nodes (24): kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt(), test_changes_requested_three_times_blocks() (+16 more)

### Community 58 - "Community 58"
Cohesion: 0.11
Nodes (17): _area_entries(), expand_index(), _inside(), _read(), read_repo_docs(), ContextInputs, DependencyView, GateFailure (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.09
Nodes (20): NewProjectButton(), useDismissJob(), useInterruptedRun(), MAX_CARDS, NeedsYouCard, needsYouCards(), NeedsYouKind, sentence() (+12 more)

### Community 60 - "Community 60"
Cohesion: 0.15
Nodes (18): Delivery, ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note() (+10 more)

### Community 61 - "Community 61"
Cohesion: 0.08
Nodes (12): serve(), _serve(), _Server, configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file() (+4 more)

### Community 62 - "Community 62"
Cohesion: 0.10
Nodes (8): _Cancelled, _Failed, Job, roll_back(), Rollback, Runner, Step, Checked

### Community 63 - "Community 63"
Cohesion: 0.12
Nodes (19): capture(), on_raw(), _transcript(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files() (+11 more)

### Community 64 - "Community 64"
Cohesion: 0.08
Nodes (6): billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), test_real_codex_run_creates_a_file_and_cannot_read_ssh(), codex()

### Community 65 - "Community 65"
Cohesion: 0.13
Nodes (17): adapter(), AdapterCase, agent_sdk(), claude_cli(), codex_cli(), fake(), run(), record() (+9 more)

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (21): cache_dir(), refresh(), FakeGraphify, builds(), pointer(), source(), test_a_busy_cache_gives_no_map(), test_a_cache_from_another_version_is_discarded() (+13 more)

### Community 67 - "Community 67"
Cohesion: 0.08
Nodes (4): billing_error(), CliTransport, SdkRun, test_billing_errors_are_recognised()

### Community 68 - "Community 68"
Cohesion: 0.15
Nodes (21): ConfigError, load_settings(), test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1(), test_config_file_is_read(), test_defaults_without_config_file() (+13 more)

### Community 69 - "Community 69"
Cohesion: 0.22
Nodes (24): FakeRunner, ReviewInputs, run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages(), test_cancelled_is_passed_through() (+16 more)

### Community 70 - "Community 70"
Cohesion: 0.16
Nodes (18): close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(), stuck() (+10 more)

### Community 71 - "Community 71"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 72 - "Community 72"
Cohesion: 0.12
Nodes (13): describe_graphify(), _build(), CodeMap, _current(), _drop(), _refresh(), _remove_unused(), _save() (+5 more)

### Community 73 - "Community 73"
Cohesion: 0.07
Nodes (5): stop(), Session, _signal_group(), _stream(), StreamParser

### Community 74 - "Community 74"
Cohesion: 0.14
Nodes (12): DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, clean(), check_done_when(), _not_run() (+4 more)

### Community 75 - "Community 75"
Cohesion: 0.12
Nodes (18): ProjectError, ProjectValidationError, has_spec(), init_project(), _initial_yaml(), InitResult, parse_project(), _populate() (+10 more)

### Community 76 - "Community 76"
Cohesion: 0.09
Nodes (9): create_app(), lifespan(), health(), Health, check_git(), recover_all_integrations(), recover_all_worktrees(), RecoveryReport (+1 more)

### Community 77 - "Community 77"
Cohesion: 0.11
Nodes (9): acquire_lock(), DaemonLock, holder(), LockHeld, _read_pid(), _try_lock(), _unlock(), active_message() (+1 more)

### Community 78 - "Community 78"
Cohesion: 0.18
Nodes (18): create(), git_state(), jobs_for(), snapshot(), source_fields(), states(), test_a_commit_without_an_identity_fails_and_rolls_back(), test_a_failing_test_command_names_its_field() (+10 more)

### Community 79 - "Community 79"
Cohesion: 0.19
Nodes (17): auth(), _ended(), finished(), post(), refused(), test_a_failing_test_command_and_its_rollback(), test_a_project_being_created_is_reported_as_creating(), test_a_read_only_path_the_rollback_cant_delete_is_listed() (+9 more)

### Community 80 - "Community 80"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 81 - "Community 81"
Cohesion: 0.09
Nodes (10): dump(), merge(), parse(), read(), to_plain(), _message(), parse_contract(), _Strict (+2 more)

### Community 82 - "Community 82"
Cohesion: 0.10
Nodes (17): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, BODIES (+9 more)

### Community 83 - "Community 83"
Cohesion: 0.07
Nodes (8): _client(), set_command(), sync_command(), init(), describe(), make_runner(), review_command(), store_api_key()

### Community 84 - "Community 84"
Cohesion: 0.12
Nodes (10): _authenticate(), _convert(), _Envelopes, events(), EventStreams, _send(), _stream(), listener() (+2 more)

### Community 85 - "Community 85"
Cohesion: 0.15
Nodes (10): get_ticket(), get_tickets(), put_ticket(), _read(), unblock_ticket(), InvalidTicketView, Note, TicketList (+2 more)

### Community 86 - "Community 86"
Cohesion: 0.13
Nodes (17): denials_except(), home_denials(), test_real_agent_sdk_run_creates_a_file_and_is_denied_ssh(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket() (+9 more)

### Community 87 - "Community 87"
Cohesion: 0.12
Nodes (16): AUTOSAVE_MS, SaveState, planBlocker(), PlanState, useGeneratePlan(), wordCount(), PlanButton(), PlanFailure() (+8 more)

### Community 88 - "Community 88"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 89 - "Community 89"
Cohesion: 0.13
Nodes (8): get_settings(), Settings, get_engine(), make_engine(), run(), url(), test_settings_read_the_environment(), test_migrations_create_and_drop_the_schema()

### Community 90 - "Community 90"
Cohesion: 0.09
Nodes (8): ContextBudgetError, ContextError, PromptTemplateError, fenced(), _PromptLoader, PromptTemplate, render_template(), _template_line()

### Community 91 - "Community 91"
Cohesion: 0.14
Nodes (11): _check(), check_secret(), SecretCheck, answer(), handler(), fail(), test_a_redirect_is_not_followed(), test_each_provider_gets_one_read_only_call() (+3 more)

### Community 92 - "Community 92"
Cohesion: 0.10
Nodes (14): check_git_version(), disabled_hooks_dir(), git_env(), git_executable(), GitError, hook_and_signing_options(), neutral_cwd(), parse_git_version() (+6 more)

### Community 94 - "Community 94"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 95 - "Community 95"
Cohesion: 0.11
Nodes (9): github_token(), store_github_token(), MemoryKeyring, stored_key(), test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins() (+1 more)

### Community 96 - "Community 96"
Cohesion: 0.17
Nodes (19): gates(), test_all_passing(), test_an_unset_command_is_skipped_and_the_run_still_passes(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+11 more)

### Community 97 - "Community 97"
Cohesion: 0.14
Nodes (17): is_git_url(), _is_path(), open_template(), generated(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up() (+9 more)

### Community 98 - "Community 98"
Cohesion: 0.12
Nodes (11): ApiError, _conflict(), check_secret_route(), delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings (+3 more)

### Community 99 - "Community 99"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 100 - "Community 100"
Cohesion: 0.09
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 101 - "Community 101"
Cohesion: 0.13
Nodes (17): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_clean_strips_ansi_and_crlf() (+9 more)

### Community 102 - "Community 102"
Cohesion: 0.20
Nodes (12): createItem(), getItem(), listItems(), Item, NewItem, ItemList(), CreateItemForm(), submit() (+4 more)

### Community 103 - "Community 103"
Cohesion: 0.25
Nodes (15): check(), refused(), request(), test_a_duplicate_name_is_refused(), test_a_good_name_passes(), test_a_new_repo_needs_a_new_or_empty_folder(), test_a_symlinked_target_is_refused(), test_a_template_only_for_a_template_source() (+7 more)

### Community 104 - "Community 104"
Cohesion: 0.17
Nodes (13): _check_branch(), _check_existing(), _check_new(), check_request(), _commands(), CreateProject, CreationError, _current_branch() (+5 more)

### Community 105 - "Community 105"
Cohesion: 0.13
Nodes (10): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_dir(), _statements(), _user_version() (+2 more)

### Community 106 - "Community 106"
Cohesion: 0.26
Nodes (15): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_attempt_artifacts(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_history_pages_are_stable_under_inserts() (+7 more)

### Community 107 - "Community 107"
Cohesion: 0.25
Nodes (15): auth(), error(), etag(), test_an_invalid_project_yaml_is_listed_with_its_first_problem(), test_list_and_get_projects(), test_project_detail_says_why_nothing_can_run(), test_settings_edit_with_etags(), test_spec_edit_with_etags() (+7 more)

### Community 108 - "Community 108"
Cohesion: 0.25
Nodes (20): block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason(), test_gate_checked_items_replace_the_reviewers_answer() (+12 more)

### Community 109 - "Community 109"
Cohesion: 0.17
Nodes (11): _check_decisions(), _decisions(), folders(), test_a_consistent_fixture_passes(), test_a_duplicated_number_fails(), test_a_mismatched_title_fails(), test_a_missing_number_fails(), test_an_entry_missing_from_the_area_files_fails() (+3 more)

### Community 110 - "Community 110"
Cohesion: 0.13
Nodes (6): ApiClient, ApiError, DaemonNotRunning, _detail(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401()

### Community 111 - "Community 111"
Cohesion: 0.18
Nodes (12): acquire_daemon_lock(), DaemonAlreadyRunning, lock_path(), make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_second_acquire_names_the_holder() (+4 more)

### Community 112 - "Community 112"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 113 - "Community 113"
Cohesion: 0.18
Nodes (12): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_a_huge_body_is_capped(), test_md_escape() (+4 more)

### Community 114 - "Community 114"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 115 - "Community 115"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 116 - "Community 116"
Cohesion: 0.17
Nodes (8): delete_secret(), _lookup(), read_secret(), secret_status(), SecretStatus, store_secret(), test_empty_values_and_an_unreadable_keychain(), test_environment_wins_over_the_keychain()

### Community 118 - "Community 118"
Cohesion: 0.21
Nodes (14): test_a_git_template_check_runs_no_global_git_hooks(), test_init_an_empty_repo_on_a_branch(), test_init_an_existing_repo_then_validate(), test_init_existing_folder(), test_init_from_a_git_template_at_a_ref(), test_init_from_a_local_folder_template(), test_init_from_a_template_fills_its_commands(), test_init_refuses_a_bad_branch_name() (+6 more)

### Community 119 - "Community 119"
Cohesion: 0.15
Nodes (5): _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 120 - "Community 120"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 121 - "Community 121"
Cohesion: 0.13
Nodes (10): check_gate_command(), gate_env(), resolve_program(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument() (+2 more)

### Community 122 - "Community 122"
Cohesion: 0.16
Nodes (11): _clear_read_only_and_retry(), remove_path(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck() (+3 more)

### Community 123 - "Community 123"
Cohesion: 0.12
Nodes (6): test_health(), Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token(), test_list_templates(), test_list_templates_needs_the_token()

### Community 124 - "Community 124"
Cohesion: 0.21
Nodes (11): read_text(), decisions_block(), entry(), outside_paths(), test_entries_follow_number_order_not_index_order(), test_missing_area_file_and_entry_keep_the_title_with_one_warning(), test_missing_notes_are_none(), test_paths_outside_the_repo_are_never_read() (+3 more)

### Community 125 - "Community 125"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 126 - "Community 126"
Cohesion: 0.11
Nodes (13): GET, Handler, Job, JOB_ID, NAMES, openDialog(), Panel(), POST (+5 more)

### Community 127 - "Community 127"
Cohesion: 0.22
Nodes (9): RunRegistry, jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once(), test_one_plan_per_project_at_a_time() (+1 more)

### Community 128 - "Community 128"
Cohesion: 0.16
Nodes (10): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+2 more)

### Community 129 - "Community 129"
Cohesion: 0.22
Nodes (10): auth(), etag(), fixture_tickets(), test_conflicting_edit(), test_get_then_put_unchanged_is_byte_identical(), test_list_with_filters(), test_status_changes_follow_the_transition_table(), test_ticket_ids_are_checked_in_the_path() (+2 more)

### Community 130 - "Community 130"
Cohesion: 0.21
Nodes (7): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), _validation_error()

### Community 131 - "Community 131"
Cohesion: 0.19
Nodes (7): cancel_job(), dismiss_job(), get_job(), _jobs(), JobView, RollbackView, StepView

### Community 132 - "Community 132"
Cohesion: 0.12
Nodes (7): _cost(), list_command(), _policy(), _run_log(), show_command(), _tokens(), _pull_request()

### Community 133 - "Community 133"
Cohesion: 0.16
Nodes (5): _deps(), edit_command(), list_command(), set_status_command(), show_command()

### Community 134 - "Community 134"
Cohesion: 0.24
Nodes (15): describe(), RuleHit, change(), decide(), test_a_project_list_replaces_the_default(), test_a_rename_hits_on_either_name(), test_delivery_mode(), test_describe_reads_stored_rules() (+7 more)

### Community 135 - "Community 135"
Cohesion: 0.15
Nodes (10): parse_done_when(), DoneItem, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants(), test_done_when_ignores_code_fences() (+2 more)

### Community 136 - "Community 136"
Cohesion: 0.18
Nodes (13): _api_routes(), test_bodies_over_1_mb_are_refused(), test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port() (+5 more)

### Community 137 - "Community 137"
Cohesion: 0.25
Nodes (9): generate(), test_a_copier_failure_is_reported(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_template_without_a_test_command_is_rejected(), test_an_empty_existing_folder_is_used(), test_tasks_from_an_include_are_refused_by_copier_and_never_run(), test_the_users_copier_trust_list_is_ignored() (+1 more)

### Community 138 - "Community 138"
Cohesion: 0.24
Nodes (11): test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install() (+3 more)

### Community 139 - "Community 139"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 140 - "Community 140"
Cohesion: 0.14
Nodes (5): _message(), _model_at(), _number(), split_error(), test_split_error()

### Community 141 - "Community 141"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 142 - "Community 142"
Cohesion: 0.16
Nodes (7): commit_file(), set_identity(), anonymise(), manager(), wt_repo(), wt_root(), test_real_review_names_the_missing_test()

### Community 143 - "Community 143"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 144 - "Community 144"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 145 - "Community 145"
Cohesion: 0.19
Nodes (8): AttemptView, CurrentRun, Discarded, MergedView, PhaseLine, PolicyView, Reject, RuleHitView

### Community 146 - "Community 146"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 147 - "Community 147"
Cohesion: 0.12
Nodes (17): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+9 more)

### Community 148 - "Community 148"
Cohesion: 0.24
Nodes (7): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from(), test_testing_a_secret_needs_the_token_and_a_known_name(), test_testing_a_secret_never_returns_or_logs_it()

### Community 149 - "Community 149"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 150 - "Community 150"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 151 - "Community 151"
Cohesion: 0.22
Nodes (12): AttemptFinishedData, AttemptStartedData, AuthMessage, _Data, EventEnvelope, IntegrateData, LogData, PolicyDecisionData (+4 more)

### Community 152 - "Community 152"
Cohesion: 0.22
Nodes (8): EditConflict, etag_of(), _lock(), read_with_etag(), write_if_match(), test_concurrent_edits_with_the_same_etag_let_one_win(), edit(), test_write_only_when_the_etag_matches()

### Community 153 - "Community 153"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 154 - "Community 154"
Cohesion: 0.17
Nodes (4): _openapi(), health(), Health, create_app()

### Community 155 - "Community 155"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 156 - "Community 156"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 157 - "Community 157"
Cohesion: 0.23
Nodes (12): fixture_text(), base_chars(), big_spec(), fenced_content(), test_cap_excerpt(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections() (+4 more)

### Community 158 - "Community 158"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 159 - "Community 159"
Cohesion: 0.30
Nodes (6): approve_plan(), generate_plan(), _plans(), GeneratePlan, PlanApproved, PlanStarted

### Community 160 - "Community 160"
Cohesion: 0.14
Nodes (4): describe(), print_run(), check_command(), list_command()

### Community 163 - "Community 163"
Cohesion: 0.30
Nodes (10): make_plan(), test_a_failed_write_leaves_the_old_files(), test_a_title_that_needs_quotes_stays_valid_yaml(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members() (+2 more)

### Community 164 - "Community 164"
Cohesion: 0.27
Nodes (5): just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 165 - "Community 165"
Cohesion: 0.19
Nodes (7): allowed_env(), child_env(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start(), test_windows_names_match_in_any_case(), test_child_env_is_an_allowlist()

### Community 166 - "Community 166"
Cohesion: 0.17
Nodes (4): test_client_connection_refused(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 167 - "Community 167"
Cohesion: 0.27
Nodes (7): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd()

### Community 168 - "Community 168"
Cohesion: 0.24
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 169 - "Community 169"
Cohesion: 0.38
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 170 - "Community 170"
Cohesion: 0.32
Nodes (4): agents(), AgentsView, BackendView, GraphifyView

### Community 172 - "Community 172"
Cohesion: 0.26
Nodes (6): latest_phase(), project_totals(), Totals, test_an_empty_log_has_no_usage_and_no_activity(), test_last_activity_is_the_latest_event_and_the_step_its_phase(), test_usage_sums_tokens_and_cost_across_runs()

### Community 173 - "Community 173"
Cohesion: 0.26
Nodes (5): Base, client(), test_session(), engine(), session()

### Community 174 - "Community 174"
Cohesion: 0.27
Nodes (7): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 175 - "Community 175"
Cohesion: 0.24
Nodes (9): test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file(), test_token_budget() (+1 more)

### Community 176 - "Community 176"
Cohesion: 0.25
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 177 - "Community 177"
Cohesion: 0.20
Nodes (4): parse_numstat(), staged_changes(), test_parse_numstat_with_a_rename_and_a_binary(), test_staged_changes_names_both_sides_of_a_rename()

### Community 178 - "Community 178"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 180 - "Community 180"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 181 - "Community 181"
Cohesion: 0.40
Nodes (4): Item, create_item(), get_item(), list_items()

### Community 182 - "Community 182"
Cohesion: 0.25
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 185 - "Community 185"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 186 - "Community 186"
Cohesion: 0.31
Nodes (4): App(), root, HomePage(), react-dom

### Community 187 - "Community 187"
Cohesion: 0.31
Nodes (3): describe(), StatusPill(), TopBar()

### Community 188 - "Community 188"
Cohesion: 0.36
Nodes (3): list_templates(), TemplateCommandsView, TemplateView

### Community 190 - "Community 190"
Cohesion: 0.39
Nodes (6): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_one_line_drops_control_and_format_characters(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 191 - "Community 191"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 192 - "Community 192"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 193 - "Community 193"
Cohesion: 0.36
Nodes (4): test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 196 - "Community 196"
Cohesion: 0.32
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 199 - "Community 199"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 200 - "Community 200"
Cohesion: 0.29
Nodes (4): _fail_after_yaml(), test_failed_rename_leaves_nothing(), test_failure_mid_init_leaves_nothing(), test_missing_git_is_reported()

### Community 204 - "Community 204"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 208 - "Community 208"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 217 - "Community 217"
Cohesion: 0.67
Nodes (3): dependencies, react, react-dom

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `Config`, `InvalidRequest`, `NotRunning` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2220 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **171 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 27` to `Community 0`, `Community 1`, `Community 4`, `Community 7`, `Community 9`, `Community 18`, `Community 156`, `Community 29`, `Community 31`, `Community 32`, `Community 172`, `Community 174`, `Community 60`, `Community 63`, `Community 70`, `Community 209`, `Community 84`, `Community 105`, `Community 106`, `Community 111`, `Community 127`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `RunLog` (e.g. with `page_runs()` and `recover_interrupted()`) actually correct?**
  _`RunLog` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `Config` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.037821827295511506 - nodes in this community are weakly interconnected._
- **Why does `load_project()` connect `Community 34` to `Community 0`, `Community 4`, `Community 8`, `Community 138`, `Community 139`, `Community 11`, `Community 21`, `Community 24`, `Community 31`, `Community 32`, `Community 161`, `Community 33`, `Community 164`, `Community 40`, `Community 169`, `Community 44`, `Community 48`, `Community 54`, `Community 57`, `Community 60`, `Community 198`, `Community 201`, `Community 75`, `Community 76`, `Community 78`, `Community 81`, `Community 83`, `Community 107`, `Community 118`, `Community 127`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 66 inferred relationships involving `load_project()` (e.g. with `_load()` and `_settings_data()`) actually correct?**
  _`load_project()` has 66 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05380333951762523 - nodes in this community are weakly interconnected._