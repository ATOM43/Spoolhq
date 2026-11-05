# Graph Report - Project_Manager  (2026-11-05)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 6596 nodes · 18766 edges · 347 communities (181 shown, 166 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1584 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ee5365f7`
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
- Community 194
- Community 198
- Community 200
- Community 201
- Community 335
- Community 336
- Community 337

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 114 edges
2. `load_project()` - 89 edges
3. `WorktreeManager` - 82 edges
4. `AgentPolicy` - 69 edges
5. `RunRegistry` - 69 edges
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

## Communities (347 total, 166 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (28): agents_command(), describe(), describe_roles(), describe_worktrees(), ApiError, DaemonNotRunning, serve(), _serve() (+20 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (26): AgentSdkRunner, api_key(), check_path(), make_hook(), policy_parts(), billing_for(), format_version(), parse_version() (+18 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (65): PlanError, PlanProblem, SchedulerError, TransitionError, _and_list(), _find_cycles(), require_valid(), sort_ids() (+57 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (33): decode_cursor(), encode_cursor(), page_runs(), RunPage, attempt_dir_name(), AttemptStatus, Event, EventKind (+25 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (30): resolve_program(), ProcessResult, run_process(), _signal_group(), _stop_tree(), _wait(), _make_attempt_dir(), test_startup_without_a_projects_folder_serves() (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (65): Agents, useAgents(), checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning (+57 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (48): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), _usage_counts(), usd_to_micro(), assistant(), load() (+40 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (54): useInterruptedRun(), MAX_CARDS, NeedsYouCard, needsYouCards(), NeedsYouKind, sentence(), TicketLike, time() (+46 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (46): _get(), get_integration(), Integration, IntegrationState, last_integration(), open_integrations(), pull_request_integration(), set_integration_state() (+38 more)

