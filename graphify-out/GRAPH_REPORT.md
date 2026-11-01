# Graph Report - Project_Manager  (2026-11-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 5826 nodes · 16564 edges · 340 communities (164 shown, 176 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1461 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a6825bcf`
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
- Community 174
- Community 175
- Community 176
- Community 177
- Community 180
- Community 181
- Community 183
- Community 184
- Community 328
- Community 329
- Community 330

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 109 edges
2. `WorktreeManager` - 82 edges
3. `load_project()` - 81 edges
4. `RunRegistry` - 71 edges
5. `AgentPolicy` - 69 edges
6. `FakeRunner` - 68 edges
7. `ClaudeStreamParser` - 61 edges
8. `Run` - 58 edges
9. `build_implementer_prompt()` - 57 edges
10. `RunLoop` - 55 edges

## Surprising Connections (you probably didn't know these)
- `schema()` --calls--> `create_app()`  [INFERRED]
  scripts/dump_openapi.py → daemon/src/spoolhq/api/app.py
- `test_codex_not_logged_in_says_codex_login()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `integrate()` --calls--> `IntegrationResult`  [INFERRED]
  daemon/tests/services/runloop/test_loop.py → daemon/src/spoolhq/services/runloop/integrator.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py

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

## Communities (340 total, 176 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (50): weighted_tokens(), format_version(), parse_version(), build_argv(), check_worktree(), child_env(), existing_stubs(), expand_home() (+42 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (21): DaemonLock, approve(), reject(), unblock(), _waiting(), Integrator, active_message(), take_run_lock() (+13 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (62): advance(), checked_out(), _clean_line(), commit(), commit_message(), conclude_merge(), conflict_files(), create_tag() (+54 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (38): branch_name(), _recover_one(), RecoveryAction, RecoveryEntry, branch_sha(), default_branch_sha(), DirtyRepoError, ensure_no_operation_in_progress() (+30 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (48): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), _usage_counts(), usd_to_micro(), assistant(), load() (+40 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (37): slugify(), clean_title(), InvalidPlan, _not_blank(), one_line(), PlannedTicket, PlannerError, PlanOutput (+29 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (27): format_ts(), RunLogError, utc_now(), decode_cursor(), encode_cursor(), page_runs(), RunPage, AttemptKind (+19 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (27): edit_ticket(), parse_done_when(), run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError, DoneItem (+19 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (30): delete_branch(), fetch(), github_repo(), _network(), push(), push_tag(), PushResult, remote_ref() (+22 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (46): AgentPolicy, assert_gone(), endpoint_runner(), fake_probe(), read_record(), Recorder, run(), runner() (+38 more)

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (25): make_runner(), dotted_path(), format_errors(), _message(), _model_at(), _number(), ProjectError, ProjectValidationError (+17 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (15): agents_command(), describe(), describe_roles(), describe_worktrees(), ApiError, DaemonNotRunning, fail(), settings() (+7 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (49): state_db_path(), state_dir(), FailingCommit, raw(), run_log(), test_a_plan_run_has_kind_plan_and_its_attempts_in_runs_plan(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs() (+41 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (30): github_token(), store_github_token(), delete_secret(), secret_status(), SecretStatus, store_secret(), adapter(), AdapterCase (+22 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (55): load_ticket(), save_ticket(), errors_for(), make_project(), replace_line(), round_trip_tickets(), save_and_read(), test_assignment_is_validated() (+47 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (26): approval_message(), _result(), HoldForIntegration, IntegrationResult, IntegrationStatus, agent_stopped(), attempt_once(), check_resolved() (+18 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (21): test_serve_starts_and_serves_docs(), wait_for_health(), main(), make_stubs(), parse(), ask_hook(), main(), parse() (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.06
Nodes (30): client(), clock(), fake_backend(), fake_claude_cmd(), fake_codex_cmd(), fake_graphify(), fake_sdk_cmd(), fixture_contract() (+22 more)

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (49): init_project(), load_project(), del_path(), errors_for(), _fail_after_yaml(), set_path(), test_a_template_must_be_a_block(), test_all_errors_are_reported_at_once() (+41 more)

### Community 19 - "Community 19"
Cohesion: 0.09
Nodes (44): build_implementer_prompt(), assert_snapshot(), block(), fixture_inputs(), fixture_text(), fixture_ticket(), read_text(), test_negative_cap_is_refused() (+36 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (31): bare(), crash_at(), delivery(), git(), log_of(), mate(), recover_twice(), run() (+23 more)

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (20): AgentSdkRunner, check_command(), check_path(), check_tool(), make_hook(), pre_tool_use(), relative_pattern(), probe() (+12 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 23 - "Community 23"
Cohesion: 0.10
Nodes (27): service_errors(), approve_ticket(), Artifact, cancel_run(), current_run(), discard_ticket(), get_artifact(), get_run() (+19 more)

### Community 24 - "Community 24"
Cohesion: 0.06
Nodes (46): dependencies, react, react-dom, engines, node, name, packageManager, private (+38 more)

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (30): ChangedFile, parse_numstat(), staged_changes(), decide(), read_artifact(), as_record(), _compile(), delivery_mode() (+22 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (17): logged_in(), inputs(), worktree(), jobs(), registry(), test_a_failed_plan_blocks_the_run_with_the_error(), test_a_plan_run_is_recorded_with_kind_plan_and_its_usage(), test_approve_through_the_jobs() (+9 more)

### Community 27 - "Community 27"
Cohesion: 0.07
Nodes (18): create_app(), lifespan(), _openapi(), LocalOnlyMiddleware, check_git(), recover_all_integrations(), recover_all_worktrees(), serve() (+10 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (38): api_method(), api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), daemon_request() (+30 more)

### Community 29 - "Community 29"
Cohesion: 0.06
Nodes (18): cap_excerpt(), ContextBudgetError, ContextError, PromptTemplateError, _clean(), code(), escape_closing_tag(), fenced() (+10 more)

### Community 30 - "Community 30"
Cohesion: 0.06
Nodes (6): check_ticket_id(), _user_approved(), attempt_dir_name(), _check_count(), _make_attempt_dir(), Run

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (25): policy_parts(), build_argv(), install_dir(), permission_profile(), policy_parts(), refusal(), required_parts(), temp_folders() (+17 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (41): WorktreeManager, run_git(), branches(), make_read_only(), marker(), real(), registered_paths(), sha() (+33 more)

### Community 33 - "Community 33"
Cohesion: 0.07
Nodes (19): keep_for(), EventBus, RunLog, WorkspaceRuns, test_tickets_show_the_pull_request(), bus(), drain(), run_log() (+11 more)

### Community 34 - "Community 34"
Cohesion: 0.20
Nodes (31): LocalIntegrator, RunRegistry, Transcripts, git(), hooked(), call(), kinds(), _linking() (+23 more)

### Community 35 - "Community 35"
Cohesion: 0.06
Nodes (16): billing_for(), CodexCliRunner, legacy_sandbox(), login_method(), child_env(), endpoint_token(), keyring_key(), missing_token() (+8 more)

### Community 36 - "Community 36"
Cohesion: 0.09
Nodes (39): PlanProblem, _and_list(), validate_plan(), check_transition(), dashboard(), make(), messages(), test_all_problems_are_reported_at_once() (+31 more)

### Community 37 - "Community 37"
Cohesion: 0.11
Nodes (23): id_key(), _find_cycles(), require_valid(), sort_ids(), sort_tickets(), critical_path(), CriticalPath, _hours() (+15 more)

### Community 38 - "Community 38"
Cohesion: 0.07
Nodes (8): marker_key(), _norm(), parse_worktree_list(), RegisteredWorktree, same_path(), Worktree, WorktreeSession, test_parse_worktree_list()

### Community 39 - "Community 39"
Cohesion: 0.09
Nodes (17): loader(), CheckResult, load_contract(), _message(), parse_contract(), _Strict, TemplateCommands, TemplateContract (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (28): Hooked, write_ticket(), crashed_run(), lock_is_free(), status(), test_a_codex_reviewer_or_planner_is_warned_about_at_run_start(), test_cancel_a_paused_run(), test_cancel_during_the_implementer_removes_the_worktree() (+20 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (29): assert_refused(), read_only(), read_record(), refused_message(), run(), runner(), temps(), test_a_custom_endpoint_never_gets_the_users_login() (+21 more)

### Community 42 - "Community 42"
Cohesion: 0.08
Nodes (14): table(), _cost(), list_command(), _policy(), _run_log(), show_command(), _tokens(), _workspace() (+6 more)

### Community 43 - "Community 43"
Cohesion: 0.08
Nodes (15): billing_for(), ClaudeCliRunner, platform_reason(), test_backends_are_separated_by_a_blank_line(), test_codex_not_logged_in_says_codex_login(), test_codex_shows_what_it_enforces_per_role(), test_codex_worktrees_line(), test_graphify_found_with_its_version() (+7 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (34): ensure_clean(), fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it(), test_branch_name_refuses_bad_ticket_ids(), test_clean_repo_passes(), test_default_branch_sha() (+26 more)

### Community 45 - "Community 45"
Cohesion: 0.11
Nodes (19): App(), root, createItem(), getItem(), listItems(), Item, NewItem, ItemList() (+11 more)

### Community 46 - "Community 46"
Cohesion: 0.14
Nodes (26): Merging, kinds(), log_of(), phases(), run_once(), test_agent_error_blocks_with_its_text(), test_budget_counts_cache_reads_at_a_tenth(), test_budget_used_up_blocks_before_the_next_attempt() (+18 more)

### Community 47 - "Community 47"
Cohesion: 0.09
Nodes (29): keep_connected(), keep_head(), keep_newest_entries(), _lines(), newest_entries(), newest_lines(), select_spec(), _total() (+21 more)

### Community 48 - "Community 48"
Cohesion: 0.10
Nodes (30): apiError(), call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion() (+22 more)

### Community 49 - "Community 49"
Cohesion: 0.06
Nodes (5): billing_error(), CliTransport, SdkRun, StreamWarning, test_billing_errors_are_recognised()

### Community 50 - "Community 50"
Cohesion: 0.10
Nodes (16): _when(), _get(), get_integration(), Integration, IntegrationState, last_integration(), open_integrations(), pull_request_integration() (+8 more)

### Community 51 - "Community 51"
Cohesion: 0.08
Nodes (15): GateLine, ItemVerdict, ReviewResult, _gate_word(), _ignore(), _items(), render_review_prompt(), review() (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.14
Nodes (21): require_if_match(), run_log(), settings(), workspace(), put(), _conflict(), create_project(), get_project() (+13 more)

### Community 53 - "Community 53"
Cohesion: 0.11
Nodes (19): on_raw(), on_raw(), append_transcript(), _artifact_name(), attempt_dir(), attempt_files(), write_artifact(), FixedClock (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.12
Nodes (23): auth(), test_a_secret_is_stored_and_never_echoed(), test_no_keychain_is_a_readable_error(), test_secret_refusals(), test_settings_show_where_secrets_come_from(), done(), feed(), item() (+15 more)

### Community 55 - "Community 55"
Cohesion: 0.09
Nodes (15): hours(), approve_command(), check_command(), describe_plan(), generate_command(), _invalid_lines(), _listing(), make_runner() (+7 more)

### Community 56 - "Community 56"
Cohesion: 0.13
Nodes (25): ConfigError, load_settings(), make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old() (+17 more)

### Community 57 - "Community 57"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 58 - "Community 58"
Cohesion: 0.13
Nodes (15): all_command(), approve_command(), _base(), _call(), cancel_command(), _client(), _control(), discard_command() (+7 more)

### Community 59 - "Community 59"
Cohesion: 0.08
Nodes (12): ApiClient, _detail(), test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably(), test_version_without_daemon() (+4 more)

### Community 60 - "Community 60"
Cohesion: 0.10
Nodes (16): dumper(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap(), _node(), parse_yaml() (+8 more)

### Community 61 - "Community 61"
Cohesion: 0.20
Nodes (20): record(), run(), runner(), scenario(), test_a_billing_or_quota_error_blocks(), test_a_denied_call_is_reported_with_the_hooks_reason_and_logged(), test_a_failed_cli_reports_its_stderr(), test_a_local_endpoint_gets_the_dummy_token_not_the_key() (+12 more)

### Community 62 - "Community 62"
Cohesion: 0.22
Nodes (15): fake(), FakeGitHub, git(), leaks(), log_of(), start(), status(), test_a_failed_pull_request_removes_its_branch_and_blocks() (+7 more)

### Community 63 - "Community 63"
Cohesion: 0.16
Nodes (17): ManualClock, decisions(), log_of(), remote(), run_case(), test_a_400_line_change_goes_direct_and_logs_no_hits(), test_approve_integrates_and_reject_needs_a_note(), test_each_rule_alone_needs_a_person() (+9 more)

### Community 64 - "Community 64"
Cohesion: 0.07
Nodes (5): stop(), Session, _signal_group(), _stream(), StreamParser

### Community 65 - "Community 65"
Cohesion: 0.22
Nodes (24): FakeRunner, ReviewInputs, run(), test_approve(), test_budget_defaults_and_overrides(), run(), test_callbacks_get_events_and_raw_messages(), test_cancelled_is_passed_through() (+16 more)

### Community 66 - "Community 66"
Cohesion: 0.12
Nodes (19): denials_except(), home_denials(), policy(), user_home(), worktree(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home() (+11 more)

### Community 67 - "Community 67"
Cohesion: 0.14
Nodes (16): GitHubClient, GitHubError, create_pull(), get_pull(), _list(), list_review_comments(), list_reviews(), _pull() (+8 more)

### Community 68 - "Community 68"
Cohesion: 0.12
Nodes (11): _api_error(), error_response(), ErrorBody, ErrorResponse, _http_error(), install(), _validation_error(), _is_api_path() (+3 more)

### Community 69 - "Community 69"
Cohesion: 0.10
Nodes (10): sync(), approve_plan(), generate_plan(), _plans(), GitHubSync, GeneratePlan, PlanApproved, PlanStarted (+2 more)

### Community 71 - "Community 71"
Cohesion: 0.21
Nodes (19): cache_dir(), refresh(), FakeGraphify, builds(), pointer(), source(), test_a_busy_cache_gives_no_map(), test_a_cache_from_another_version_is_discarded() (+11 more)

### Community 72 - "Community 72"
Cohesion: 0.10
Nodes (15): check_command(), describe_source(), list_command(), _clear_read_only_and_retry(), remove_path(), builtin_descriptions(), builtin_names(), builtin_root() (+7 more)

### Community 73 - "Community 73"
Cohesion: 0.22
Nodes (26): copy_dashboard(), make_project(), set_status(), test_approve_moves_the_drafts_then_has_nothing_to_approve(), test_approve_refuses_a_cycle(), test_check_invalid_files_only(), test_check_one_ticket_and_unknown_project(), test_check_reports_problems_and_invalid_files() (+18 more)

### Community 74 - "Community 74"
Cohesion: 0.11
Nodes (10): _authenticate(), _convert(), _Envelopes, events(), EventStreams, _send(), _stream(), listener() (+2 more)

### Community 75 - "Community 75"
Cohesion: 0.09
Nodes (16): BackendSettings, Budget, _check_base_url(), check_github_url(), _check_path_pattern(), Commands, ContextSettings, GatesSettings (+8 more)

### Community 76 - "Community 76"
Cohesion: 0.16
Nodes (17): close_code(), connect(), emit(), receive(), run_log(), test_a_client_receives_every_event_of_a_fake_run_in_order(), test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(), stuck() (+9 more)

### Community 77 - "Community 77"
Cohesion: 0.10
Nodes (12): daemon_answering(), test_github_sync_prints_each_line(), test_github_sync_through_the_api(), test_run_status_shows_the_pull_request(), test_secrets_set_anthropic(), test_secrets_set_endpoint_token(), test_secrets_set_github_reads_a_hidden_prompt(), fake_getpass() (+4 more)

### Community 78 - "Community 78"
Cohesion: 0.15
Nodes (10): get_ticket(), get_tickets(), put_ticket(), _read(), unblock_ticket(), InvalidTicketView, Note, TicketList (+2 more)

### Community 79 - "Community 79"
Cohesion: 0.14
Nodes (14): show_command(), ContextInputs, DependencyView, GateFailure, PreviousAttempt, RenderedPrompt, RepoDocs, ReviewNote (+6 more)

### Community 80 - "Community 80"
Cohesion: 0.15
Nodes (11): resolve_program(), DoneWhenCheck, GateFailureData, GateResult, GateRun, GateStatus, check_done_when(), _not_run() (+3 more)

### Community 81 - "Community 81"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 82 - "Community 82"
Cohesion: 0.17
Nodes (20): plan(), revised(), snapshot(), test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(), test_a_missing_spec_is_refused(), test_a_run_that_does_not_complete_writes_nothing(), test_a_valid_retry_writes_the_plan(), test_an_unknown_project_is_refused() (+12 more)

### Community 83 - "Community 83"
Cohesion: 0.11
Nodes (7): config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings, schema()

### Community 84 - "Community 84"
Cohesion: 0.07
Nodes (27): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+19 more)

### Community 85 - "Community 85"
Cohesion: 0.14
Nodes (13): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+5 more)

### Community 86 - "Community 86"
Cohesion: 0.14
Nodes (3): summarize(), CodexStreamParser, _int()

### Community 87 - "Community 87"
Cohesion: 0.14
Nodes (9): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_no_code_map_note_when_the_map_is_off(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket() (+1 more)

### Community 88 - "Community 88"
Cohesion: 0.17
Nodes (14): init(), test_a_copier_failure_is_reported(), test_a_failed_commit_removes_the_repo_and_workspace(), test_a_failed_workspace_empties_an_existing_folder(), test_a_file_as_repo_is_refused(), test_a_git_url_template_records_the_commit(), test_a_local_template(), test_a_non_empty_folder_is_refused_and_untouched() (+6 more)

### Community 89 - "Community 89"
Cohesion: 0.13
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.24
Nodes (21): parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met(), test_duplicate_index(), test_empty_reason() (+13 more)

### Community 91 - "Community 91"
Cohesion: 0.25
Nodes (15): auth(), follow(), _log(), test_a_needs_human_run_waits_then_is_rejected_and_approved(), test_attempt_artifacts(), test_current_with_no_run(), test_every_run_route_needs_the_token(), test_history_pages_are_stable_under_inserts() (+7 more)

### Community 92 - "Community 92"
Cohesion: 0.13
Nodes (16): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_excerpt_keeps_head_failure_window_and_tail() (+8 more)

### Community 93 - "Community 93"
Cohesion: 0.13
Nodes (12): PlanError, SchedulerError, TransitionError, apply_transition(), parse_status(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone() (+4 more)

### Community 94 - "Community 94"
Cohesion: 0.18
Nodes (14): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+6 more)

### Community 95 - "Community 95"
Cohesion: 0.13
Nodes (11): describe_graphify(), _build(), find_command(), Graphify, GraphifyError, _kill_tree(), probe(), run() (+3 more)

### Community 96 - "Community 96"
Cohesion: 0.18
Nodes (15): is_git_url(), open_template(), test_a_bad_ref_is_refused(), test_a_built_in_records_the_package_version(), test_a_git_ref(), test_a_git_url_is_resolved_to_a_commit_and_cleaned_up(), test_a_local_folder(), test_a_local_git_repository_at_a_ref() (+7 more)

### Community 97 - "Community 97"
Cohesion: 0.18
Nodes (12): acquire_daemon_lock(), DaemonAlreadyRunning, lock_path(), make_workspace(), test_list_workspaces_skips_non_projects(), test_recovery_failure_skips_the_workspace(), test_registry_keeps_one_log_and_bus_per_workspace(), test_second_acquire_names_the_holder() (+4 more)

### Community 98 - "Community 98"
Cohesion: 0.20
Nodes (15): parse_plan(), _where(), dashboard_plan(), block(), errors(), existing_ticket(), test_a_dependency_on_a_missing_ticket_is_reported(), test_a_self_dependency_is_reported_by_the_ticket_store() (+7 more)

### Community 99 - "Community 99"
Cohesion: 0.18
Nodes (12): _done_when(), _gates(), md_escape(), pull_request_body(), pull_request_title(), section(), test_a_huge_body_is_capped(), test_md_escape() (+4 more)

### Community 100 - "Community 100"
Cohesion: 0.09
Nodes (22): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 101 - "Community 101"
Cohesion: 0.25
Nodes (16): fake_tool_cmd(), gates(), test_all_passing(), test_ansi_and_invalid_utf8_in_the_excerpt(), test_done_when_maps_configured_commands_only(), test_done_when_with_just_test(), test_failing_install_skips_lint_and_test(), test_failing_lint_still_runs_test() (+8 more)

### Community 102 - "Community 102"
Cohesion: 0.14
Nodes (11): _assistant(), clock(), _init(), make_loop(), make(), project(), registry(), repo() (+3 more)

### Community 103 - "Community 103"
Cohesion: 0.18
Nodes (9): CodeMap, _current(), _drop(), _refresh(), _remove_unused(), _save(), summary(), test_a_report_without_known_sections_is_empty() (+1 more)

### Community 104 - "Community 104"
Cohesion: 0.16
Nodes (8): ApiError, delete_secret_route(), get_settings(), _keychain_error(), put_secret(), DaemonSettings, SecretValue, SecretView

### Community 105 - "Community 105"
Cohesion: 0.18
Nodes (10): daemon(), test_cancel_resume_discard_and_status(), test_ctrl_c_detaches(), test_errors_from_the_daemon_exit_1(), test_integrate_merges_a_held_ticket(), test_needs_human_waits_then_approve_merges(), test_next_follows_the_run_to_its_end(), test_status_after_a_merge_shows_the_last_merged_ticket() (+2 more)

### Community 106 - "Community 106"
Cohesion: 0.11
Nodes (7): set_command(), sync_command(), describe(), review_command(), store_api_key(), store_endpoint_token(), test_store()

### Community 107 - "Community 107"
Cohesion: 0.13
Nodes (6): acquire_lock(), holder(), LockHeld, _read_pid(), _try_lock(), _unlock()

### Community 108 - "Community 108"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 109 - "Community 109"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 110 - "Community 110"
Cohesion: 0.15
Nodes (10): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+2 more)

### Community 111 - "Community 111"
Cohesion: 0.22
Nodes (10): auth(), etag(), fixture_tickets(), test_conflicting_edit(), test_get_then_put_unchanged_is_byte_identical(), test_list_with_filters(), test_status_changes_follow_the_transition_table(), test_ticket_ids_are_checked_in_the_path() (+2 more)

### Community 112 - "Community 112"
Cohesion: 0.13
Nodes (9): check_gate_command(), gate_env(), split_command(), _check_command(), test_gate_env_drops_secrets_and_adds_ci_settings(), test_gate_env_keeps_windows_system_variables(), test_quoted_argument_with_spaces_is_one_argument(), test_shell_syntax_is_refused() (+1 more)

### Community 113 - "Community 113"
Cohesion: 0.29
Nodes (10): failing(), run_once(), set_code_map_chars(), status(), test_a_hanging_graphify_does_not_hold_up_the_run(), test_a_retry_updates_the_map_only_after_the_code_changed(), test_the_implementer_gets_the_map_and_the_reviewer_never_does(), test_the_next_run_updates_the_cache_instead_of_rebuilding() (+2 more)

### Community 114 - "Community 114"
Cohesion: 0.20
Nodes (9): ProcessResult, run_process(), _signal_group(), _stop_tree(), alive(), run(), test_invalid_utf8_and_crlf_are_cleaned_in_the_log(), test_output_cap_cuts_the_log_and_drains_the_process() (+1 more)

### Community 115 - "Community 115"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 116 - "Community 116"
Cohesion: 0.19
Nodes (12): _api_routes(), test_bodies_over_1_mb_are_refused(), test_docs_and_openapi_are_served(), test_every_api_route_but_health_needs_the_token(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token() (+4 more)

### Community 117 - "Community 117"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 118 - "Community 118"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 119 - "Community 119"
Cohesion: 0.21
Nodes (4): get_engine(), get_session(), make_engine(), test_migrations_create_and_drop_the_schema()

### Community 120 - "Community 120"
Cohesion: 0.21
Nodes (11): test_init_existing_folder(), test_init_reports_every_problem(), test_init_template_ref_needs_a_template(), test_init_then_validate(), test_init_with_a_bad_template_creates_nothing(), test_init_with_a_git_template_prints_the_commit_first(), test_init_with_a_git_template_runs_no_global_git_hooks(), test_init_with_a_local_template() (+3 more)

### Community 121 - "Community 121"
Cohesion: 0.20
Nodes (12): AttemptFinishedData, AttemptStartedData, AuthMessage, _Data, EventEnvelope, IntegrateData, LogData, PolicyDecisionData (+4 more)

### Community 122 - "Community 122"
Cohesion: 0.17
Nodes (6): get_settings(), Settings, run(), url(), test_default_session_uses_the_configured_database(), test_settings_read_the_environment()

### Community 123 - "Community 123"
Cohesion: 0.31
Nodes (15): make_project(), test_list_dashboard_plan(), test_list_empty_project(), test_list_missing_project(), test_list_no_match(), test_list_only_invalid_files(), test_list_prints_a_table(), test_list_reports_invalid_files_last() (+7 more)

### Community 124 - "Community 124"
Cohesion: 0.20
Nodes (6): generated(), just(), test_init_generates_one_commit_and_fills_the_commands(), test_lint_catches_a_sibling_slice_import(), test_lint_catches_fastapi_in_services(), test_lint_passes_without_violations()

### Community 125 - "Community 125"
Cohesion: 0.30
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 126 - "Community 126"
Cohesion: 0.24
Nodes (9): recover_worktrees(), branches(), real(), registered(), test_recovery_cleans_up_and_keeps_what_it_must(), test_recovery_reports_a_worktree_it_cannot_remove(), stuck(), test_recovery_with_no_root_does_nothing() (+1 more)

### Community 127 - "Community 127"
Cohesion: 0.22
Nodes (8): EditConflict, etag_of(), _lock(), read_with_etag(), write_if_match(), test_concurrent_edits_with_the_same_etag_let_one_win(), edit(), test_write_only_when_the_etag_matches()

### Community 129 - "Community 129"
Cohesion: 0.18
Nodes (6): commit_file(), anonymise(), manager(), wt_repo(), wt_root(), test_real_review_names_the_missing_test()

### Community 130 - "Community 130"
Cohesion: 0.17
Nodes (9): test_a_sequence_replays_one_transcript_per_run(), test_cancel(), test_detect(), test_policy_violation(), test_read_only_init_with_edit_is_not_enforced(), test_replay_of_the_recorded_real_run(), test_replay_writes_the_file(), test_writes_outside_the_worktree_are_skipped() (+1 more)

### Community 131 - "Community 131"
Cohesion: 0.17
Nodes (8): EventEnvelope, EventStreamOptions, FINAL_CLOSES, isEnvelope(), subscribeEvents(), MockSocket, start(), Schemas

### Community 132 - "Community 132"
Cohesion: 0.36
Nodes (9): auth(), error(), etag(), test_create_project_from_an_unknown_template(), test_create_project_like_spool_init(), test_list_and_get_projects(), test_settings_edit_with_etags(), test_spec_edit_with_etags() (+1 more)

### Community 133 - "Community 133"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 135 - "Community 135"
Cohesion: 0.32
Nodes (10): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+2 more)

### Community 136 - "Community 136"
Cohesion: 0.13
Nodes (15): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, openapi-fetch, radix-ui (+7 more)

### Community 137 - "Community 137"
Cohesion: 0.37
Nodes (9): error(), test_a_description_over_the_limit(), test_a_missing_command(), test_a_missing_file(), test_a_valid_contract(), test_bad_yaml(), test_every_problem_is_listed(), test_shell_syntax_in_a_command() (+1 more)

### Community 138 - "Community 138"
Cohesion: 0.27
Nodes (7): auth(), plan_client(), test_approve_mirrors_the_cli(), test_every_plan_route_needs_the_token(), test_generate_refusals(), test_generate_returns_202_and_the_run_is_logged_as_a_plan(), test_generate_without_a_body_and_with_a_template()

### Community 139 - "Community 139"
Cohesion: 0.26
Nodes (4): agents(), AgentsView, BackendView, GraphifyView

### Community 140 - "Community 140"
Cohesion: 0.16
Nodes (4): test_health(), Detected, test_agents_lists_backends_and_graphify(), test_agents_needs_the_token()

### Community 141 - "Community 141"
Cohesion: 0.22
Nodes (7): client(), test_a_non_json_error_and_a_network_error(), test_a_plain_403_is_not_a_rate_limit(), test_an_empty_answer_is_none(), test_an_error_names_the_call_and_redacts_the_token(), test_rate_limits_say_when_to_retry(), test_requests_carry_the_token_and_api_headers()

### Community 142 - "Community 142"
Cohesion: 0.30
Nodes (10): make_plan(), test_a_failed_write_leaves_the_old_files(), test_a_title_that_needs_quotes_stays_valid_yaml(), test_an_unreadable_plan_record_keeps_every_draft(), test_approval_moves_only_drafts_and_changes_only_the_status_line(), test_approval_names_every_problem(), test_approval_of_an_unknown_project_fails(), test_approval_refuses_a_cycle_and_names_its_members() (+2 more)

### Community 144 - "Community 144"
Cohesion: 0.19
Nodes (5): create_app(), client(), test_session(), engine(), session()

### Community 145 - "Community 145"
Cohesion: 0.31
Nodes (5): Base, Item, create_item(), get_item(), list_items()

### Community 146 - "Community 146"
Cohesion: 0.20
Nodes (7): available_runners(), backend_names(), make_runner(), _check_backend(), test_codex_takes_the_endpoint_and_model(), test_the_agent_sdk_takes_the_endpoint_and_model(), test_the_built_in_backends()

### Community 147 - "Community 147"
Cohesion: 0.32
Nodes (5): create_item(), get_item(), list_items(), ItemCreate, ItemRead

### Community 148 - "Community 148"
Cohesion: 0.25
Nodes (3): test_check_a_git_url_prints_the_commit(), test_check_fails_with_the_gate_output(), test_check_passes()

### Community 149 - "Community 149"
Cohesion: 0.29
Nodes (5): check_template(), test_a_failing_gate(), test_a_passing_template(), test_an_invalid_contract_runs_nothing(), test_the_gates_run_in_a_git_work_tree()

### Community 150 - "Community 150"
Cohesion: 0.24
Nodes (4): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them()

### Community 152 - "Community 152"
Cohesion: 0.22
Nodes (3): clean(), _Log, test_clean_strips_ansi_and_crlf()

### Community 153 - "Community 153"
Cohesion: 0.25
Nodes (6): is_test(), main(), oversized(), is_test(), main(), oversized()

### Community 154 - "Community 154"
Cohesion: 0.33
Nodes (6): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder()

### Community 155 - "Community 155"
Cohesion: 0.33
Nodes (4): test_an_unparseable_line_and_no_result_names_the_parse_error(), test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(), test_an_unparseable_result_still_ends_the_input(), transcript()

### Community 156 - "Community 156"
Cohesion: 0.27
Nodes (5): allowed_env(), test_posix_output_is_unchanged(), test_secrets_never_pass_on_any_platform(), test_windows_gets_what_processes_need_to_start(), test_windows_names_match_in_any_case()

### Community 157 - "Community 157"
Cohesion: 0.24
Nodes (3): start(), test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 158 - "Community 158"
Cohesion: 0.27
Nodes (5): test_create_and_get(), test_create_rejects_an_empty_name(), test_get_missing_item_is_404(), test_list_in_creation_order(), test_service_without_http()

### Community 159 - "Community 159"
Cohesion: 0.22
Nodes (5): api_key(), no_parent_key(), stored_key(), test_an_unreadable_keychain_means_no_key(), test_the_key_comes_from_the_environment_then_the_keychain()

### Community 161 - "Community 161"
Cohesion: 0.22
Nodes (4): bare(), someone_pushes(), test_the_background_poller_syncs_every_project_and_survives_errors(), token()

### Community 162 - "Community 162"
Cohesion: 0.22
Nodes (9): scripts, build, check:api, dev, format, gen:api, lint, tauri (+1 more)

### Community 165 - "Community 165"
Cohesion: 0.39
Nodes (5): _check_not_newer(), connect(), _migrate(), _statements(), _user_version()

### Community 166 - "Community 166"
Cohesion: 0.46
Nodes (5): parse(), test_a_long_title_with_a_newline_becomes_one_clean_line(), test_invalid_tickets_are_refused(), test_text_fields_are_cleaned_to_one_line(), ticket()

### Community 167 - "Community 167"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 172 - "Community 172"
Cohesion: 0.33
Nodes (6): scripts, build, dev, format, lint, test

### Community 174 - "Community 174"
Cohesion: 0.33
Nodes (4): _cycle(), _duplicate(), _estimate(), test_invalid_output_is_retried_with_the_errors_then_fails()

### Community 176 - "Community 176"
Cohesion: 0.53
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 177 - "Community 177"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

## Knowledge Gaps
- **14 isolated node(s):** `@fontsource/inter`, `@fontsource/jetbrains-mono`, `openapi-typescript`, `tailwindcss`, `@tauri-apps/cli` (+9 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 1994 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **176 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ClaudeStreamParser` connect `Community 4` to `Community 0`, `Community 160`, `Community 43`, `Community 49`, `Community 21`, `Community 86`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `RunLog` (e.g. with `page_runs()` and `recover_interrupted()`) actually correct?**
  _`RunLog` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@fontsource/inter`, `@fontsource/jetbrains-mono`, `openapi-typescript` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.04416745698414849 - nodes in this community are weakly interconnected._
- **Why does `RunLog` connect `Community 33` to `Community 1`, `Community 2`, `Community 6`, `Community 135`, `Community 12`, `Community 25`, `Community 157`, `Community 30`, `Community 34`, `Community 42`, `Community 175`, `Community 50`, `Community 52`, `Community 53`, `Community 56`, `Community 63`, `Community 74`, `Community 76`, `Community 91`, `Community 97`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.04373464373464373 - nodes in this community are weakly interconnected._
- **Why does `WorktreeManager` connect `Community 32` to `Community 1`, `Community 2`, `Community 3`, `Community 129`, `Community 6`, `Community 38`, `Community 59`, `Community 11`, `Community 109`, `Community 56`, `Community 27`, `Community 126`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._