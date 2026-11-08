# Graph Report - Project_Manager  (2026-11-08)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 7198 nodes · 20869 edges · 346 communities (194 shown, 152 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1752 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ea876427`
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
- Community 206
- Community 209
- Community 335
- Community 336
- Community 337

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 139 edges
2. `load_project()` - 91 edges
3. `RunRegistry` - 86 edges
4. `WorktreeManager` - 80 edges
5. `AgentPolicy` - 80 edges
6. `FakeRunner` - 77 edges
7. `ClaudeStreamParser` - 72 edges
8. `build_implementer_prompt()` - 60 edges
9. `Transcripts` - 59 edges
10. `react` - 59 edges

## Surprising Connections (you probably didn't know these)
- `schema()` --uses--> `Settings`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/core/config.py
- `schema()` --calls--> `create_app()`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/api/app.py
- `unblock()` --calls--> `RunLoopError`  [INFERRED]
  daemon/tests/api/test_tickets.py → daemon/src/spoolhq/services/runloop/model.py
- `test_client_connection_refused()` --calls--> `ApiClient`  [INFERRED]
  daemon/tests/cli/test_main.py → daemon/src/spoolhq/cli/client.py
- `test_codex_not_logged_in_says_codex_login()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runloop/__init__.py -> daemon/src/spoolhq/services/runloop/polling.py -> daemon/src/spoolhq/services/runloop/loop.py -> daemon/src/spoolhq/services/runloop/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
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
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/history.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (346 total, 152 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (51): approval_message(), approve(), decide(), read_artifact(), reject(), unblock(), _user_approved(), _waiting() (+43 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (105): Artifact, DiffFile, DiffReport, GateReport, GatesReport, load(), PATHS, Report (+97 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (34): fill_verdict(), format_version(), parse_version(), existing_stubs(), requested_tools(), with_config_dir(), BackendInfo, Budget (+26 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (63): check_ticket_id(), slugify(), parse_numstat(), staged_changes(), advance(), checked_out(), commit(), conclude_merge() (+55 more)

### Community 4 - "Community 4"
Cohesion: 0.04
Nodes (34): _branch_of(), finish(), _hint(), publish_tag(), recover_integrations(), _result(), _set_run(), tag_name() (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (41): check_git(), keep_for(), decode_cursor(), encode_cursor(), EventPage, page_events(), page_runs(), RunPage (+33 more)

### Community 6 - "Community 6"
Cohesion: 0.02
Nodes (70): COALESCE_MS, EventSource, lastSeq, Probe(), subscribe, useProjectEvents(), Backend, backends (+62 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (41): escape_closing_tag(), clean_title(), InvalidPlan, _not_blank(), one_line(), PlanInvalid, PlannedTicket, PlannerError (+33 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (71): asTyped(), BodyParts, DoneItem, joinBody(), splitBody(), splitDoneWhen(), RuleHit, ruleLabel() (+63 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (57): Agents, useAgents(), checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning (+49 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (28): weighted_tokens(), _blocks(), _int(), keep_end(), line_counts(), _lines(), PolicyViolation, result_text() (+20 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (46): _header(), _path(), _split_files(), trim_diff(), GateLine, ItemVerdict, ReviewResult, _gate_word() (+38 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (49): useRunLimits(), nextAttemptLine(), NOTE_MAX, NoteKind, useSendNote(), NoteDialog(), ReasonButton(), attemptSummary() (+41 more)

### Community 13 - "Community 13"
Cohesion: 0.04
Nodes (19): agents_command(), describe(), describe_roles(), describe_worktrees(), fail(), settings(), _client(), sync_command() (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.05
Nodes (26): write_atomic(), parse_done_when(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError, DoneItem (+18 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (44): ClaudeStreamParser, epoch_to_datetime(), usd_to_micro(), assistant(), load(), parse(), replay(), result() (+36 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (34): id_key(), PlanError, PlanProblem, SchedulerError, TicketEditError, TicketLockedError, TransitionError, _and_list() (+26 more)

### Community 17 - "Community 17"
Cohesion: 0.04
Nodes (10): billing_error(), CliTransport, SdkRun, stop(), RunResult, Session, _signal_group(), _stream() (+2 more)

### Community 18 - "Community 18"
Cohesion: 0.05
Nodes (37): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, BODIES (+29 more)

### Community 19 - "Community 19"
Cohesion: 0.05
Nodes (31): AgentSdkRunner, check_path(), policy_parts(), build_argv(), check_worktree(), child_env(), expand_home(), permission_modes() (+23 more)

### Community 20 - "Community 20"
Cohesion: 0.06
Nodes (44): ProjectDetail, ProjectSummary, useProject(), useProjects(), loadSpec(), saveSpec(), SPEC_FILE, SpecFile (+36 more)

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (56): load_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated(), test_bad_file_name() (+48 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (42): NewProjectButton(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants, Card(), CardAction() (+34 more)

### Community 23 - "Community 23"
Cohesion: 0.07
Nodes (28): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+20 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (42): assert_gone(), endpoint_runner(), fake_probe(), read_record(), Recorder, run(), runner(), test_a_custom_endpoint_never_gets_the_users_login() (+34 more)

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (39): Plan, PlanProblem, problemLabel(), useApprovePlan(), useGeneratePlan(), usePlan(), Ticket, ticketsQuery() (+31 more)

### Community 26 - "Community 26"
Cohesion: 0.06
Nodes (31): allowed_env(), build_argv(), child_env(), install_dir(), permission_profile(), policy_parts(), refusal(), required_parts() (+23 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (20): _recover_one(), RecoveryEntry, WorktreeInfo, _check(), check_secret(), SecretCheck, delete_secret(), _lookup() (+12 more)

### Community 28 - "Community 28"
Cohesion: 0.06
Nodes (35): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+27 more)

### Community 29 - "Community 29"
Cohesion: 0.11
Nodes (49): load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_a_workspace_can_be_written_before_its_repo(), test_all_errors_are_reported_at_once() (+41 more)

### Community 30 - "Community 30"
Cohesion: 0.09
Nodes (25): service_errors(), approve_ticket(), _artifact(), cancel_run(), current_run(), discard_ticket(), get_diff(), get_gates() (+17 more)

### Community 31 - "Community 31"
Cohesion: 0.10
Nodes (43): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), test_negative_cap_is_refused(), test_no_map_no_block() (+35 more)

### Community 32 - "Community 32"
Cohesion: 0.08
Nodes (39): Listener, listeners, openSettings(), SettingsTab, useOpenRequests(), Agents, backendReady(), DaemonSettings (+31 more)

### Community 33 - "Community 33"
Cohesion: 0.11
Nodes (43): git_executable(), WorktreeManager, branches(), make_read_only(), marker(), real(), registered_paths(), sha() (+35 more)

### Community 34 - "Community 34"
Cohesion: 0.08
Nodes (43): apply_transition(), check_transition(), parse_status(), copy_dashboard(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once() (+35 more)

### Community 35 - "Community 35"
Cohesion: 0.07
Nodes (10): _clear_read_only_and_retry(), marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, remove_path(), same_path(), Worktree (+2 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (29): api_key(), no_parent_key(), test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript(), record(), run() (+21 more)

### Community 37 - "Community 37"
Cohesion: 0.08
Nodes (22): check_command(), describe_source(), list_command(), check_template(), CheckResult, load_contract(), TemplateContract, TemplateError (+14 more)

### Community 38 - "Community 38"
Cohesion: 0.07
Nodes (25): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project() (+17 more)

### Community 39 - "Community 39"
Cohesion: 0.19
Nodes (32): LocalIntegrator, Transcripts, git(), hooked(), call(), kinds(), _linking(), local() (+24 more)

### Community 40 - "Community 40"
Cohesion: 0.06
Nodes (41): engines, node, name, packageManager, private, type, version, description (+33 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (29): assert_refused(), read_only(), read_record(), refused_message(), run(), runner(), temps(), test_a_custom_endpoint_never_gets_the_users_login() (+21 more)

### Community 42 - "Community 42"
Cohesion: 0.11
Nodes (24): _conflict(), create_project(), _creating(), get_project(), get_settings(), get_spec(), _left_behind(), list_projects() (+16 more)

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (27): Hooked, crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree(), test_current_lists_the_phase_lines() (+19 more)

### Community 44 - "Community 44"
Cohesion: 0.09
Nodes (27): ChangedFile, as_record(), _compile(), delivery_mode(), describe(), evaluate(), _listed(), path_matches() (+19 more)

### Community 45 - "Community 45"
Cohesion: 0.10
Nodes (15): serve(), load_or_create_token(), read_token(), token_path(), config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path() (+7 more)

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (26): Merging, kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt() (+18 more)

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (20): GitHubPoller, bare(), fake(), FakeGitHub, git(), leaks(), log_of(), start() (+12 more)

### Community 48 - "Community 48"
Cohesion: 0.07
Nodes (15): cap_excerpt(), ContextBudgetError, ContextError, PromptTemplateError, _clean(), code(), fenced(), normalize_newlines() (+7 more)

### Community 49 - "Community 49"
Cohesion: 0.07
Nodes (13): format_errors(), dump(), loader(), merge(), parse(), _message(), parse_contract(), _Strict (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.08
Nodes (8): _Cancelled, _Failed, Job, roll_back(), Rollback, Runner, Step, Checked

### Community 51 - "Community 51"
Cohesion: 0.07
Nodes (12): agents(), sync(), list_templates(), AgentsView, BackendView, GraphifyView, GitHubSync, TemplateCommandsView (+4 more)

### Community 52 - "Community 52"
Cohesion: 0.15
Nodes (26): FakeRunner, ReviewInputs, test_each_review_is_its_own_run(), OutcomeRunner, run(), test_approve(), test_budget_defaults_and_overrides(), run() (+18 more)

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (15): gate_env(), resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when() (+7 more)

### Community 54 - "Community 54"
Cohesion: 0.08
Nodes (17): Agents, BackendSettings, Budget, _check_backend(), _check_base_url(), _check_path_pattern(), Commands, ContextSettings (+9 more)

### Community 55 - "Community 55"
Cohesion: 0.10
Nodes (33): fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes(), test_default_branch_sha(), test_default_branch_sha_outside_a_repo() (+25 more)

### Community 56 - "Community 56"
Cohesion: 0.12
Nodes (19): require_if_match(), run_log(), settings(), workspace(), get_ticket(), get_tickets(), put_ticket(), _read() (+11 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (19): Delivery, ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note() (+11 more)

### Community 58 - "Community 58"
Cohesion: 0.07
Nodes (13): create_app(), lifespan(), _openapi(), health(), Health, recover_all_integrations(), recover_all_worktrees(), RecoveryAction (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.10
Nodes (21): capture(), on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact() (+13 more)

### Community 60 - "Community 60"
Cohesion: 0.08
Nodes (18): set_command(), store_api_key(), available_runners(), backend_names(), make_runner(), endpoint_token(), keyring_key(), missing_token() (+10 more)

### Community 61 - "Community 61"
Cohesion: 0.09
Nodes (15): hours(), approve_command(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner() (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 63 - "Community 63"
Cohesion: 0.12
Nodes (26): _clean_line(), commit_message(), branch(), git_out(), head(), _squash(), _stage_link(), test_advance_fast_forwards_the_checked_out_branch() (+18 more)

### Community 64 - "Community 64"
Cohesion: 0.22
Nodes (22): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+14 more)

### Community 65 - "Community 65"
Cohesion: 0.10
Nodes (24): diff_report(), DiffFile, DiffReport, _file(), GateReport, gates_report(), GatesReport, _header_path() (+16 more)

### Community 66 - "Community 66"
Cohesion: 0.13
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _control(), discard_command() (+7 more)

### Community 67 - "Community 67"
Cohesion: 0.09
Nodes (20): useDismissJob(), useInterruptedRun(), MAX_CARDS, NeedsYouCard, needsYouCards(), NeedsYouKind, sentence(), TicketLike (+12 more)

### Community 68 - "Community 68"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 69 - "Community 69"
Cohesion: 0.12
Nodes (16): GitHubClient, GitHubError, create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull() (+8 more)

### Community 70 - "Community 70"
Cohesion: 0.11
Nodes (18): ProjectError, ProjectValidationError, Project, has_spec(), init_project(), _initial_yaml(), InitResult, parse_project() (+10 more)

### Community 71 - "Community 71"
Cohesion: 0.10
Nodes (17): dumper(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node() (+9 more)

### Community 72 - "Community 72"
Cohesion: 0.12
Nodes (18): AgentRunner, adapter(), AdapterCase, agent_sdk(), claude_cli(), codex_cli(), fake(), run() (+10 more)

### Community 73 - "Community 73"
Cohesion: 0.15
Nodes (21): ConfigError, load_settings(), test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1(), test_config_file_is_read(), test_defaults_without_config_file() (+13 more)

### Community 74 - "Community 74"
Cohesion: 0.10
Nodes (21): keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total() (+13 more)

### Community 75 - "Community 75"
Cohesion: 0.16
Nodes (18): close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(), stuck() (+10 more)

### Community 76 - "Community 76"
Cohesion: 0.12
Nodes (25): config_without_port_uses_the_default(), current_home(), DAEMON_HOST, daemon_info(), DaemonInfo, DEFAULT_PORT, empty_spoolhq_home_falls_back_to_the_default_folder(), env_port_wins_over_config_toml() (+17 more)

### Community 77 - "Community 77"
Cohesion: 0.11
Nodes (18): _assistant(), clock(), FakeGates, _init(), make_loop(), make(), project(), registry() (+10 more)

### Community 78 - "Community 78"
Cohesion: 0.12
Nodes (27): test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_cache_reads_count_a_tenth_toward_weighted_tokens(), test_empty_folder_left_by_an_uncommitted_attempt_is_reused(), test_ended_run_takes_no_attempts(), test_event_with_an_attempt_of_another_run_is_refused() (+19 more)

### Community 79 - "Community 79"
Cohesion: 0.13
Nodes (16): _area_entries(), expand_index(), _inside(), _read(), read_repo_docs(), read_text(), decisions_block(), entry() (+8 more)

### Community 80 - "Community 80"
Cohesion: 0.21
Nodes (19): cache_dir(), refresh(), FakeGraphify, builds(), pointer(), source(), test_a_busy_cache_gives_no_map(), test_a_cache_from_another_version_is_discarded() (+11 more)

### Community 81 - "Community 81"
Cohesion: 0.11
Nodes (11): _authenticate(), _convert(), _Envelopes, events(), EventStreams, _send(), _stream(), listener() (+3 more)

### Community 82 - "Community 82"
Cohesion: 0.11
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 83 - "Community 83"
Cohesion: 0.18
Nodes (18): create(), git_state(), jobs_for(), snapshot(), source_fields(), states(), test_a_commit_without_an_identity_fails_and_rolls_back(), test_a_failing_test_command_names_its_field() (+10 more)

### Community 84 - "Community 84"
Cohesion: 0.19
Nodes (17): auth(), _ended(), finished(), post(), refused(), test_a_failing_test_command_and_its_rollback(), test_a_project_being_created_is_reported_as_creating(), test_a_read_only_path_the_rollback_cant_delete_is_listed() (+9 more)

### Community 85 - "Community 85"
Cohesion: 0.17
Nodes (20): auth(), edit(), etag(), fixture_tickets(), test_a_title_edit_changes_only_the_title_line(), test_an_edit_that_breaks_the_plan_is_422_with_the_field(), test_an_edit_while_running_is_409(), test_conflicting_edit() (+12 more)

### Community 86 - "Community 86"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 87 - "Community 87"
Cohesion: 0.12
Nodes (23): AgentDeniedData, AgentFileEditData, AgentMessageData, AgentRateLimitData, AgentToolCallData, AgentToolResultData, AgentUsageData, AgentWarningData (+15 more)

### Community 88 - "Community 88"
Cohesion: 0.14
Nodes (14): init(), _check_branch(), _check_existing(), _check_new(), check_request(), _commands(), CreateProject, CreationError (+6 more)

### Community 89 - "Community 89"
Cohesion: 0.14
Nodes (17): check_command(), denials_except(), home_denials(), PolicyError, test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused() (+9 more)

### Community 90 - "Community 90"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 91 - "Community 91"
Cohesion: 0.15
Nodes (15): AgentPolicy, test_policy_fields_are_untouched_by_credentials_list(), test_unusable_backend_raises_before_starting(), test_a_cancel_during_the_delay_stops_the_run(), test_a_sequence_replays_one_transcript_per_run(), test_a_write_outside_the_worktree_is_refused_as_a_policy_error(), test_cancel(), test_cycle_starts_the_sequence_again() (+7 more)

### Community 92 - "Community 92"
Cohesion: 0.10
Nodes (5): billing_for(), ClaudeCliRunner, platform_reason(), probe(), test_real_run_creates_a_file_and_is_denied_python()

### Community 93 - "Community 93"
Cohesion: 0.11
Nodes (7): version(), Version, _is_api_path(), LocalOnlyMiddleware, _read_body(), _replay(), replay()

### Community 94 - "Community 94"
Cohesion: 0.10
Nodes (5): billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), test_real_codex_run_creates_a_file_and_cannot_read_ssh()

### Community 95 - "Community 95"
Cohesion: 0.13
Nodes (11): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, holder(), lock_path(), LockHeld, _read_pid(), _try_lock() (+3 more)

### Community 96 - "Community 96"
Cohesion: 0.12
Nodes (18): build_excerpt(), take(), clean(), _clip(), failing_tests(), first_failure(), _priority(), split_lines() (+10 more)

### Community 97 - "Community 97"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 98 - "Community 98"
Cohesion: 0.17
Nodes (19): gates(), test_all_passing(), test_an_unset_command_is_skipped_and_the_run_still_passes(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+11 more)

### Community 99 - "Community 99"
Cohesion: 0.15
Nodes (14): _check_decisions(), _decisions(), folders(), _script(), test_a_consistent_fixture_passes(), test_a_duplicated_number_fails(), test_a_mismatched_title_fails(), test_a_missing_number_fails() (+6 more)

### Community 100 - "Community 100"
Cohesion: 0.15
Nodes (13): describe_graphify(), _build(), CodeMap, _current(), _drop(), _refresh(), _remove_unused(), _save() (+5 more)

### Community 101 - "Community 101"
Cohesion: 0.15
Nodes (13): check_command(), check_tool(), relative_pattern(), call_hook(), test_reviewer_and_planner_get_no_write_or_bash(), test_the_hook_allows_allowlisted_commands(), test_the_hook_answers_the_sdk(), test_the_hook_confines_file_tools() (+5 more)

### Community 102 - "Community 102"
Cohesion: 0.10
Nodes (15): fake_backend(), fake_graphify(), free_port(), git_identity(), isolated_git(), keychain(), no_graphify(), plan_project() (+7 more)

### Community 103 - "Community 103"
Cohesion: 0.22
Nodes (17): done(), feed(), item(), test_a_blocked_network_call_is_a_denial(), test_a_completed_turn_wins_over_earlier_errors(), test_a_failed_patch_changes_nothing(), test_a_failing_command_is_not_a_denial(), test_a_read_only_run_that_changes_files_is_a_policy_violation() (+9 more)

### Community 104 - "Community 104"
Cohesion: 0.24
Nodes (16): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_attempt_artifacts(), test_attempt_reports(), test_current_with_no_run(), test_every_run_route_needs_the_token() (+8 more)

### Community 105 - "Community 105"
Cohesion: 0.09
Nodes (5): PORT_ENV_VAR, Backoff, BACKOFF, FAST, WAIT

### Community 106 - "Community 106"
Cohesion: 0.10
Nodes (7): _pr_state(), ticket_runs(), TicketGit, TicketRuns, retries_used(), _Job, PlanJobs

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
Nodes (16): state_db_path(), state_dir(), raw(), test_closed_log_refuses_calls(), test_daemon_instance_must_not_be_empty(), test_fresh_database_has_version_7_and_all_tables(), test_naive_clock_raises(), test_newer_schema_is_refused() (+8 more)

### Community 111 - "Community 111"
Cohesion: 0.15
Nodes (9): ApiError, problem_view(), cancel_job(), dismiss_job(), get_job(), _jobs(), JobView, RollbackView (+1 more)

### Community 112 - "Community 112"
Cohesion: 0.12
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 113 - "Community 113"
Cohesion: 0.13
Nodes (9): table(), _cost(), list_command(), _policy(), _run_log(), show_command(), _tokens(), _workspace() (+1 more)

### Community 115 - "Community 115"
Cohesion: 0.13
Nodes (9): make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_serve_refuses_while_another_daemon_holds_the_lock(), test_startup_recovers_and_skips_a_corrupt_database(), test_startup_without_a_projects_folder_serves(), test_bus_of_an_empty_database_starts_at_zero() (+1 more)

### Community 116 - "Community 116"
Cohesion: 0.12
Nodes (9): github_token(), store_github_token(), MemoryKeyring, stored_key(), test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins() (+1 more)

### Community 117 - "Community 117"
Cohesion: 0.25
Nodes (15): auth(), error(), etag(), test_an_invalid_project_yaml_is_listed_with_its_first_problem(), test_list_and_get_projects(), test_project_detail_says_why_nothing_can_run(), test_settings_edit_with_etags(), test_spec_edit_with_etags() (+7 more)

### Community 118 - "Community 118"
Cohesion: 0.14
Nodes (11): check_secret_route(), delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretTest, SecretValue (+3 more)

### Community 119 - "Community 119"
Cohesion: 0.15
Nodes (11): dev_agents(), runner(), auth(), _check_reports(), dev_client(), make(), run_next(), test_a_scenario_writing_outside_the_worktree_blocks() (+3 more)

### Community 120 - "Community 120"
Cohesion: 0.25
Nodes (15): auth(), get_plan(), plan_client(), test_a_clean_approve_makes_the_drafts_ready(), test_an_invalid_ticket_file_is_a_problem(), test_approve_with_problems_is_409_and_changes_nothing(), test_each_problem_has_its_code_and_ticket_ids(), test_every_plan_route_needs_the_token() (+7 more)

### Community 121 - "Community 121"
Cohesion: 0.18
Nodes (16): is_git_url(), _is_path(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder() (+8 more)

### Community 122 - "Community 122"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 123 - "Community 123"
Cohesion: 0.18
Nodes (12): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_a_huge_body_is_capped(), test_md_escape() (+4 more)

### Community 124 - "Community 124"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 125 - "Community 125"
Cohesion: 0.10
Nodes (15): NAME_RULE, CREATED_TOAST, GET, Handler, Job, JOB_ID, NAMES, openDialog() (+7 more)

### Community 126 - "Community 126"
Cohesion: 0.18
Nodes (16): a_4401_close_stops_for_good(), a_dropped_connection_reconnects(), accept(), close_with(), Harness, next_text(), received(), reconnect_resends_since_the_last_seq_after_4408() (+8 more)

### Community 127 - "Community 127"
Cohesion: 0.20
Nodes (11): ContextInputs, DependencyView, GateFailure, PreviousAttempt, RenderedPrompt, ReviewNote, TicketView, code_map() (+3 more)

### Community 129 - "Community 129"
Cohesion: 0.21
Nodes (12): test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install() (+4 more)

### Community 130 - "Community 130"
Cohesion: 0.18
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 131 - "Community 131"
Cohesion: 0.21
Nodes (14): test_a_git_template_check_runs_no_global_git_hooks(), test_init_an_empty_repo_on_a_branch(), test_init_an_existing_repo_then_validate(), test_init_existing_folder(), test_init_from_a_git_template_at_a_ref(), test_init_from_a_local_folder_template(), test_init_from_a_template_fills_its_commands(), test_init_refuses_a_bad_branch_name() (+6 more)

### Community 132 - "Community 132"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 133 - "Community 133"
Cohesion: 0.12
Nodes (6): dotted_path(), _message(), _model_at(), _number(), split_error(), test_split_error()

### Community 134 - "Community 134"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 135 - "Community 135"
Cohesion: 0.18
Nodes (6): codex_review(), set_roles(), test_a_ticket_runs_end_to_end_on_codex(), codex(), test_a_ticket_runs_end_to_end_on_the_agent_sdk(), test_each_role_starts_its_own_backend()

### Community 137 - "Community 137"
Cohesion: 0.16
Nodes (5): _deps(), edit_command(), list_command(), set_status_command(), show_command()

### Community 138 - "Community 138"
Cohesion: 0.22
Nodes (9): _crashed_journal(), git(), held(), recover(), restart(), test_a_main_checkout_mid_merge_is_skipped(), test_crash_after_each_journal_state(), test_dirty_checkout_after_a_cut_off_fast_forward_is_left_alone() (+1 more)

### Community 139 - "Community 139"
Cohesion: 0.25
Nodes (9): generate(), test_a_copier_failure_is_reported(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_template_without_a_test_command_is_rejected(), test_an_empty_existing_folder_is_used(), test_tasks_from_an_include_are_refused_by_copier_and_never_run(), test_the_users_copier_trust_list_is_ignored() (+1 more)

### Community 140 - "Community 140"
Cohesion: 0.18
Nodes (10): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+2 more)

### Community 141 - "Community 141"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 142 - "Community 142"
Cohesion: 0.25
Nodes (9): approve_plan(), generate_plan(), get_plan(), _plans(), GeneratePlan, PlanApproved, PlanProblemView, PlanStarted (+1 more)

### Community 143 - "Community 143"
Cohesion: 0.16
Nodes (4): ApiClient, ApiError, DaemonNotRunning, _detail()

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
Cohesion: 0.26
Nodes (9): RunRegistry, jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs(), test_errors_before_the_agent_come_back_at_once(), test_one_plan_per_project_at_a_time() (+1 more)

### Community 149 - "Community 149"
Cohesion: 0.19
Nodes (8): AttemptView, CurrentRun, Discarded, MergedView, PhaseLine, PolicyView, Reject, RuleHitView

### Community 150 - "Community 150"
Cohesion: 0.21
Nodes (12): _api_routes(), test_bodies_over_1_mb_are_refused(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token() (+4 more)

### Community 151 - "Community 151"
Cohesion: 0.15
Nodes (8): test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_logs_the_fake_runner_and_passes_its_agents(), test_serve_refuses_non_loopback_host(), test_serve_refuses_the_fake_runner_frozen_or_unknown(), test_version_with_bad_config_fails_readably(), test_version_without_daemon()

### Community 152 - "Community 152"
Cohesion: 0.15
Nodes (6): summary(), find_command(), probe(), test_find_command_uses_path(), test_a_report_without_known_sections_is_empty(), test_keeps_the_map_and_drops_the_rest()

### Community 153 - "Community 153"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 154 - "Community 154"
Cohesion: 0.18
Nodes (7): api_url(), check_project(), daemon_target(), events_subscribe(), events_unsubscribe(), Streams, Target

### Community 155 - "Community 155"
Cohesion: 0.27
Nodes (7): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), _validation_error()

### Community 156 - "Community 156"
Cohesion: 0.24
Nodes (9): recover_worktrees(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+1 more)

### Community 157 - "Community 157"
Cohesion: 0.22
Nodes (8): EditConflict, etag_of(), _lock(), read_with_etag(), write_if_match(), test_concurrent_edits_with_the_same_etag_let_one_win(), edit(), test_write_only_when_the_etag_matches()

### Community 158 - "Community 158"
Cohesion: 0.18
Nodes (5): get_settings(), Settings, url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 159 - "Community 159"
Cohesion: 0.22
Nodes (7): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from(), test_testing_a_secret_needs_the_token_and_a_known_name(), test_testing_a_secret_never_returns_or_logs_it()

### Community 160 - "Community 160"
Cohesion: 0.22
Nodes (6): generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 161 - "Community 161"
Cohesion: 0.21
Nodes (11): api_method(), daemon_get(), daemon_request(), DaemonError, Config, InvalidRequest, NotRunning, TokenMissing (+3 more)

### Community 162 - "Community 162"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 163 - "Community 163"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 164 - "Community 164"
Cohesion: 0.27
Nodes (10): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning() (+2 more)

### Community 165 - "Community 165"
Cohesion: 0.21
Nodes (5): _generated_at(), plan_overview(), PlanOverview, _invalid_problem(), plan_problems()

### Community 166 - "Community 166"
Cohesion: 0.30
Nodes (10): make_plan(), test_a_failed_write_leaves_the_old_files(), test_a_title_that_needs_quotes_stays_valid_yaml(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members() (+2 more)

### Community 167 - "Community 167"
Cohesion: 0.15
Nodes (3): describe(), print_run(), run_command()

### Community 169 - "Community 169"
Cohesion: 0.24
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 170 - "Community 170"
Cohesion: 0.23
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 171 - "Community 171"
Cohesion: 0.38
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 172 - "Community 172"
Cohesion: 0.20
Nodes (7): check_gate_command(), split_command(), _check_command(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused(), test_unclosed_quote_is_refused()

### Community 173 - "Community 173"
Cohesion: 0.26
Nodes (5): Base, client(), test_session(), engine(), session()

### Community 174 - "Community 174"
Cohesion: 0.44
Nodes (7): auth(), _get(), _log(), test_1200_events_come_in_pages_of_500_500_and_200(), test_a_limit_over_2000_is_refused(), test_attempt_n_gives_its_window_with_the_run_level_events(), test_unknown_run_or_attempt_is_404()

### Community 176 - "Community 176"
Cohesion: 0.27
Nodes (3): get_engine(), get_session(), make_engine()

### Community 177 - "Community 177"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 178 - "Community 178"
Cohesion: 0.27
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 179 - "Community 179"
Cohesion: 0.24
Nodes (4): Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token(), test_agents_reports_the_fake_runner()

### Community 180 - "Community 180"
Cohesion: 0.38
Nodes (7): ask_hook(), main(), parse(), receive(), run(), send(), write_file()

### Community 182 - "Community 182"
Cohesion: 0.20
Nodes (3): make_hook(), pre_tool_use(), home()

### Community 183 - "Community 183"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 184 - "Community 184"
Cohesion: 0.44
Nodes (4): Item, create_item(), get_item(), list_items()

### Community 185 - "Community 185"
Cohesion: 0.22
Nodes (3): test_health(), test_list_templates(), test_list_templates_needs_the_token()

### Community 186 - "Community 186"
Cohesion: 0.31
Nodes (4): App(), root, HomePage(), react-dom

### Community 188 - "Community 188"
Cohesion: 0.27
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 189 - "Community 189"
Cohesion: 0.27
Nodes (5): run_ticket(), setup(), test_hello_with_and_without_the_code_map(), model_calls(), test_real_run_implements_and_approves_a_tiny_ticket()

### Community 191 - "Community 191"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 192 - "Community 192"
Cohesion: 0.33
Nodes (6): connect_once(), End, Final, Retry, Stopped, run_stream()

### Community 196 - "Community 196"
Cohesion: 0.32
Nodes (3): @tailwindcss/vite, vite, @vitejs/plugin-react

### Community 197 - "Community 197"
Cohesion: 0.46
Nodes (5): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 198 - "Community 198"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 199 - "Community 199"
Cohesion: 0.29
Nodes (4): run_log(), test_committed_events_are_published_in_order(), test_concurrent_appends_get_increasing_ids(), test_failed_insert_publishes_nothing()

### Community 200 - "Community 200"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 202 - "Community 202"
Cohesion: 0.53
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 203 - "Community 203"
Cohesion: 0.40
Nodes (4): Markdown(), PLUGINS, react-markdown, remark-gfm

### Community 204 - "Community 204"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 209 - "Community 209"
Cohesion: 0.67
Nodes (3): dependencies, react, react-dom

## Knowledge Gaps
- **18 isolated node(s):** `Event`, `Stopped`, `Config`, `InvalidRequest`, `NotRunning` (+13 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 2360 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **152 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 4` to `Community 0`, `Community 5`, `Community 10`, `Community 148`, `Community 162`, `Community 38`, `Community 39`, `Community 174`, `Community 47`, `Community 56`, `Community 57`, `Community 59`, `Community 69`, `Community 75`, `Community 77`, `Community 81`, `Community 82`, `Community 85`, `Community 104`, `Community 106`, `Community 107`, `Community 110`, `Community 113`, `Community 115`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `RunLog` (e.g. with `recover_interrupted()` and `RunRegistry`) actually correct?**
  _`RunLog` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Event`, `Stopped`, `Config` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.03407716090872429 - nodes in this community are weakly interconnected._
- **Why does `WorktreeManager` connect `Community 33` to `Community 0`, `Community 3`, `Community 35`, `Community 5`, `Community 4`, `Community 38`, `Community 134`, `Community 73`, `Community 13`, `Community 58`, `Community 27`, `Community 156`, `Community 63`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 72 inferred relationships involving `load_project()` (e.g. with `_load()` and `_settings_data()`) actually correct?**
  _`load_project()` has 72 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.034826773081806636 - nodes in this community are weakly interconnected._