### Community 9 - "Community 9"
Cohesion: 0.04
Nodes (44): App(), root, root, queryClient, QueryProvider(), AppRouter(), router, RootLayout() (+36 more)

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (27): format_errors(), edit_ticket(), parse_done_when(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError (+19 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (34): check_ticket_id(), slugify(), advance(), checked_out(), commit(), ensure_main_ready(), MergeIn, branch_name() (+26 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (33): id_key(), clean_title(), InvalidPlan, _not_blank(), one_line(), PlannedTicket, PlannerError, PlanOutput (+25 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (46): auth(), finished(), post(), refused(), test_a_failing_test_command_and_its_rollback(), test_a_project_being_created_is_reported_as_creating(), test_a_rolled_back_project_is_gone_from_the_list(), test_bad_names() (+38 more)

### Community 14 - "Community 14"
Cohesion: 0.05
Nodes (23): create_project(), init(), Job, roll_back(), Rollback, Runner, Step, CreationJobs (+15 more)

### Community 15 - "Community 15"
Cohesion: 0.05
Nodes (18): EventBus, _check_count(), RunLog, Run, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others() (+10 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (54): git_executable(), WorktreeManager, make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_keep_rule(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project(), commit_file() (+46 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (29): last_merged(), HoldForIntegration, IntegrationStatus, Integrator, agent_stopped(), attempt_once(), check_resolved(), commit() (+21 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (38): no_parent_key(), test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript(), record(), run(), runner() (+30 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (13): approve(), reject(), unblock(), _waiting(), RunLoop, Active, Flags, NotBlockedError (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.07
Nodes (31): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+23 more)

### Community 21 - "Community 21"
Cohesion: 0.04
Nodes (20): create_app(), lifespan(), _openapi(), sync(), health(), list_templates(), version(), GitHubSync (+12 more)

### Community 22 - "Community 22"
Cohesion: 0.10
Nodes (57): list_tickets(), load_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated() (+49 more)

### Community 23 - "Community 23"
Cohesion: 0.06
Nodes (18): fail(), settings(), table(), _cost(), list_command(), _policy(), _run_log(), show_command() (+10 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (51): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_a_workspace_can_be_written_before_its_repo(), test_all_errors_are_reported_at_once() (+43 more)

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (39): Listener, listeners, openSettings(), SettingsTab, useOpenRequests(), Agents, DaemonSettings, removeSecret() (+31 more)

### Community 26 - "Community 26"
Cohesion: 0.06
Nodes (16): logged_in(), FakeGates, Merging, transcripts(), main(), codex_review(), set_roles(), test_a_ticket_runs_end_to_end_on_codex() (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (14): _clear_read_only_and_retry(), marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, remove_path(), same_path(), Worktree (+6 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (48): cancelJob(), CreateRequest, fieldError(), Job, JobStep, POLL_MS, startJob(), Template (+40 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (30): check_command(), check_tool(), relative_pattern(), call_hook(), test_reviewer_and_planner_get_no_write_or_bash(), test_the_hook_allows_allowlisted_commands(), test_the_hook_answers_the_sdk(), test_the_hook_confines_file_tools() (+22 more)

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (38): conclude_merge(), conflict_files(), _git(), is_junk(), is_secret(), _matches(), merge_head(), merge_in() (+30 more)

### Community 31 - "Community 31"
Cohesion: 0.10
Nodes (44): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), test_fixture_docs_fit_untrimmed(), test_negative_cap_is_refused() (+36 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (27): service_errors(), approve_ticket(), Artifact, cancel_run(), current_run(), discard_ticket(), get_artifact(), get_run() (+19 more)

### Community 33 - "Community 33"
Cohesion: 0.09
Nodes (18): weighted_tokens(), keep_end(), PolicyViolation, summarize(), CodexStreamParser, _int(), check_command(), FileEdit (+10 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 35 - "Community 35"
Cohesion: 0.16
Nodes (35): LocalIntegrator, _assistant(), _init(), _result(), Transcripts, git(), hooked(), call() (+27 more)

### Community 36 - "Community 36"
Cohesion: 0.10
Nodes (27): require_if_match(), run_log(), settings(), workspace(), _conflict(), _creating(), get_project(), get_settings() (+19 more)

### Community 37 - "Community 37"
Cohesion: 0.08
Nodes (26): build_argv(), child_env(), install_dir(), permission_profile(), policy_parts(), refusal(), required_parts(), temp_folders() (+18 more)

### Community 38 - "Community 38"
Cohesion: 0.09
Nodes (17): create_tag(), is_ancestor(), tag_exists(), too_large(), approval_message(), _branch_of(), finish(), _hint() (+9 more)

### Community 39 - "Community 39"
Cohesion: 0.09
Nodes (29): _api_routes(), test_bodies_over_1_mb_are_refused(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token() (+21 more)

### Community 40 - "Community 40"
Cohesion: 0.09
Nodes (35): ensure_clean(), status_entries(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes() (+27 more)

### Community 41 - "Community 41"
Cohesion: 0.08
Nodes (29): backendReady(), useAgentBlocker(), AUTOSAVE_MS, conflictOf(), SaveState, useSpecAutosave(), planBlocker(), PlanState (+21 more)

### Community 42 - "Community 42"
Cohesion: 0.09
Nodes (28): decide(), read_artifact(), _user_approved(), as_record(), _compile(), delivery_mode(), describe(), evaluate() (+20 more)

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (27): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+19 more)

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (29): assert_refused(), read_only(), read_record(), refused_message(), run(), runner(), temps(), test_a_custom_endpoint_never_gets_the_users_login() (+21 more)

### Community 45 - "Community 45"
Cohesion: 0.18
Nodes (34): endpoint_runner(), read_record(), run(), runner(), test_a_custom_endpoint_never_gets_the_users_login(), test_a_remote_endpoint_without_a_token_is_refused(), test_api_key_billing_passes_the_key_and_the_budget(), test_billing_follows_the_auth_method() (+26 more)

### Community 46 - "Community 46"
Cohesion: 0.06
Nodes (5): billing_error(), CliTransport, SdkRun, stop(), test_billing_errors_are_recognised()

### Community 47 - "Community 47"
Cohesion: 0.08
Nodes (25): cap_excerpt(), keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec() (+17 more)

### Community 48 - "Community 48"
Cohesion: 0.10
Nodes (18): get_ticket(), get_tickets(), put_ticket(), _read(), unblock_ticket(), InvalidTicketView, Note, TicketList (+10 more)

### Community 49 - "Community 49"
Cohesion: 0.09
Nodes (18): _read(), show_command(), ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, GateFailure (+10 more)

### Community 50 - "Community 50"
Cohesion: 0.07
Nodes (18): Agents, BackendSettings, Budget, _check_backend(), _check_base_url(), _check_path_pattern(), Commands, ContextSettings (+10 more)

### Community 51 - "Community 51"
Cohesion: 0.07
Nodes (17): client(), clock(), fake_claude_cmd(), fake_codex_cmd(), fake_sdk_cmd(), FixedClock, git_repo(), make_github_remote() (+9 more)

### Community 52 - "Community 52"
Cohesion: 0.08
Nodes (20): ProjectDetail, settingsErrorLine(), PATHS, RunAction, useRunAction(), formatUsage(), guidance(), idleReason() (+12 more)

### Community 53 - "Community 53"
Cohesion: 0.11
Nodes (17): GitHubClient, GitHubError, create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull() (+9 more)

### Community 54 - "Community 54"
Cohesion: 0.08
Nodes (17): make_runner(), ProjectError, ProjectValidationError, check_slug(), Project, init_project(), _initial_yaml(), InitResult (+9 more)

### Community 55 - "Community 55"
Cohesion: 0.09
Nodes (15): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+7 more)

### Community 56 - "Community 56"
Cohesion: 0.10
Nodes (22): build_argv(), child_env(), sandbox_settings(), AgentPolicy, test_policy_fields_are_untouched_by_credentials_list(), parent_env(), settings_json(), test_a_custom_endpoint_gets_spoolhqs_token_and_no_login() (+14 more)

### Community 57 - "Community 57"
Cohesion: 0.09
Nodes (15): hours(), approve_command(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner() (+7 more)

### Community 58 - "Community 58"
Cohesion: 0.13
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _control(), discard_command() (+7 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (26): FakeRunner, ReviewInputs, test_each_review_is_its_own_run(), OutcomeRunner, run(), test_approve(), test_budget_defaults_and_overrides(), run() (+18 more)

### Community 60 - "Community 60"
Cohesion: 0.09
Nodes (14): GateLine, ItemVerdict, ReviewResult, _gate_word(), _ignore(), _items(), render_review_prompt(), review() (+6 more)

### Community 61 - "Community 61"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 62 - "Community 62"
Cohesion: 0.10
Nodes (12): dump(), loader(), to_plain(), load_contract(), _message(), parse_contract(), TemplateError, check_safe() (+4 more)

### Community 63 - "Community 63"
Cohesion: 0.10
Nodes (16): dumper(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node(), parse_yaml() (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 65 - "Community 65"
Cohesion: 0.19
Nodes (24): kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt(), test_changes_requested_three_times_blocks() (+16 more)

### Community 66 - "Community 66"
Cohesion: 0.09
Nodes (17): set_command(), store_api_key(), available_runners(), backend_names(), make_runner(), endpoint_token(), keyring_key(), store_endpoint_token() (+9 more)

### Community 67 - "Community 67"
Cohesion: 0.09
Nodes (17): describe(), print_run(), check_command(), describe_source(), list_command(), CheckResult, TemplateContract, builtin_contracts() (+9 more)

### Community 68 - "Community 68"
Cohesion: 0.15
Nodes (18): Delivery, ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note() (+10 more)

### Community 69 - "Community 69"
Cohesion: 0.11
Nodes (14): _check(), check_secret(), SecretCheck, _lookup(), read_secret(), store_secret(), answer(), handler() (+6 more)

### Community 70 - "Community 70"
Cohesion: 0.10
Nodes (15): _recover_one(), recover_worktrees(), RecoveryAction, RecoveryEntry, RecoveryReport, WorktreeInfo, WorktreeState, branches() (+7 more)

### Community 71 - "Community 71"
Cohesion: 0.12
Nodes (14): describe_graphify(), _build(), CodeMap, _current(), _drop(), refresh(), _refresh(), _remove_unused() (+6 more)

### Community 72 - "Community 72"
Cohesion: 0.08
Nodes (6): Session, _signal_group(), _stream(), StreamParser, main(), problems()

### Community 73 - "Community 73"
Cohesion: 0.11
Nodes (19): ClaudeCliRunner, test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable() (+11 more)

### Community 74 - "Community 74"
Cohesion: 0.17
Nodes (20): cache_dir(), FakeGraphify, builds(), pointer(), source(), test_a_busy_cache_gives_no_map(), test_a_cache_from_another_version_is_discarded(), test_a_command_that_cannot_start() (+12 more)

### Community 75 - "Community 75"
Cohesion: 0.16
Nodes (18): close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(), stuck() (+10 more)

### Community 76 - "Community 76"
Cohesion: 0.09
Nodes (19): fake_backend(), fake_graphify(), free_port(), git_identity(), home(), isolated_git(), keychain(), no_graphify() (+11 more)

### Community 77 - "Community 77"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 78 - "Community 78"
Cohesion: 0.12
Nodes (27): test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_cache_reads_count_a_tenth_toward_weighted_tokens(), test_empty_folder_left_by_an_uncommitted_attempt_is_reused(), test_ended_run_takes_no_attempts(), test_event_with_an_attempt_of_another_run_is_refused() (+19 more)

### Community 79 - "Community 79"
Cohesion: 0.12
Nodes (13): RunRegistry, WorkspaceRuns, start(), jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs() (+5 more)

### Community 80 - "Community 80"
Cohesion: 0.08
Nodes (5): billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), test_real_codex_run_creates_a_file_and_cannot_read_ssh()

### Community 81 - "Community 81"
Cohesion: 0.13
Nodes (19): capture(), on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact() (+11 more)

### Community 82 - "Community 82"
Cohesion: 0.09
Nodes (21): CREATED_TOAST, NewProjectButton(), GET, Handler, Job, JOB_ID, NAMES, openDialog() (+13 more)

### Community 83 - "Community 83"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 84 - "Community 84"
Cohesion: 0.09
Nodes (9): ApiClient, _detail(), _client(), config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir() (+1 more)

### Community 85 - "Community 85"
Cohesion: 0.13
Nodes (16): _area_entries(), expand_index(), _inside(), _read(), read_repo_docs(), read_text(), decisions_block(), entry() (+8 more)

### Community 86 - "Community 86"
Cohesion: 0.13
Nodes (19): COALESCE_MS, EventSource, lastSeq, Probe(), subscribe, useProjectEvents(), ProjectSummary, loadSpec() (+11 more)

### Community 87 - "Community 87"
Cohesion: 0.12
Nodes (10): _authenticate(), _convert(), _Envelopes, events(), EventStreams, _send(), _stream(), listener() (+2 more)

### Community 88 - "Community 88"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 89 - "Community 89"
Cohesion: 0.18
Nodes (13): createItem(), getItem(), listItems(), Item, NewItem, ItemList(), CreateItemForm(), submit() (+5 more)

### Community 90 - "Community 90"
Cohesion: 0.15
Nodes (16): denials_except(), home_denials(), test_read_only_policy_has_no_commands(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket() (+8 more)

### Community 92 - "Community 92"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 93 - "Community 93"
Cohesion: 0.17
Nodes (19): gates(), test_all_passing(), test_an_unset_command_is_skipped_and_the_run_still_passes(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+11 more)

### Community 94 - "Community 94"
Cohesion: 0.10
Nodes (8): code(), fenced(), _PromptLoader, PromptTemplate, render_template(), _template_line(), example(), test_task_md_example_project_yaml_validates()

### Community 95 - "Community 95"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 96 - "Community 96"
Cohesion: 0.11
Nodes (21): engines, node, name, packageManager, private, type, version, eslint (+13 more)

### Community 97 - "Community 97"
Cohesion: 0.22
Nodes (17): done(), feed(), item(), test_a_blocked_network_call_is_a_denial(), test_a_completed_turn_wins_over_earlier_errors(), test_a_failed_patch_changes_nothing(), test_a_failing_command_is_not_a_denial(), test_a_read_only_run_that_changes_files_is_a_policy_violation() (+9 more)

### Community 98 - "Community 98"
Cohesion: 0.09
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 99 - "Community 99"
Cohesion: 0.24
Nodes (21): parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason() (+13 more)

### Community 100 - "Community 100"
Cohesion: 0.25
Nodes (15): check(), refused(), request(), test_a_duplicate_name_is_refused(), test_a_good_name_passes(), test_a_new_repo_needs_a_new_or_empty_folder(), test_a_symlinked_target_is_refused(), test_a_template_only_for_a_template_source() (+7 more)

### Community 101 - "Community 101"
Cohesion: 0.14
Nodes (10): check_secret_route(), delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretTest, SecretValue (+2 more)

### Community 102 - "Community 102"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 103 - "Community 103"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 104 - "Community 104"
Cohesion: 0.12
Nodes (9): github_token(), store_github_token(), MemoryKeyring, stored_key(), test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins() (+1 more)

### Community 105 - "Community 105"
Cohesion: 0.26
Nodes (15): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_attempt_artifacts(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_history_pages_are_stable_under_inserts() (+7 more)

### Community 106 - "Community 106"
Cohesion: 0.25
Nodes (15): auth(), error(), etag(), test_an_invalid_project_yaml_is_listed_with_its_first_problem(), test_list_and_get_projects(), test_project_detail_says_why_nothing_can_run(), test_settings_edit_with_etags(), test_spec_edit_with_etags() (+7 more)

### Community 107 - "Community 107"
Cohesion: 0.13
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 108 - "Community 108"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 110 - "Community 110"
Cohesion: 0.18
Nodes (12): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_a_huge_body_is_capped(), test_md_escape() (+4 more)

### Community 111 - "Community 111"
Cohesion: 0.14
Nodes (16): state_db_path(), state_dir(), raw(), test_closed_log_refuses_calls(), test_daemon_instance_must_not_be_empty(), test_fresh_database_has_version_7_and_all_tables(), test_naive_clock_raises(), test_newer_schema_is_refused() (+8 more)

### Community 112 - "Community 112"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 113 - "Community 113"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 114 - "Community 114"
Cohesion: 0.19
Nodes (15): is_git_url(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder(), test_a_local_git_repository_at_a_ref() (+7 more)

### Community 115 - "Community 115"
Cohesion: 0.13
Nodes (10): allowed_env(), find_command(), _kill_tree(), probe(), run(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start() (+2 more)

### Community 116 - "Community 116"
Cohesion: 0.10
Nodes (19): description, engines, node, license, name, packageManager, private, type (+11 more)

### Community 117 - "Community 117"
Cohesion: 0.18
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 118 - "Community 118"
Cohesion: 0.15
Nodes (11): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+3 more)

### Community 119 - "Community 119"
Cohesion: 0.21
Nodes (14): test_a_git_template_check_runs_no_global_git_hooks(), test_init_an_empty_repo_on_a_branch(), test_init_an_existing_repo_then_validate(), test_init_existing_folder(), test_init_from_a_git_template_at_a_ref(), test_init_from_a_local_folder_template(), test_init_from_a_template_fills_its_commands(), test_init_refuses_a_bad_branch_name() (+6 more)

### Community 120 - "Community 120"
Cohesion: 0.15
Nodes (5): _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 121 - "Community 121"
Cohesion: 0.12
Nodes (6): dotted_path(), _message(), _model_at(), _number(), split_error(), test_split_error()

### Community 122 - "Community 122"
Cohesion: 0.12
Nodes (6): test_health(), Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token(), test_list_templates(), test_list_templates_needs_the_token()

### Community 123 - "Community 123"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 124 - "Community 124"
Cohesion: 0.22
Nodes (10): auth(), etag(), fixture_tickets(), test_conflicting_edit(), test_get_then_put_unchanged_is_byte_identical(), test_list_with_filters(), test_status_changes_follow_the_transition_table(), test_ticket_ids_are_checked_in_the_path() (+2 more)

### Community 125 - "Community 125"
Cohesion: 0.21
Nodes (7): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), _validation_error()

### Community 126 - "Community 126"
Cohesion: 0.25
Nodes (9): generate(), test_a_copier_failure_is_reported(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_template_without_a_test_command_is_rejected(), test_an_empty_existing_folder_is_used(), test_tasks_from_an_include_are_refused_by_copier_and_never_run(), test_the_users_copier_trust_list_is_ignored() (+1 more)

### Community 127 - "Community 127"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 128 - "Community 128"
Cohesion: 0.16
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 129 - "Community 129"
Cohesion: 0.20
Nodes (7): ApiError, cancel_job(), get_job(), _jobs(), JobView, RollbackView, StepView

### Community 130 - "Community 130"
Cohesion: 0.16
Nodes (9): escape_closing_tag(), _kept(), esc(), render_planner_prompt(), test_escaping_is_case_insensitive_and_spacing_tolerant(), assert_snapshot(), test_a_project_can_override_the_prompt(), test_template_syntax_and_closing_tags_in_the_spec_are_plain_text() (+1 more)

### Community 131 - "Community 131"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 132 - "Community 132"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 133 - "Community 133"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 134 - "Community 134"
Cohesion: 0.23
Nodes (9): GateResult, GateStatus, clean(), _not_run(), _run_gate(), run_gates(), try_command(), test_clean_strips_ansi_and_crlf() (+1 more)

### Community 136 - "Community 136"
Cohesion: 0.20
Nodes (8): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements(), _user_version(), test_timestamps_are_utc_with_milliseconds()

### Community 137 - "Community 137"
Cohesion: 0.12
Nodes (17): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+9 more)

### Community 138 - "Community 138"
Cohesion: 0.19
Nodes (4): get_engine(), get_session(), make_engine(), test_migrations_create_and_drop_the_schema()

### Community 139 - "Community 139"
Cohesion: 0.24
Nodes (7): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from(), test_testing_a_secret_needs_the_token_and_a_known_name(), test_testing_a_secret_never_returns_or_logs_it()

### Community 140 - "Community 140"
Cohesion: 0.12
Nodes (4): sync_command(), validate_project(), describe(), review_command()

### Community 141 - "Community 141"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 142 - "Community 142"
Cohesion: 0.22
Nodes (12): AttemptFinishedData, AttemptStartedData, AuthMessage, _Data, EventEnvelope, IntegrateData, LogData, PolicyDecisionData (+4 more)

### Community 143 - "Community 143"
Cohesion: 0.22
Nodes (6): generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 144 - "Community 144"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 145 - "Community 145"
Cohesion: 0.16
Nodes (9): check_gate_command(), gate_env(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused() (+1 more)

### Community 146 - "Community 146"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 147 - "Community 147"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 148 - "Community 148"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 149 - "Community 149"
Cohesion: 0.21
Nodes (5): ChangedFile, parse_numstat(), staged_changes(), test_parse_numstat_with_a_rename_and_a_binary(), test_staged_changes_names_both_sides_of_a_rename()

### Community 150 - "Community 150"
Cohesion: 0.27
Nodes (7): auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template()

### Community 151 - "Community 151"
Cohesion: 0.30
Nodes (6): approve_plan(), generate_plan(), _plans(), GeneratePlan, PlanApproved, PlanStarted

### Community 152 - "Community 152"
Cohesion: 0.22
Nodes (5): create_app(), client(), test_session(), engine(), session()

### Community 153 - "Community 153"
Cohesion: 0.30
Nodes (10): make_plan(), test_a_failed_write_leaves_the_old_files(), test_a_title_that_needs_quotes_stays_valid_yaml(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members() (+2 more)

### Community 154 - "Community 154"
Cohesion: 0.27
Nodes (8): apply_transition(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 155 - "Community 155"
Cohesion: 0.31
Nodes (5): Base, Item, create_item(), get_item(), list_items()

### Community 156 - "Community 156"
Cohesion: 0.27
Nodes (7): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd()

### Community 157 - "Community 157"
Cohesion: 0.26
Nodes (10): base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning(), test_spec_ties_keep_document_order(), test_spec_without_sections_or_room_for_the_outline_keeps_its_beginning() (+2 more)

### Community 158 - "Community 158"
Cohesion: 0.24
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 159 - "Community 159"
Cohesion: 0.38
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 160 - "Community 160"
Cohesion: 0.32
Nodes (4): agents(), AgentsView, BackendView, GraphifyView

### Community 161 - "Community 161"
Cohesion: 0.21
Nodes (4): DoneWhenCheck, GateFailureData, GateRun, check_done_when()

### Community 162 - "Community 162"
Cohesion: 0.24
Nodes (9): test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file(), test_token_budget() (+1 more)

### Community 163 - "Community 163"
Cohesion: 0.29
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 164 - "Community 164"
Cohesion: 0.22
Nodes (5): delete_secret(), secret_status(), SecretStatus, test_empty_values_and_an_unreadable_keychain(), test_environment_wins_over_the_keychain()

### Community 165 - "Community 165"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 167 - "Community 167"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 168 - "Community 168"
Cohesion: 0.25
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 170 - "Community 170"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 171 - "Community 171"
Cohesion: 0.33
Nodes (4): ReasonButton(), describe(), StatusPill(), TopBar()

### Community 173 - "Community 173"
Cohesion: 0.22
Nodes (5): _clean_line(), commit_message(), test_control_characters_are_removed(), test_progress_note_is_wrapped_at_72(), test_untrusted_title_becomes_one_line_of_at_most_72()

### Community 174 - "Community 174"
Cohesion: 0.36
Nodes (5): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_startup_recovers_and_skips_a_corrupt_database()

### Community 175 - "Community 175"
Cohesion: 0.25
Nodes (3): assert_gone(), Recorder, test_cancel()

### Community 176 - "Community 176"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 177 - "Community 177"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 179 - "Community 179"
Cohesion: 0.39
Nodes (4): pre_tool_use(), policy(), user_home(), worktree()

### Community 181 - "Community 181"
Cohesion: 0.32
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 182 - "Community 182"
Cohesion: 0.25
Nodes (4): builtin_fixture(), fixture_contract(), make_git_template(), make_template()

### Community 183 - "Community 183"
Cohesion: 0.46
Nodes (5): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 186 - "Community 186"
Cohesion: 0.29
Nodes (4): run_log(), test_committed_events_are_published_in_order(), test_concurrent_appends_get_increasing_ids(), test_failed_insert_publishes_nothing()

### Community 188 - "Community 188"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 190 - "Community 190"
Cohesion: 0.53
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 191 - "Community 191"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 201 - "Community 201"
Cohesion: 0.67
Nodes (3): dependencies, react, react-dom

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `@fontsource/inter`, `@fontsource/jetbrains-mono`, `openapi-typescript` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2207 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **166 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 15` to `Community 3`, `Community 8`, `Community 16`, `Community 17`, `Community 19`, `Community 147`, `Community 21`, `Community 23`, `Community 35`, `Community 36`, `Community 38`, `Community 42`, `Community 174`, `Community 68`, `Community 75`, `Community 79`, `Community 81`, `Community 87`, `Community 105`, `Community 109`, `Community 111`, `Community 118`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `RunLog` (e.g. with `page_runs()` and `recover_interrupted()`) actually correct?**
  _`RunLog` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `@fontsource/inter` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.035306334371754934 - nodes in this community are weakly interconnected._
- **Why does `load_project()` connect `Community 24` to `Community 0`, `Community 8`, `Community 140`, `Community 12`, `Community 143`, `Community 17`, `Community 19`, `Community 21`, `Community 23`, `Community 26`, `Community 159`, `Community 34`, `Community 35`, `Community 36`, `Community 39`, `Community 43`, `Community 49`, `Community 50`, `Community 51`, `Community 54`, `Community 184`, `Community 57`, `Community 185`, `Community 64`, `Community 65`, `Community 68`, `Community 73`, `Community 79`, `Community 106`, `Community 109`, `Community 117`, `Community 119`, `Community 127`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 66 inferred relationships involving `load_project()` (e.g. with `_load()` and `_settings_data()`) actually correct?**
  _`load_project()` has 66 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.04079065588499551 - nodes in this community are weakly interconnected._