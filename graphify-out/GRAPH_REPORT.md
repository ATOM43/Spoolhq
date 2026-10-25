# Graph Report - Project_Manager  (2026-10-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 4589 nodes · 12787 edges · 274 communities (146 shown, 128 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1069 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `12050abc`
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
- Community 160
- Community 164
- Community 253
- Community 254
- Community 255

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 97 edges
2. `WorktreeManager` - 81 edges
3. `run_git()` - 73 edges
4. `ClaudeStreamParser` - 69 edges
5. `AgentPolicy` - 63 edges
6. `load_project()` - 58 edges
7. `FakeRunner` - 56 edges
8. `Transcripts` - 51 edges
9. `build_implementer_prompt()` - 48 edges
10. `run_git()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `broken()` --calls--> `GitError`  [INFERRED]
  daemon/tests/services/runloop/test_integration.py → daemon/src/spoolhq/services/git/runner.py
- `test_error_without_stderr_has_no_colon()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_git_error_keeps_the_last_20_stderr_lines()` --calls--> `GitResult`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/pulls.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/journal.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 5-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/rows.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (274 total, 128 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (58): weighted_tokens(), _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), keep_end(), summarize(), _usage_counts() (+50 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (37): id_key(), slugify(), clean_title(), InvalidPlan, _not_blank(), one_line(), PlannedTicket, PlannerError (+29 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (59): parse_plan(), _where(), copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only() (+51 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (32): check_ticket_id(), branch_name(), _recover_one(), recover_worktrees(), RecoveryEntry, default_branch_sha(), DirtyRepoError, ensure_clean() (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (18): fail(), settings(), table(), _client(), _cost(), list_command(), _run_log(), show_command() (+10 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (37): advance(), checked_out(), _clean_line(), commit(), commit_message(), conclude_merge(), conflict_files(), create_tag() (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (27): sync(), approve_plan(), generate_plan(), _plans(), cancel_run(), current_run(), discard_ticket(), errors() (+19 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (20): agents_command(), describe(), available_runners(), billing_for(), ClaudeCliRunner, format_version(), parse_version(), permission_modes() (+12 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (7): RunLoop, NotFoundError, record_phase(), RunLoopError, user_errors(), AttemptKind, test_next_kind()

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (19): default_agents(), check_git(), HoldForIntegration, IntegrationResult, IntegrationStatus, Integrator, active_message(), take_run_lock() (+11 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (40): AgentPolicy, assert_gone(), fake_probe(), read_record(), Recorder, run(), runner(), test_api_key_billing_passes_the_key_and_the_budget() (+32 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (55): load_ticket(), errors_for(), make_project(), replace_line(), save_and_read(), test_assignment_is_validated(), test_bad_file_name(), test_bad_project_name() (+47 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (16): AttemptStatus, Event, EventKind, RunKind, RunStatus, Usage, open_pull_requests(), set_pull_request() (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (20): approve_plan(), write_atomic(), run_editor(), start_edit(), TicketEdit, source_name(), TicketError, TicketValidationError (+12 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (34): FakeRunner, ReviewInputs, test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file() (+26 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (44): dependencies, react, react-dom, engines, node, name, packageManager, private (+36 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (43): WorktreeManager, branches(), make_read_only(), marker(), real(), registered_paths(), sha(), test_commit_all_commits_on_top_of_the_base() (+35 more)

### Community 17 - "Community 17"
Cohesion: 0.09
Nodes (18): last_merged(), publish_tag(), _result(), tag_name(), waiting_message(), _get(), get_integration(), Integration (+10 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (5): attempt_dir_name(), _check_count(), RunLog, Attempt, Run

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (13): _assistant(), clock(), gate_result(), _init(), make_loop(), make(), ManualClock, Merging (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (37): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text(), big_docs() (+29 more)

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (42): load_project(), test_integrate_merges_a_held_ticket(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_all_errors_are_reported_at_once() (+34 more)

### Community 23 - "Community 23"
Cohesion: 0.18
Nodes (28): LocalIntegrator, RunRegistry, git(), hooked(), call(), kinds(), _linking(), log_of() (+20 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (19): acquire_daemon_lock(), acquire_lock(), DaemonAlreadyRunning, DaemonLock, holder(), lock_path(), LockHeld, _read_pid() (+11 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (21): client(), clock(), fixture_contract(), free_port(), git_identity(), git_repo(), home(), isolated_git() (+13 more)

### Community 27 - "Community 27"
Cohesion: 0.08
Nodes (7): marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, same_path(), Worktree, WorktreeSession

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (26): allowed_env(), build_argv(), check_worktree(), child_env(), existing_stubs(), expand_home(), _remove_empty_tree(), remove_new_stubs() (+18 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (18): CheckResult, _check_command(), load_contract(), _message(), parse_contract(), _Strict, TemplateCommands, TemplateContract (+10 more)

### Community 30 - "Community 30"
Cohesion: 0.09
Nodes (16): GitHubClient, GitHubError, _message(), create_pull(), get_pull(), _list(), list_review_comments(), list_reviews() (+8 more)

### Community 31 - "Community 31"
Cohesion: 0.09
Nodes (17): serve(), load_or_create_token(), read_token(), token_path(), ensure_home(), is_test(), main(), oversized() (+9 more)

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (26): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree(), test_current_lists_the_phase_lines() (+18 more)

### Community 33 - "Community 33"
Cohesion: 0.11
Nodes (29): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+21 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (33): fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes(), test_default_branch_sha(), test_default_branch_sha_outside_a_repo() (+25 more)

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (18): dumper(), loader(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap() (+10 more)

### Community 36 - "Community 36"
Cohesion: 0.10
Nodes (21): implement(), on_raw(), _transcript(), on_raw(), append_transcript(), _artifact_name(), ArtifactName, attempt_dir() (+13 more)

### Community 37 - "Community 37"
Cohesion: 0.07
Nodes (16): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), ResumeTimer, test_entry_with_a_note(), test_entry_without_a_note() (+8 more)

### Community 38 - "Community 38"
Cohesion: 0.21
Nodes (23): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+15 more)

### Community 39 - "Community 39"
Cohesion: 0.10
Nodes (15): hours(), approve_command(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner() (+7 more)

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (25): _cycle(), _duplicate(), _estimate(), plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused() (+17 more)

### Community 41 - "Community 41"
Cohesion: 0.11
Nodes (20): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+12 more)

### Community 42 - "Community 42"
Cohesion: 0.09
Nodes (15): _read(), show_command(), ContextBudgetError, ContextError, PromptTemplateError, ContextInputs, DependencyView, GateFailure (+7 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (16): App(), root, createItem(), getItem(), listItems(), Item, NewItem, ItemList() (+8 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (20): cap_excerpt(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total() (+12 more)

### Community 45 - "Community 45"
Cohesion: 0.13
Nodes (25): editor_command(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores(), test_edit_interrupted_restores() (+17 more)

### Community 46 - "Community 46"
Cohesion: 0.10
Nodes (18): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+10 more)

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (16): fake(), FakeGitHub, git(), leaks(), log_of(), start(), status(), test_a_failed_pull_request_removes_its_branch_and_blocks() (+8 more)

### Community 48 - "Community 48"
Cohesion: 0.11
Nodes (17): ProjectError, ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate() (+9 more)

### Community 49 - "Community 49"
Cohesion: 0.14
Nodes (15): agent_stopped(), attempt_once(), check_resolved(), commit(), drive(), _git(), integrate(), interrupted() (+7 more)

### Community 50 - "Community 50"
Cohesion: 0.15
Nodes (25): run_git(), branch(), git_out(), head(), _squash(), _stage_link(), test_advance_fast_forwards_the_checked_out_branch(), test_advance_refuses_a_dirty_checkout() (+17 more)

### Community 51 - "Community 51"
Cohesion: 0.10
Nodes (15): create_app(), test_health(), make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old() (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.09
Nodes (10): ApiClient, ApiError, DaemonNotRunning, _detail(), test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host() (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (13): all_command(), _base(), _call(), cancel_command(), _client(), _current_run_id(), discard_command(), _follow() (+5 more)

### Community 54 - "Community 54"
Cohesion: 0.27
Nodes (24): failing(), Transcripts, kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth() (+16 more)

### Community 55 - "Community 55"
Cohesion: 0.12
Nodes (26): test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_cache_reads_count_a_tenth_toward_weighted_tokens(), test_empty_folder_left_by_an_uncommitted_attempt_is_reused(), test_ended_run_takes_no_attempts(), test_event_with_an_attempt_of_another_run_is_refused() (+18 more)

### Community 56 - "Community 56"
Cohesion: 0.12
Nodes (8): ahead_message(), _approved(), _artifact(), Delivery, delivery_mode(), _failed(), _held(), pr_branch()

### Community 57 - "Community 57"
Cohesion: 0.11
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 58 - "Community 58"
Cohesion: 0.13
Nodes (20): builtin_descriptions(), builtin_names(), builtin_root(), is_git_url(), _is_path(), _local(), open_template(), test_a_bad_ref_is_refused() (+12 more)

### Community 59 - "Community 59"
Cohesion: 0.12
Nodes (15): Agents, Budget, check_github_url(), check_slug(), Commands, ContextSettings, GatesSettings, GateTimeouts (+7 more)

### Community 60 - "Community 60"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (10): resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when(), _not_run() (+2 more)

### Community 62 - "Community 62"
Cohesion: 0.12
Nodes (10): GateLine, ItemVerdict, ReviewResult, _gate_word(), _ignore(), _items(), render_review_prompt(), review() (+2 more)

### Community 63 - "Community 63"
Cohesion: 0.16
Nodes (14): init(), test_a_copier_failure_is_reported(), test_a_failed_commit_removes_the_repo_and_workspace(), test_a_failed_workspace_empties_an_existing_folder(), test_a_file_as_repo_is_refused(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_non_empty_folder_is_refused_and_untouched() (+6 more)

### Community 64 - "Community 64"
Cohesion: 0.10
Nodes (10): _clean(), code(), fenced(), normalize_newlines(), _previous_vars(), _PromptLoader, PromptTemplate, render_template() (+2 more)

### Community 65 - "Community 65"
Cohesion: 0.12
Nodes (7): PlanError, SchedulerError, TransitionError, IdleReason, apply_transition(), parse_status(), TransitionResult

### Community 66 - "Community 66"
Cohesion: 0.16
Nodes (13): commit_file(), FakeGates, repo(), _crashed_journal(), git(), held(), recover(), restart() (+5 more)

### Community 67 - "Community 67"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 68 - "Community 68"
Cohesion: 0.15
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 69 - "Community 69"
Cohesion: 0.17
Nodes (15): home_denials(), test_read_only_policy_has_no_commands(), test_read_only_init_with_edit_is_not_enforced(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket(), test_extra_stack_commands_are_allowed() (+7 more)

### Community 70 - "Community 70"
Cohesion: 0.13
Nodes (8): github_token(), store_github_token(), MemoryKeyring, test_an_empty_token_is_refused(), test_an_unreadable_keychain_is_no_token(), test_no_token(), test_the_environment_wins(), test_the_keychain()

### Community 71 - "Community 71"
Cohesion: 0.24
Nodes (17): ConfigError, load_settings(), test_config_file_is_read(), test_defaults_without_config_file(), test_env_overrides_config_file(), test_explicit_override_wins(), test_home_follows_env(), test_invalid_config_names_field_and_file() (+9 more)

### Community 72 - "Community 72"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 74 - "Community 74"
Cohesion: 0.15
Nodes (8): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket(), test_template_is_in_the_built_wheel()

### Community 75 - "Community 75"
Cohesion: 0.25
Nodes (20): block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason(), test_gate_checked_items_replace_the_reviewers_answer() (+12 more)

### Community 76 - "Community 76"
Cohesion: 0.13
Nodes (14): PlanProblem, _and_list(), _find_cycles(), sort_ids(), validate_plan(), messages(), test_all_problems_are_reported_at_once(), test_cycle_starts_at_its_lowest_id_wherever_the_walk_enters() (+6 more)

### Community 77 - "Community 77"
Cohesion: 0.18
Nodes (12): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_a_huge_body_is_capped(), test_md_escape() (+4 more)

### Community 78 - "Community 78"
Cohesion: 0.15
Nodes (9): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, _statements(), _user_version(), WorkspaceRuns (+1 more)

### Community 79 - "Community 79"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 80 - "Community 80"
Cohesion: 0.25
Nodes (16): fake_tool_cmd(), gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+8 more)

### Community 81 - "Community 81"
Cohesion: 0.13
Nodes (7): clean(), _Log, ProcessResult, run_process(), _signal_group(), _stop_tree(), test_clean_strips_ansi_and_crlf()

### Community 82 - "Community 82"
Cohesion: 0.12
Nodes (3): _Session, _signal_group(), _stream()

### Community 83 - "Community 83"
Cohesion: 0.15
Nodes (17): state_db_path(), state_dir(), raw(), test_closed_log_refuses_calls(), test_daemon_instance_must_not_be_empty(), test_events_are_append_only(), test_fresh_database_has_version_6_and_all_tables(), test_naive_clock_raises() (+9 more)

### Community 84 - "Community 84"
Cohesion: 0.17
Nodes (17): explain_idle(), dashboard(), test_critical_path_skips_done_tickets(), test_dashboard_critical_path(), test_dashboard_remaining_hours(), test_dashboard_summary(), test_idle_all_done(), test_idle_awaiting_approval() (+9 more)

### Community 85 - "Community 85"
Cohesion: 0.16
Nodes (6): config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings

### Community 86 - "Community 86"
Cohesion: 0.12
Nodes (5): _clear_read_only_and_retry(), remove_path(), _clone(), _git(), _label()

### Community 87 - "Community 87"
Cohesion: 0.10
Nodes (5): describe(), print_run(), run_command(), check_command(), list_command()

### Community 89 - "Community 89"
Cohesion: 0.15
Nodes (8): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket(), test_status_of_an_active_run(), test_status_with_no_run()

### Community 90 - "Community 90"
Cohesion: 0.13
Nodes (7): main(), make_stubs(), parse(), anonymise(), logged_in(), test_real_run_creates_a_file_and_is_denied_python(), test_real_review_names_the_missing_test()

### Community 91 - "Community 91"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 92 - "Community 92"
Cohesion: 0.15
Nodes (3): Review, GitHubPoller, review_text()

### Community 93 - "Community 93"
Cohesion: 0.18
Nodes (11): critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours(), summary(), _work_order() (+3 more)

### Community 94 - "Community 94"
Cohesion: 0.15
Nodes (11): parse_done_when(), DoneItem, test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts(), test_done_when_heading_variants(), test_done_when_ignores_code_fences() (+3 more)

### Community 95 - "Community 95"
Cohesion: 0.16
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 96 - "Community 96"
Cohesion: 0.14
Nodes (8): check_gate_command(), gate_env(), split_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused(), test_unclosed_quote_is_refused()

### Community 97 - "Community 97"
Cohesion: 0.15
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 98 - "Community 98"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 99 - "Community 99"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 100 - "Community 100"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 101 - "Community 101"
Cohesion: 0.16
Nodes (8): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_github_reads_a_hidden_prompt(), test_secrets_set_refuses_other_names_and_empty_tokens(), test_secrets_set_without_a_keychain(), test_tickets_show_the_pull_request()

### Community 102 - "Community 102"
Cohesion: 0.16
Nodes (4): configure_logging(), JsonFormatter, PlainFormatter, _Redactor

### Community 103 - "Community 103"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 104 - "Community 104"
Cohesion: 0.20
Nodes (6): generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 105 - "Community 105"
Cohesion: 0.23
Nodes (11): test_init_existing_folder(), test_init_reports_every_problem(), test_init_template_ref_needs_a_template(), test_init_then_validate(), test_init_with_a_bad_template_creates_nothing(), test_init_with_a_git_template_prints_the_commit_first(), test_init_with_a_git_template_runs_no_global_git_hooks(), test_init_with_a_local_template() (+3 more)

### Community 106 - "Community 106"
Cohesion: 0.27
Nodes (8): require_valid(), sort_tickets(), _ids(), next_ready(), _statuses(), _unmet(), waiting_on(), Ticket

### Community 107 - "Community 107"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 108 - "Community 108"
Cohesion: 0.25
Nodes (7): auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template()

### Community 109 - "Community 109"
Cohesion: 0.33
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 110 - "Community 110"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 111 - "Community 111"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 112 - "Community 112"
Cohesion: 0.20
Nodes (6): consistency_errors(), InvalidVerdict, _location(), parse_verdict(), ParsedItem, ParsedVerdict

### Community 113 - "Community 113"
Cohesion: 0.27
Nodes (10): RepoDocs, base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries(), test_fixture_docs_fit_untrimmed(), test_large_spec_keeps_the_outline_and_relevant_sections(), test_long_claude_md_keeps_its_beginning() (+2 more)

### Community 114 - "Community 114"
Cohesion: 0.30
Nodes (10): check_transition(), make(), test_allowed_transitions_pass(), test_disallowed_transition_messages(), test_disallowed_transitions_raise(), test_running_from_blocked_also_waits_for_dependencies(), test_running_needs_a_valid_plan(), test_running_waits_for_every_dependency() (+2 more)

### Community 116 - "Community 116"
Cohesion: 0.29
Nodes (6): auth(), follow(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_refusals_carry_the_message(), test_run_through_the_api_merges_into_main()

### Community 117 - "Community 117"
Cohesion: 0.22
Nodes (7): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install(), use(), fake_claude_cmd(), sandbox_which()

### Community 118 - "Community 118"
Cohesion: 0.20
Nodes (5): manager(), wt_repo(), wt_root(), run_log(), test_unknown_integration()

### Community 119 - "Community 119"
Cohesion: 0.26
Nodes (8): branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing(), test_worktree_of_a_killed_process_is_recovered()

### Community 120 - "Community 120"
Cohesion: 0.22
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 121 - "Community 121"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 122 - "Community 122"
Cohesion: 0.18
Nodes (4): main(), start(), test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 123 - "Community 123"
Cohesion: 0.17
Nodes (5): FixedClock, run_log(), test_committed_events_are_published_in_order(), test_concurrent_appends_get_increasing_ids(), test_failed_insert_publishes_nothing()

### Community 124 - "Community 124"
Cohesion: 0.21
Nodes (4): test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1()

### Community 125 - "Community 125"
Cohesion: 0.23
Nodes (3): health(), Health, create_app()

### Community 126 - "Community 126"
Cohesion: 0.27
Nodes (9): test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401() (+1 more)

### Community 127 - "Community 127"
Cohesion: 0.22
Nodes (3): get_engine(), make_engine(), test_migrations_create_and_drop_the_schema()

### Community 128 - "Community 128"
Cohesion: 0.29
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 129 - "Community 129"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 130 - "Community 130"
Cohesion: 0.22
Nodes (3): init(), validate_project(), version()

### Community 131 - "Community 131"
Cohesion: 0.18
Nodes (3): describe(), make_runner(), review_command()

### Community 132 - "Community 132"
Cohesion: 0.36
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 133 - "Community 133"
Cohesion: 0.33
Nodes (6): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder()

### Community 134 - "Community 134"
Cohesion: 0.24
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 135 - "Community 135"
Cohesion: 0.24
Nodes (4): lifespan(), keep_for(), recover_all_integrations(), recover_all_worktrees()

### Community 137 - "Community 137"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 139 - "Community 139"
Cohesion: 0.47
Nodes (4): Item, create_item(), get_item(), list_items()

### Community 142 - "Community 142"
Cohesion: 0.36
Nodes (4): client(), test_session(), engine(), session()

### Community 143 - "Community 143"
Cohesion: 0.50
Nodes (5): alive(), run(), test_invalid_utf8_and_crlf_are_cleaned_in_the_log(), test_output_cap_cuts_the_log_and_drains_the_process(), test_timeout_stops_the_whole_process_tree()

### Community 144 - "Community 144"
Cohesion: 0.46
Nodes (5): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 145 - "Community 145"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 148 - "Community 148"
Cohesion: 0.29
Nodes (4): escape_closing_tag(), _kept(), esc(), test_escaping_is_case_insensitive_and_spacing_tolerant()

### Community 149 - "Community 149"
Cohesion: 0.48
Nodes (3): policy(), user_home(), worktree()

### Community 151 - "Community 151"
Cohesion: 0.52
Nodes (6): copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line(), test_apply_unknown_ticket()

### Community 152 - "Community 152"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 153 - "Community 153"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 155 - "Community 155"
Cohesion: 0.33
Nodes (3): bare(), someone_pushes(), token()

### Community 157 - "Community 157"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **190 isolated node(s):** `CopyState`, `RetryProps`, `DaemonReply`, `RawDaemonInfo`, `allowImportingTsExtensions` (+185 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1564 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **128 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RunLog` connect `Community 18` to `Community 4`, `Community 5`, `Community 135`, `Community 8`, `Community 9`, `Community 12`, `Community 17`, `Community 146`, `Community 23`, `Community 25`, `Community 156`, `Community 32`, `Community 161`, `Community 36`, `Community 51`, `Community 54`, `Community 57`, `Community 78`, `Community 83`, `Community 88`, `Community 110`, `Community 118`, `Community 122`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `Community 16` to `Community 3`, `Community 4`, `Community 5`, `Community 135`, `Community 8`, `Community 9`, `Community 91`, `Community 50`, `Community 51`, `Community 118`, `Community 119`, `Community 27`, `Community 124`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `ClaudeStreamParser` connect `Community 0` to `Community 82`, `Community 28`, `Community 14`, `Community 7`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `RunLog` (e.g. with `Attempt` and `AttemptKind`) actually correct?**
  _`RunLog` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `CopyState`, `RetryProps`, `DaemonReply` to the rest of the system?**
  _190 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.055860805860805864 - nodes in this community are weakly interconnected._