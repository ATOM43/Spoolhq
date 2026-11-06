# Graph Report - Project_Manager  (2026-11-06)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 6859 nodes · 19822 edges · 348 communities (188 shown, 160 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1613 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d7020ce9`
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
- Community 201
- Community 202
- Community 203
- Community 205
- Community 206
- Community 337
- Community 338
- Community 339

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 134 edges
2. `load_project()` - 90 edges
3. `WorktreeManager` - 83 edges
4. `RunRegistry` - 83 edges
5. `FakeRunner` - 74 edges
6. `AgentPolicy` - 69 edges
7. `ClaudeStreamParser` - 61 edges
8. `build_implementer_prompt()` - 60 edges
9. `Transcripts` - 55 edges
10. `run_git()` - 52 edges

## Surprising Connections (you probably didn't know these)
- `schema()` --uses--> `Settings`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/core/config.py
- `schema()` --calls--> `create_app()`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/api/app.py
- `unblock()` --calls--> `RunLoopError`  [INFERRED]
  daemon/tests/api/test_tickets.py → daemon/src/spoolhq/services/runloop/model.py
- `test_codex_not_logged_in_says_codex_login()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py

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

## Communities (348 total, 160 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (71): Plan, PlanProblem, problemLabel(), useApprovePlan(), useGeneratePlan(), usePlan(), splitDoneWhen(), RuleHit (+63 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (23): approve(), reject(), unblock(), _user_approved(), _waiting(), last_merged(), HoldForIntegration, IntegrationStatus (+15 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (32): fail(), hours(), settings(), table(), approve_command(), check_command(), describe_plan(), generate_command() (+24 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (56): AppRouter(), router, RootLayout(), routes, BODIES, invokeMock, COALESCE_MS, EventSource (+48 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (49): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), summarize(), _usage_counts(), usd_to_micro(), assistant() (+41 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (58): ClaudeCliRunner, AgentPolicy, test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version(), test_lists_the_installed_backend() (+50 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (19): retries_used(), decode_cursor(), encode_cursor(), page_runs(), RunPage, _check_count(), _make_attempt_dir(), RunLog (+11 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (51): root, queryClient, QueryProvider(), Loaded(), Panel(), DAEMON_HOST, DAEMON_START_COMMAND, cn() (+43 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (38): clean_title(), InvalidPlan, _not_blank(), one_line(), PlanInvalid, PlannedTicket, PlannerError, PlanOutput (+30 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (60): state_db_path(), state_dir(), seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first() (+52 more)

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (40): Agents, auth(), _ended(), finished(), post(), refused(), test_a_failing_test_command_and_its_rollback(), test_a_project_being_created_is_reported_as_creating() (+32 more)

### Community 11 - "Community 11"
Cohesion: 0.04
Nodes (26): logged_in(), clock(), FakeGates, make_loop(), make(), Merging, project(), registry() (+18 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (27): approve_plan(), format_errors(), parse_done_when(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError (+19 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (21): weighted_tokens(), keep_end(), PolicyViolation, CodexStreamParser, _int(), BackendInfo, check_command(), FileEdit (+13 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (54): Agents, useAgents(), checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning (+46 more)

### Community 15 - "Community 15"
Cohesion: 0.05
Nodes (60): latestReview(), verdicts(), cancelJob(), cleanupToast(), CreateRequest, fieldError(), Job, JobStep (+52 more)

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (46): api_key(), no_parent_key(), test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript(), record(), run() (+38 more)

### Community 17 - "Community 17"
Cohesion: 0.06
Nodes (26): _kill_tree(), ProcessResult, run_process(), _signal_group(), _stop_tree(), _wait(), test_serve_accepts_the_event_websocket(), test_serve_starts_and_serves_docs() (+18 more)

### Community 18 - "Community 18"
Cohesion: 0.05
Nodes (29): check_ticket_id(), slugify(), branch_name(), branch_sha(), default_branch_sha(), DirtyRepoError, ensure_no_operation_in_progress(), has_local_branch() (+21 more)

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (46): ProjectDetail, ProjectSummary, useProject(), useProjects(), loadSpec(), saveSpec(), SPEC_FILE, SpecFile (+38 more)

### Community 20 - "Community 20"
Cohesion: 0.06
Nodes (20): AgentSdkRunner, policy_parts(), billing_for(), format_version(), parse_version(), platform_reason(), probe(), build_argv() (+12 more)

### Community 21 - "Community 21"
Cohesion: 0.07
Nodes (27): approval_message(), decide(), read_artifact(), _result(), IntegrationResult, agent_stopped(), attempt_once(), check_resolved() (+19 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (45): denials_except(), home_denials(), assert_refused(), read_only(), read_record(), refused_message(), run(), runner() (+37 more)

### Community 23 - "Community 23"
Cohesion: 0.07
Nodes (29): id_key(), PlanError, PlanProblem, SchedulerError, TicketEditError, TicketLockedError, TransitionError, _find_cycles() (+21 more)

### Community 24 - "Community 24"
Cohesion: 0.07
Nodes (48): _and_list(), validate_plan(), explain_idle(), apply_transition(), check_transition(), edit_ticket(), parse_status(), copy_dashboard() (+40 more)

### Community 25 - "Community 25"
Cohesion: 0.10
Nodes (56): load_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated(), test_bad_file_name() (+48 more)

### Community 26 - "Community 26"
Cohesion: 0.10
Nodes (33): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+25 more)

### Community 27 - "Community 27"
Cohesion: 0.07
Nodes (20): attempt_dir_name(), AttemptStatus, Event, EventKind, RunKind, RunStatus, Usage, record_policy() (+12 more)

### Community 28 - "Community 28"
Cohesion: 0.06
Nodes (31): builtin_fixture(), client(), clock(), fake_backend(), fake_claude_cmd(), fake_codex_cmd(), fake_graphify(), fake_sdk_cmd() (+23 more)

### Community 29 - "Community 29"
Cohesion: 0.08
Nodes (40): ChangedFile, as_record(), _compile(), delivery_mode(), describe(), evaluate(), _listed(), path_matches() (+32 more)

### Community 30 - "Community 30"
Cohesion: 0.05
Nodes (17): EventBus, Subscription, FixedClock, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others() (+9 more)

### Community 31 - "Community 31"
Cohesion: 0.10
Nodes (30): service_errors(), approve_ticket(), cancel_run(), current_run(), discard_ticket(), get_run(), _loop(), pause_run() (+22 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (44): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), test_fixture_docs_fit_untrimmed(), test_negative_cap_is_refused() (+36 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (48): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_a_workspace_can_be_written_before_its_repo(), test_all_errors_are_reported_at_once() (+40 more)

### Community 34 - "Community 34"
Cohesion: 0.08
Nodes (40): Listener, listeners, openSettings(), SettingsTab, useOpenRequests(), Agents, backendReady(), DaemonSettings (+32 more)

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (29): advance(), checked_out(), _clean_line(), commit(), conclude_merge(), conflict_files(), create_tag(), ensure_main_ready() (+21 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (45): git_executable(), remove_path(), WorktreeManager, run_git(), branches(), make_read_only(), marker(), real() (+37 more)

### Community 37 - "Community 37"
Cohesion: 0.07
Nodes (23): dump(), dumper(), loader(), merge(), parse(), read(), to_plain(), write_atomic() (+15 more)

### Community 38 - "Community 38"
Cohesion: 0.08
Nodes (26): build_argv(), child_env(), install_dir(), permission_profile(), policy_parts(), refusal(), required_parts(), temp_folders() (+18 more)

### Community 39 - "Community 39"
Cohesion: 0.07
Nodes (24): remoteHost(), PATHS, RunAction, useRunAction(), formatUsage(), guidance(), idleReason(), PanelState (+16 more)

### Community 40 - "Community 40"
Cohesion: 0.09
Nodes (22): CheckResult, load_contract(), _message(), parse_contract(), _Strict, TemplateCommands, TemplateContract, TemplateError (+14 more)

### Community 41 - "Community 41"
Cohesion: 0.08
Nodes (37): ensure_clean(), status_entries(), check_git_version(), GitResult, fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it() (+29 more)

### Community 42 - "Community 42"
Cohesion: 0.05
Nodes (14): create_app(), lifespan(), _openapi(), health(), version(), Health, Version, check_git() (+6 more)

### Community 43 - "Community 43"
Cohesion: 0.19
Nodes (33): LocalIntegrator, _assistant(), _init(), _result(), Transcripts, git(), hooked(), kinds() (+25 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (26): require_if_match(), put(), _conflict(), create_project(), _creating(), get_project(), get_settings(), get_spec() (+18 more)

### Community 45 - "Community 45"
Cohesion: 0.13
Nodes (28): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+20 more)

### Community 46 - "Community 46"
Cohesion: 0.06
Nodes (6): billing_error(), CliTransport, SdkRun, stop(), _signal_group(), test_billing_errors_are_recognised()

### Community 47 - "Community 47"
Cohesion: 0.08
Nodes (27): cap_excerpt(), keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec() (+19 more)

### Community 48 - "Community 48"
Cohesion: 0.07
Nodes (39): engines, node, name, packageManager, private, type, version, description (+31 more)

### Community 49 - "Community 49"
Cohesion: 0.10
Nodes (24): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+16 more)

### Community 50 - "Community 50"
Cohesion: 0.10
Nodes (17): DaemonNotRunning, serve(), _serve(), _Server, load_or_create_token(), read_token(), token_path(), config_path() (+9 more)

### Community 51 - "Community 51"
Cohesion: 0.09
Nodes (19): make_runner(), ProjectError, ProjectValidationError, check_slug(), Project, has_spec(), init_project(), _initial_yaml() (+11 more)

### Community 52 - "Community 52"
Cohesion: 0.08
Nodes (6): marker_key(), _norm(), RegisteredWorktree, same_path(), Worktree, WorktreeSession

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (17): GitHubClient, GitHubError, create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull() (+9 more)

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 55 - "Community 55"
Cohesion: 0.12
Nodes (28): asTyped(), BodyParts, DoneItem, joinBody(), splitBody(), saveTicket(), NOTE_MAX, NoteKind (+20 more)

### Community 56 - "Community 56"
Cohesion: 0.09
Nodes (16): GateLine, ItemVerdict, ReviewResult, _gate_word(), _ignore(), _items(), render_review_prompt(), review() (+8 more)

### Community 57 - "Community 57"
Cohesion: 0.16
Nodes (25): kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt(), test_changes_requested_three_times_blocks() (+17 more)

### Community 58 - "Community 58"
Cohesion: 0.08
Nodes (16): Agents, BackendSettings, Budget, _check_base_url(), _check_path_pattern(), Commands, ContextSettings, GatesSettings (+8 more)

### Community 59 - "Community 59"
Cohesion: 0.15
Nodes (19): Delivery, ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note() (+11 more)

### Community 60 - "Community 60"
Cohesion: 0.10
Nodes (15): run_log(), settings(), workspace(), Artifact, get_artifact(), list_runs(), get_ticket(), get_tickets() (+7 more)

### Community 61 - "Community 61"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 62 - "Community 62"
Cohesion: 0.11
Nodes (16): _read(), show_command(), ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, GateFailure (+8 more)

### Community 63 - "Community 63"
Cohesion: 0.14
Nodes (14): all_command(), approve_command(), _base(), _call(), cancel_command(), _control(), discard_command(), _follow() (+6 more)

### Community 64 - "Community 64"
Cohesion: 0.10
Nodes (15): check_command(), check_path(), check_tool(), make_hook(), pre_tool_use(), relative_pattern(), call_hook(), test_the_hook_allows_allowlisted_commands() (+7 more)

### Community 65 - "Community 65"
Cohesion: 0.13
Nodes (24): commit_message(), git_out(), head(), _squash(), _stage_link(), test_advance_fast_forwards_the_checked_out_branch(), test_advance_refuses_a_dirty_checkout(), test_advance_reports_main_moved() (+16 more)

### Community 66 - "Community 66"
Cohesion: 0.16
Nodes (19): events(), close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run() (+11 more)

### Community 67 - "Community 67"
Cohesion: 0.08
Nodes (8): ApiClient, ApiError, _detail(), version(), _client(), Settings, test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401()

### Community 68 - "Community 68"
Cohesion: 0.11
Nodes (12): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+4 more)

### Community 69 - "Community 69"
Cohesion: 0.13
Nodes (19): capture(), on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact() (+11 more)

### Community 70 - "Community 70"
Cohesion: 0.14
Nodes (16): _get(), get_integration(), Integration, IntegrationState, last_integration(), open_integrations(), pull_request_integration(), set_integration_state() (+8 more)

### Community 71 - "Community 71"
Cohesion: 0.10
Nodes (19): useDismissJob(), useInterruptedRun(), MAX_CARDS, NeedsYouCard, needsYouCards(), NeedsYouKind, sentence(), TicketLike (+11 more)

### Community 72 - "Community 72"
Cohesion: 0.13
Nodes (17): adapter(), AdapterCase, agent_sdk(), claude_cli(), codex_cli(), fake(), run(), record() (+9 more)

### Community 73 - "Community 73"
Cohesion: 0.08
Nodes (5): billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), test_real_codex_run_creates_a_file_and_cannot_read_ssh()

### Community 74 - "Community 74"
Cohesion: 0.11
Nodes (10): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), problem_view(), _validation_error() (+2 more)

### Community 75 - "Community 75"
Cohesion: 0.22
Nodes (24): FakeRunner, ReviewInputs, run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages(), test_cancelled_is_passed_through() (+16 more)

### Community 76 - "Community 76"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 77 - "Community 77"
Cohesion: 0.11
Nodes (12): RunRegistry, start(), jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once() (+4 more)

### Community 78 - "Community 78"
Cohesion: 0.10
Nodes (20): child_env(), sandbox_settings(), test_reviewer_and_planner_get_no_write_or_bash(), parent_env(), settings_json(), test_a_custom_endpoint_gets_spoolhqs_token_and_no_login(), test_api_billing_keeps_only_the_api_key(), test_argv_is_exactly_the_documented_command_line() (+12 more)

### Community 79 - "Community 79"
Cohesion: 0.13
Nodes (16): _area_entries(), expand_index(), _inside(), _read(), read_repo_docs(), read_text(), decisions_block(), entry() (+8 more)

### Community 80 - "Community 80"
Cohesion: 0.17
Nodes (18): create(), git_state(), jobs_for(), snapshot(), source_fields(), states(), test_a_commit_without_an_identity_fails_and_rolls_back(), test_a_failing_test_command_names_its_field() (+10 more)

### Community 81 - "Community 81"
Cohesion: 0.11
Nodes (14): set_command(), store_api_key(), backend_names(), endpoint_token(), keyring_key(), missing_token(), store_endpoint_token(), token_var() (+6 more)

### Community 82 - "Community 82"
Cohesion: 0.21
Nodes (19): cache_dir(), refresh(), FakeGraphify, builds(), pointer(), source(), test_a_busy_cache_gives_no_map(), test_a_cache_from_another_version_is_discarded() (+11 more)

### Community 83 - "Community 83"
Cohesion: 0.10
Nodes (13): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+5 more)

### Community 84 - "Community 84"
Cohesion: 0.17
Nodes (20): auth(), edit(), etag(), fixture_tickets(), test_a_title_edit_changes_only_the_title_line(), test_an_edit_that_breaks_the_plan_is_422_with_the_field(), test_an_edit_while_running_is_409(), test_conflicting_edit() (+12 more)

### Community 85 - "Community 85"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 86 - "Community 86"
Cohesion: 0.13
Nodes (12): _check(), check_secret(), SecretCheck, read_secret(), answer(), handler(), fail(), test_a_redirect_is_not_followed() (+4 more)

### Community 87 - "Community 87"
Cohesion: 0.11
Nodes (9): _authenticate(), _convert(), _Envelopes, EventStreams, _send(), _stream(), listener(), _until_disconnect() (+1 more)

### Community 88 - "Community 88"
Cohesion: 0.16
Nodes (11): DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when(), _not_run(), _run_gate() (+3 more)

### Community 89 - "Community 89"
Cohesion: 0.13
Nodes (14): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), example(), test_task_md_example_project_yaml_validates() (+6 more)

### Community 90 - "Community 90"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 91 - "Community 91"
Cohesion: 0.11
Nodes (7): _Cancelled, _Failed, roll_back(), Rollback, Runner, Step, Checked

### Community 92 - "Community 92"
Cohesion: 0.16
Nodes (13): _check_branch(), _check_existing(), _check_new(), check_request(), _commands(), CreateProject, CreationError, _current_branch() (+5 more)

### Community 93 - "Community 93"
Cohesion: 0.12
Nodes (9): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements(), _user_version(), utc_now() (+1 more)

### Community 94 - "Community 94"
Cohesion: 0.12
Nodes (18): build_excerpt(), take(), clean(), _clip(), failing_tests(), first_failure(), _priority(), split_lines() (+10 more)

### Community 95 - "Community 95"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 96 - "Community 96"
Cohesion: 0.17
Nodes (19): gates(), test_all_passing(), test_an_unset_command_is_skipped_and_the_run_still_passes(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+11 more)

### Community 97 - "Community 97"
Cohesion: 0.11
Nodes (7): test_template_is_in_the_built_wheel(), generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 98 - "Community 98"
Cohesion: 0.15
Nodes (14): _check_decisions(), _decisions(), folders(), _script(), test_a_consistent_fixture_passes(), test_a_duplicated_number_fails(), test_a_mismatched_title_fails(), test_a_missing_number_fails() (+6 more)

### Community 99 - "Community 99"
Cohesion: 0.08
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 100 - "Community 100"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 101 - "Community 101"
Cohesion: 0.13
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 102 - "Community 102"
Cohesion: 0.11
Nodes (11): ticket_branch(), _pr_state(), ticket_runs(), TicketGit, _branch_of(), finish(), _hint(), publish_tag() (+3 more)

### Community 103 - "Community 103"
Cohesion: 0.09
Nodes (7): dotted_path(), _message(), _model_at(), _number(), split_error(), EditConflict, test_split_error()

### Community 104 - "Community 104"
Cohesion: 0.20
Nodes (12): createItem(), getItem(), listItems(), Item, NewItem, ItemList(), CreateItemForm(), submit() (+4 more)

### Community 105 - "Community 105"
Cohesion: 0.25
Nodes (15): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_attempt_artifacts(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_history_pages_are_stable_under_inserts() (+7 more)

### Community 106 - "Community 106"
Cohesion: 0.13
Nodes (7): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState

### Community 107 - "Community 107"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 108 - "Community 108"
Cohesion: 0.13
Nodes (9): agents_command(), describe(), describe_graphify(), describe_roles(), describe_worktrees(), find_command(), Graphify, probe() (+1 more)

### Community 109 - "Community 109"
Cohesion: 0.23
Nodes (15): auth(), get_plan(), plan_client(), test_a_clean_approve_makes_the_drafts_ready(), test_an_invalid_ticket_file_is_a_problem(), test_approve_with_problems_is_409_and_changes_nothing(), test_each_problem_has_its_code_and_ticket_ids(), test_every_plan_route_needs_the_token() (+7 more)

### Community 110 - "Community 110"
Cohesion: 0.25
Nodes (15): auth(), error(), etag(), test_an_invalid_project_yaml_is_listed_with_its_first_problem(), test_list_and_get_projects(), test_project_detail_says_why_nothing_can_run(), test_settings_edit_with_etags(), test_spec_edit_with_etags() (+7 more)

### Community 111 - "Community 111"
Cohesion: 0.09
Nodes (6): describe(), print_run(), run_command(), check_command(), describe_source(), list_command()

### Community 112 - "Community 112"
Cohesion: 0.25
Nodes (20): block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason(), test_gate_checked_items_replace_the_reviewers_answer() (+12 more)

### Community 113 - "Community 113"
Cohesion: 0.18
Nodes (16): is_git_url(), _is_path(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder() (+8 more)

### Community 114 - "Community 114"
Cohesion: 0.18
Nodes (11): _build(), CodeMap, _current(), _drop(), _refresh(), _remove_unused(), _save(), GraphifyError (+3 more)

### Community 116 - "Community 116"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 117 - "Community 117"
Cohesion: 0.11
Nodes (3): _Job, PlanJobs, planner_code_map()

### Community 118 - "Community 118"
Cohesion: 0.19
Nodes (14): start_edit(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_edit_aborted_prompt_restores(), test_edit_interrupted_restores(), test_edit_invalid_restores_the_backup(), test_edit_invalid_then_reopen() (+6 more)

### Community 119 - "Community 119"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 120 - "Community 120"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 121 - "Community 121"
Cohesion: 0.17
Nodes (7): delete_secret(), _lookup(), secret_status(), SecretStatus, store_secret(), test_empty_values_and_an_unreadable_keychain(), test_environment_wins_over_the_keychain()

### Community 122 - "Community 122"
Cohesion: 0.11
Nodes (6): code(), fenced(), _PromptLoader, PromptTemplate, render_template(), _template_line()

### Community 123 - "Community 123"
Cohesion: 0.19
Nodes (5): ahead_message(), _failed(), _held(), pr_branch(), set_pull_request()

### Community 124 - "Community 124"
Cohesion: 0.11
Nodes (15): RUN_GOING, attempt, GET, Handler, Init, NO_GIT, POST, PRIMARY (+7 more)

### Community 125 - "Community 125"
Cohesion: 0.21
Nodes (14): test_a_git_template_check_runs_no_global_git_hooks(), test_init_an_empty_repo_on_a_branch(), test_init_an_existing_repo_then_validate(), test_init_existing_folder(), test_init_from_a_git_template_at_a_ref(), test_init_from_a_local_folder_template(), test_init_from_a_template_fills_its_commands(), test_init_refuses_a_bad_branch_name() (+6 more)

### Community 126 - "Community 126"
Cohesion: 0.15
Nodes (5): _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 127 - "Community 127"
Cohesion: 0.19
Nodes (8): ApiError, cancel_job(), dismiss_job(), get_job(), _jobs(), JobView, RollbackView, StepView

### Community 129 - "Community 129"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 130 - "Community 130"
Cohesion: 0.13
Nodes (10): check_gate_command(), gate_env(), resolve_program(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument() (+2 more)

### Community 131 - "Community 131"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 132 - "Community 132"
Cohesion: 0.25
Nodes (9): generate(), test_a_copier_failure_is_reported(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_template_without_a_test_command_is_rejected(), test_an_empty_existing_folder_is_used(), test_tasks_from_an_include_are_refused_by_copier_and_never_run(), test_the_users_copier_trust_list_is_ignored() (+1 more)

### Community 133 - "Community 133"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 134 - "Community 134"
Cohesion: 0.11
Nodes (5): _client(), sync_command(), validate_project(), describe(), review_command()

### Community 135 - "Community 135"
Cohesion: 0.16
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 136 - "Community 136"
Cohesion: 0.25
Nodes (9): approve_plan(), generate_plan(), get_plan(), _plans(), GeneratePlan, PlanApproved, PlanProblemView, PlanStarted (+1 more)

### Community 137 - "Community 137"
Cohesion: 0.19
Nodes (9): check_secret_route(), delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretTest, SecretValue (+1 more)

### Community 138 - "Community 138"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 139 - "Community 139"
Cohesion: 0.19
Nodes (12): _api_routes(), test_bodies_over_1_mb_are_refused(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token() (+4 more)

### Community 140 - "Community 140"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 141 - "Community 141"
Cohesion: 0.11
Nodes (18): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+10 more)

### Community 142 - "Community 142"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 143 - "Community 143"
Cohesion: 0.20
Nodes (12): AttemptFinishedData, AttemptStartedData, AuthMessage, _Data, EventEnvelope, IntegrateData, LogData, PolicyDecisionData (+4 more)

### Community 144 - "Community 144"
Cohesion: 0.20
Nodes (10): parse_worktree_list(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+2 more)

### Community 145 - "Community 145"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 146 - "Community 146"
Cohesion: 0.24
Nodes (7): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from(), test_testing_a_secret_needs_the_token_and_a_known_name(), test_testing_a_secret_never_returns_or_logs_it()

### Community 147 - "Community 147"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 148 - "Community 148"
Cohesion: 0.22
Nodes (11): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning(), test_spec_ties_keep_document_order() (+3 more)

### Community 149 - "Community 149"
Cohesion: 0.18
Nodes (12): editor_command(), _unquote(), test_default_environment(), test_editor_that_cannot_start(), test_editor_when_visual_is_blank(), test_fallback_editors(), test_missing_editor(), test_posix_quoting() (+4 more)

### Community 150 - "Community 150"
Cohesion: 0.16
Nodes (8): test_client_connection_refused(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon(), test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 151 - "Community 151"
Cohesion: 0.18
Nodes (6): commit_file(), anonymise(), manager(), wt_repo(), wt_root(), test_real_review_names_the_missing_test()

### Community 152 - "Community 152"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 153 - "Community 153"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 154 - "Community 154"
Cohesion: 0.23
Nodes (7): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_serve_refuses_while_another_daemon_holds_the_lock(), test_startup_recovers_and_skips_a_corrupt_database(), test_startup_without_a_projects_folder_serves()

### Community 155 - "Community 155"
Cohesion: 0.21
Nodes (7): github_token(), store_github_token(), test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins(), test_the_keychain()

### Community 156 - "Community 156"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 157 - "Community 157"
Cohesion: 0.22
Nodes (5): create_app(), client(), test_session(), engine(), session()

### Community 158 - "Community 158"
Cohesion: 0.16
Nodes (4): test_health(), Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token()

### Community 160 - "Community 160"
Cohesion: 0.31
Nodes (5): Base, Item, create_item(), get_item(), list_items()

### Community 161 - "Community 161"
Cohesion: 0.27
Nodes (7): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd()

### Community 162 - "Community 162"
Cohesion: 0.24
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 163 - "Community 163"
Cohesion: 0.33
Nodes (9): make_plan(), test_a_failed_write_leaves_the_old_files(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members(), test_approving_twice_gives_nothing_to_approve() (+1 more)

### Community 164 - "Community 164"
Cohesion: 0.38
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 166 - "Community 166"
Cohesion: 0.32
Nodes (4): agents(), AgentsView, BackendView, GraphifyView

### Community 167 - "Community 167"
Cohesion: 0.24
Nodes (5): _generated_at(), plan_overview(), PlanOverview, _invalid_problem(), plan_problems()

### Community 168 - "Community 168"
Cohesion: 0.32
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 169 - "Community 169"
Cohesion: 0.24
Nodes (9): test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file(), test_token_budget() (+1 more)

### Community 170 - "Community 170"
Cohesion: 0.29
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 171 - "Community 171"
Cohesion: 0.20
Nodes (4): parse_numstat(), staged_changes(), test_parse_numstat_with_a_rename_and_a_binary(), test_staged_changes_names_both_sides_of_a_rename()

### Community 172 - "Community 172"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 174 - "Community 174"
Cohesion: 0.31
Nodes (7): etag_of(), _lock(), read_with_etag(), write_if_match(), test_concurrent_edits_with_the_same_etag_let_one_win(), edit(), test_write_only_when_the_etag_matches()

### Community 175 - "Community 175"
Cohesion: 0.27
Nodes (3): get_engine(), get_session(), make_engine()

### Community 176 - "Community 176"
Cohesion: 0.27
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 177 - "Community 177"
Cohesion: 0.31
Nodes (6): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project()

### Community 178 - "Community 178"
Cohesion: 0.27
Nodes (5): allowed_env(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start(), test_windows_names_match_in_any_case()

### Community 179 - "Community 179"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 180 - "Community 180"
Cohesion: 0.31
Nodes (4): App(), root, HomePage(), react-dom

### Community 182 - "Community 182"
Cohesion: 0.25
Nodes (3): summary(), test_a_report_without_known_sections_is_empty(), test_keeps_the_map_and_drops_the_rest()

### Community 183 - "Community 183"
Cohesion: 0.36
Nodes (3): list_templates(), TemplateCommandsView, TemplateView

### Community 184 - "Community 184"
Cohesion: 0.28
Nodes (5): available_runners(), make_runner(), test_codex_takes_the_endpoint_and_model(), test_the_agent_sdk_takes_the_endpoint_and_model(), test_the_built_in_backends()

### Community 186 - "Community 186"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 187 - "Community 187"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 189 - "Community 189"
Cohesion: 0.32
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 191 - "Community 191"
Cohesion: 0.46
Nodes (5): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 192 - "Community 192"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 195 - "Community 195"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 198 - "Community 198"
Cohesion: 0.53
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 199 - "Community 199"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 206 - "Community 206"
Cohesion: 0.67
Nodes (3): dependencies, react, react-dom

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `Config`, `InvalidRequest`, `NotRunning` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2261 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **160 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 6` to `Community 1`, `Community 2`, `Community 9`, `Community 18`, `Community 21`, `Community 154`, `Community 27`, `Community 30`, `Community 35`, `Community 42`, `Community 43`, `Community 177`, `Community 53`, `Community 54`, `Community 59`, `Community 60`, `Community 66`, `Community 69`, `Community 70`, `Community 74`, `Community 77`, `Community 83`, `Community 84`, `Community 87`, `Community 93`, `Community 102`, `Community 105`, `Community 106`, `Community 117`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `RunLog` (e.g. with `page_runs()` and `recover_interrupted()`) actually correct?**
  _`RunLog` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `Config` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05181787291879035 - nodes in this community are weakly interconnected._
- **Why does `ClaudeStreamParser` connect `Community 4` to `Community 5`, `Community 73`, `Community 13`, `Community 46`, `Community 78`, `Community 20`, `Community 185`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 71 inferred relationships involving `load_project()` (e.g. with `_load()` and `_settings_data()`) actually correct?**
  _`load_project()` has 71 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.04869721473495058 - nodes in this community are weakly interconnected._