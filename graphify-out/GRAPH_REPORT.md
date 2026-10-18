# Graph Report - Project_Manager  (2026-10-18)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2850 nodes · 7383 edges · 173 communities (92 shown, 81 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 549 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fe379719`
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
- Community 156
- Community 157

## God Nodes (most connected - your core abstractions)
1. `RunLog` - 97 edges
2. `WorktreeManager` - 74 edges
3. `ClaudeStreamParser` - 66 edges
4. `AgentPolicy` - 59 edges
5. `build_implementer_prompt()` - 45 edges
6. `run_git()` - 42 edges
7. `FakeRunner` - 41 edges
8. `Ticket` - 40 edges
9. `fixture_inputs()` - 36 edges
10. `EventBus` - 35 edges

## Surprising Connections (you probably didn't know these)
- `test_not_logged_in_and_not_enforceable()` --calls--> `BackendInfo`  [INFERRED]
  daemon/tests/cli/test_agents.py → daemon/src/spoolhq/services/agents/model.py
- `too_old()` --calls--> `GitError`  [INFERRED]
  daemon/tests/api/test_worktrees_lifespan.py → daemon/src/spoolhq/services/git/runner.py
- `test_installed_git_is_new_enough()` --calls--> `check_git_version()`  [INFERRED]
  daemon/tests/services/git/test_runner.py → daemon/src/spoolhq/services/git/runner.py
- `test_publish_completes_while_a_subscriber_never_reads()` --indirect_call--> `stuck()`  [INFERRED]
  daemon/tests/services/runs/test_bus.py → daemon/tests/services/git/test_recovery.py
- `_Session` --uses--> `ClaudeStreamParser`  [INFERRED]
  daemon/src/spoolhq/services/agents/claude_cli.py → daemon/src/spoolhq/services/agents/claude_stream.py

## Import Cycles
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/files.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`
- 3-file cycle: `daemon/src/spoolhq/services/tickets/__init__.py -> daemon/src/spoolhq/services/tickets/editor.py -> daemon/src/spoolhq/services/tickets/store.py -> daemon/src/spoolhq/services/tickets/__init__.py`
- 4-file cycle: `daemon/src/spoolhq/services/runs/__init__.py -> daemon/src/spoolhq/services/runs/registry.py -> daemon/src/spoolhq/services/runs/recovery.py -> daemon/src/spoolhq/services/runs/log.py -> daemon/src/spoolhq/services/runs/__init__.py`

## Communities (173 total, 81 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (27): agents_command(), describe(), available_runners(), _Session, check_worktree(), existing_stubs(), expand_home(), _remove_empty_tree() (+19 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (50): _blocks(), ClaudeStreamParser, epoch_to_datetime(), _int(), summarize(), _usage_counts(), PermissionDenied, RateLimit (+42 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (51): _force_utf8_streams(), main(), FakeStream, make_project(), run_spool_cp1252(), test_cp1252_stream_becomes_utf8_and_keeps_errors(), test_main_forces_utf8_before_running_the_app(), test_plan_check_writes_utf8_arrows_under_cp1252() (+43 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (40): FakeRunner, ReviewInputs, _gate_word(), _items(), render_review_prompt(), review(), capture(), finish() (+32 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (14): branch_sha(), command_error(), subcommand(), trim_stderr(), _clear_read_only_and_retry(), marker_key(), _norm(), parse_worktree_list() (+6 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (25): default_branch_sha(), DirtyRepoError, ensure_no_operation_in_progress(), has_local_branch(), is_branch_name(), is_work_tree(), MissingBranchError, operation_in_progress() (+17 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (21): describe(), allowed_env(), check_gate_command(), gate_env(), resolve_program(), split_command(), DoneWhenCheck, GateFailureData (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (15): utc_now(), Transaction, AttemptKind, AttemptStatus, Event, EventKind, Run, RunStatus (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (6): test_startup_without_a_projects_folder_serves(), test_serve_starts_and_serves_docs(), wait_for_health(), main(), make_stubs(), parse()

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (39): RunLog, raw(), run_log(), test_attempt_lifecycle(), test_attempt_numbers_count_per_ticket_across_runs(), test_bad_usage_numbers_raise(), test_closed_log_refuses_calls(), test_committed_events_are_published_in_order() (+31 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (42): git_executable(), WorktreeManager, run_git(), branches(), make_read_only(), marker(), real(), registered_paths() (+34 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (37): branch_name(), slugify(), ensure_clean(), GitResult, fake_version(), run_git(), start_conflicting_merge(), test_branch_name_raises_if_git_refuses_it() (+29 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (32): SettingsDialog(), HomePage(), ProjectPanelPage(), DAEMON_HOST, DAEMON_START_COMMAND, cn(), Button(), buttonVariants (+24 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (18): cap_excerpt(), ContextBudgetError, ContextError, PromptTemplateError, _clean(), code(), escape_closing_tag(), fenced() (+10 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (35): api_url(), config_without_port_uses_the_default(), current_home(), daemon_get(), DAEMON_HOST, daemon_info(), DaemonError, Config (+27 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (37): description, engines, node, license, name, packageManager, private, type (+29 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (33): GateFailure, build_implementer_prompt(), assert_snapshot(), fixture_inputs(), fixture_ticket(), big_docs(), big_spec(), gate_output() (+25 more)

### Community 17 - "Community 17"
Cohesion: 0.09
Nodes (9): run_editor(), TicketEdit, source_name(), TicketError, TicketValidationError, find_ticket_file(), render_ticket(), _ticket_files() (+1 more)

### Community 18 - "Community 18"
Cohesion: 0.09
Nodes (18): dumper(), loader(), to_plain(), _block_indent(), _indent(), _inline_comment(), _is_delimiter(), _is_gap() (+10 more)

### Community 19 - "Community 19"
Cohesion: 0.18
Nodes (35): load_project(), del_path(), errors_for(), set_path(), test_all_errors_are_reported_at_once(), test_bad_repo_in_yaml(), test_bad_slug_is_refused(), test_default_branch_git_error_is_reported() (+27 more)

### Community 20 - "Community 20"
Cohesion: 0.09
Nodes (22): build_argv(), child_env(), sandbox_settings(), AgentPolicy, test_policy_fields_are_untouched_by_credentials_list(), test_unusable_backend_raises_before_starting(), parent_env(), settings_json() (+14 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (31): check_transition(), dashboard(), make(), test_all_problems_are_reported_at_once(), test_allowed_transitions_pass(), test_critical_path_skips_done_tickets(), test_critical_path_ties_prefer_lower_ids(), test_dashboard_critical_path() (+23 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (26): editor_command(), start_edit(), _unquote(), fake_editor(), make_ticket(), test_check_reports_a_deleted_file(), test_default_environment(), test_edit_aborted_prompt_restores() (+18 more)

### Community 23 - "Community 23"
Cohesion: 0.20
Nodes (28): read_record(), run(), runner(), test_api_key_billing_passes_the_key_and_the_budget(), test_billing_follows_the_auth_method(), test_claude_config_dir_reaches_the_settings(), test_default_permission_mode_from_env_scrub_is_accepted(), test_detect_leaves_no_stubs_in_the_current_folder() (+20 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (4): check_ticket_id(), attempt_dir_name(), _check_count(), Attempt

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (9): ApiClient, ApiError, DaemonNotRunning, test_client_connection_refused(), test_client_reports_a_server_that_is_not_spoolhq(), test_client_sends_token_and_reports_401(), test_serve_refuses_non_loopback_host(), test_version_with_bad_config_fails_readably() (+1 more)

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (15): acquire_daemon_lock(), DaemonAlreadyRunning, DaemonLock, lock_path(), _read_pid(), _try_lock(), _unlock(), make_workspace() (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.13
Nodes (17): append_transcript(), _artifact_name(), ArtifactName, attempt_dir(), attempt_files(), write_artifact(), attempt(), run_log() (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.15
Nodes (22): set_commands(), temp_logs(), test_defaults_to_the_repository(), test_failing_test_exits_1_with_the_test_names(), test_passing_gates_exit_0(), test_unknown_project_and_missing_folder(), fake_tool_cmd(), gates() (+14 more)

### Community 29 - "Community 29"
Cohesion: 0.17
Nodes (21): ConfigError, load_settings(), test_invalid_project_exits_1(), test_list_shows_state(), test_list_shows_unregistered_folders(), test_unknown_project_exits_1(), test_config_file_is_read(), test_defaults_without_config_file() (+13 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (15): EventBus, bus(), drain(), run_log(), test_a_failing_notify_callback_does_not_affect_the_others(), test_a_failing_subscriber_does_not_affect_the_others(), test_close_wakes_a_waiting_get(), test_closed_subscription_receives_nothing() (+7 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (9): describe(), make_runner(), GateLine, ItemVerdict, ReviewResult, _ignore(), InvalidVerdict, ParsedItem (+1 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (15): root, queryClient, QueryProvider(), AppRouter(), router, RootLayout(), routes, invokeMock (+7 more)

### Community 33 - "Community 33"
Cohesion: 0.07
Nodes (28): app, security, windows, build, beforeBuildCommand, beforeDevCommand, devUrl, frontendDist (+20 more)

### Community 34 - "Community 34"
Cohesion: 0.11
Nodes (9): _stream(), ProjectError, save_project(), dump(), merge(), parse(), read(), to_node() (+1 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (14): ProjectValidationError, Project, init_project(), _initial_yaml(), InitResult, list_workspaces(), _populate(), project_dir() (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (23): consistency_errors(), _location(), parse_verdict(), block(), body(), errors(), test_approve_with_an_unmet_item(), test_changes_requested_with_everything_met() (+15 more)

### Community 37 - "Community 37"
Cohesion: 0.16
Nodes (19): call(), DaemonInfo, DaemonReply, fromCommandError(), get(), getHealth(), getVersion(), Health (+11 more)

### Community 38 - "Community 38"
Cohesion: 0.21
Nodes (23): errors_for(), save_and_read(), test_bad_file_name(), test_block_list_keeps_its_layout(), test_changing_status_changes_only_that_line(), test_crlf_frontmatter_errors_count_lines(), test_dashboard_filters(), test_emptied_block_list_becomes_flow() (+15 more)

### Community 39 - "Community 39"
Cohesion: 0.08
Nodes (26): devDependencies, eslint, eslint-import-resolver-typescript, @eslint/js, eslint-plugin-boundaries, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+18 more)

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (9): billing_for(), ClaudeCliRunner, format_version(), parse_version(), fake_probe(), test_auth_status_that_is_not_json(), test_linux_needs_bubblewrap_and_socat(), test_macos_is_enforceable_and_others_are_not() (+1 more)

### Community 41 - "Community 41"
Cohesion: 0.13
Nodes (17): build_excerpt(), take(), _clip(), failing_tests(), first_failure(), _priority(), split_lines(), test_clean_strips_ansi_and_crlf() (+9 more)

### Community 42 - "Community 42"
Cohesion: 0.20
Nodes (9): serve(), load_or_create_token(), read_token(), token_path(), ensure_home(), test_empty_token_file_is_replaced(), test_loose_token_file_mode_is_tightened(), test_token_file_and_home_have_private_modes() (+1 more)

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (8): _read(), show_command(), ContextInputs, DependencyView, PreviousAttempt, RenderedPrompt, ReviewNote, TicketView

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (9): configure_logging(), JsonFormatter, PlainFormatter, _Redactor, log_file(), read_lines(), test_exceptions_are_logged(), test_log_lines_are_json_without_token() (+1 more)

### Community 45 - "Community 45"
Cohesion: 0.15
Nodes (13): _recover_one(), recover_worktrees(), RecoveryEntry, WorktreeInfo, WorktreeState, branches(), real(), registered() (+5 more)

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (12): make_repo(), test_awaiting_approval_keeps_and_done_removes(), test_interrupted_run_keeps_its_worktree(), test_keep_rule(), test_old_git_is_logged_and_the_daemon_serves(), too_old(), test_project_without_a_run_log_is_skipped(), test_startup_recovers_worktrees_and_skips_a_broken_project() (+4 more)

### Community 48 - "Community 48"
Cohesion: 0.17
Nodes (13): seed(), test_corrupt_database_exits_1(), test_project_without_runs(), test_reading_never_recovers_a_stale_run(), test_runs_list_filters_by_ticket(), test_runs_list_shows_newest_first(), test_runs_show_a_run_without_attempts(), test_runs_show_lists_attempts_with_folders() (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.14
Nodes (9): client(), clock(), free_port(), git_repo(), home(), isolated_git(), projects_dir(), token() (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (6): create_app(), lifespan(), health(), Health, check_git(), recover_all_worktrees()

### Community 51 - "Community 51"
Cohesion: 0.20
Nodes (14): home_denials(), test_budget_defaults_to_thirty_minutes(), test_command_becomes_exact_and_prefix_rules(), test_denied_paths_are_the_credentials_and_the_spoolhq_home(), test_empty_command_is_refused(), test_exact_message_from_the_ticket(), test_extra_stack_commands_are_allowed(), test_read_only_git_follows_stack_commands() (+6 more)

### Community 52 - "Community 52"
Cohesion: 0.14
Nodes (3): table(), SchedulerError, TransitionError

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (12): id_key(), PlanError, PlanProblem, _and_list(), _find_cycles(), sort_ids(), validate_plan(), messages() (+4 more)

### Community 54 - "Community 54"
Cohesion: 0.17
Nodes (12): RepoDocs, block(), fixture_text(), read_text(), base_chars(), big_spec(), fenced_content(), test_decisions_keep_the_newest_entries() (+4 more)

### Community 55 - "Community 55"
Cohesion: 0.22
Nodes (19): load_ticket(), make_project(), replace_line(), test_assignment_is_validated(), test_broken_file_does_not_stop_the_others(), test_double_quoted_escapes_do_not_hide_the_comment(), test_every_status_is_accepted(), test_folders_are_ignored() (+11 more)

### Community 56 - "Community 56"
Cohesion: 0.14
Nodes (7): fail(), _cost(), list_command(), _run_log(), show_command(), _tokens(), _workspace()

### Community 57 - "Community 57"
Cohesion: 0.18
Nodes (10): hours(), check_command(), _invalid_lines(), _listing(), next_command(), _plan_failed(), summary_command(), _valid_listing() (+2 more)

### Community 58 - "Community 58"
Cohesion: 0.17
Nodes (13): keep_head(), keep_newest_entries(), _lines(), select_spec(), _total(), Trimmed, words(), test_entries_keep_the_preamble_when_it_fits() (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.16
Nodes (12): _cap(), _collapse(), extract_progress_note(), format_progress_entry(), _sanitize(), test_entry_with_a_note(), test_entry_without_a_note(), test_last_block_wins_and_tags_are_case_insensitive() (+4 more)

### Community 60 - "Community 60"
Cohesion: 0.19
Nodes (11): Agents, Budget, Commands, ContextSettings, GatesSettings, GateTimeouts, GitSettings, Limits (+3 more)

### Community 61 - "Community 61"
Cohesion: 0.18
Nodes (10): _check_not_newer(), connect(), format_ts(), _migrate(), RunLogError, state_db_path(), state_dir(), _statements() (+2 more)

### Community 62 - "Community 62"
Cohesion: 0.23
Nodes (10): require_valid(), sort_tickets(), explain_idle(), IdleReason, _ids(), next_ready(), _statuses(), _unmet() (+2 more)

### Community 63 - "Community 63"
Cohesion: 0.19
Nodes (10): critical_path(), CriticalPath, _hours(), PlanSummary, _rank(), remaining_hours(), summary(), _work_order() (+2 more)

### Community 64 - "Community 64"
Cohesion: 0.22
Nodes (11): clear(), commit_hooks(), fired(), markers(), plain_commit(), require_hooks_fire(), test_default_hooks_folder_never_runs(), test_hook_written_by_the_agent_never_runs() (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.18
Nodes (9): ProcessResult, run_process(), _signal_group(), _stop_tree(), alive(), run(), test_invalid_utf8_and_crlf_are_cleaned_in_the_log(), test_output_cap_cuts_the_log_and_drains_the_process() (+1 more)

### Community 66 - "Community 66"
Cohesion: 0.14
Nodes (6): docstrings(), offending(), test_no_skip_permissions_in_agents_code(), test_the_check_finds_them(), inputs(), worktree()

### Community 67 - "Community 67"
Cohesion: 0.17
Nodes (5): _deps(), edit_command(), list_command(), set_status_command(), show_command()

### Community 68 - "Community 68"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 69 - "Community 69"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, exactOptionalPropertyTypes, isolatedModules, jsx, lib, module, moduleResolution (+9 more)

### Community 70 - "Community 70"
Cohesion: 0.17
Nodes (6): config_path(), default_projects_dir(), default_worktrees_dir(), disabled_hooks_path(), home_dir(), Settings

### Community 71 - "Community 71"
Cohesion: 0.15
Nodes (4): RunRegistry, WorkspaceRuns, test_bus_of_an_empty_database_starts_at_zero(), test_bus_starts_at_the_databases_last_event()

### Community 72 - "Community 72"
Cohesion: 0.27
Nodes (9): fake(), repo(), test_approve_exits_0_and_defaults_to_the_repo(), test_changes_requested_exits_1(), test_dirty_repo_is_refused(), test_errors(), test_not_a_repository(), test_ticket_without_done_when_items() (+1 more)

### Community 73 - "Community 73"
Cohesion: 0.15
Nodes (5): set_identity(), anonymise(), logged_in(), test_real_run_creates_a_file_and_is_denied_python(), test_real_review_names_the_missing_test()

### Community 74 - "Community 74"
Cohesion: 0.25
Nodes (11): checkDaemon(), DaemonCheck, DaemonStatus, deriveStatus(), FAILURES_BEFORE_DOWN, notRunning, DAEMON_STATUS_KEY, DaemonStatusResult (+3 more)

### Community 76 - "Community 76"
Cohesion: 0.21
Nodes (8): _header(), _path(), _split_files(), trim_diff(), file_diff(), test_headers_alone_over_the_limit_still_fit(), test_large_diff_keeps_every_header_and_whole_files(), test_small_diff_is_unchanged()

### Community 77 - "Community 77"
Cohesion: 0.22
Nodes (9): apply_transition(), parse_status(), TransitionResult, copy_dashboard(), test_apply_refused_leaves_the_file_alone(), test_apply_running_is_refused_while_a_file_is_invalid(), test_apply_same_status_writes_nothing(), test_apply_transition_changes_only_the_status_line() (+1 more)

### Community 78 - "Community 78"
Cohesion: 0.19
Nodes (7): parse_done_when(), DoneItem, test_done_when_heading_variants(), test_done_when_ignores_code_fences(), test_done_when_items(), test_empty_done_when_is_a_warning(), test_round_trip_fixture_checklists()

### Community 79 - "Community 79"
Cohesion: 0.22
Nodes (7): test_backends_are_separated_by_a_blank_line(), test_lists_the_installed_backend(), test_not_logged_in_and_not_enforceable(), test_nothing_installed_says_how_to_install(), use(), fake_claude_cmd(), sandbox_which()

### Community 80 - "Community 80"
Cohesion: 0.14
Nodes (14): dependencies, class-variance-authority, clsx, @fontsource/inter, @fontsource/jetbrains-mono, lucide-react, radix-ui, react (+6 more)

### Community 81 - "Community 81"
Cohesion: 0.18
Nodes (5): dotted_path(), format_errors(), _message(), _model_at(), _number()

### Community 82 - "Community 82"
Cohesion: 0.18
Nodes (9): parse_ticket(), read_ticket(), save_ticket(), test_body_is_written_verbatim(), test_defaults_for_optional_fields(), test_flow_mapping_frontmatter_is_re_rendered(), test_parse_ticket_parts(), test_read_missing_file() (+1 more)

### Community 83 - "Community 83"
Cohesion: 0.17
Nodes (9): _id_sort_key(), list_tickets(), test_bad_project_name(), test_dashboard_plan_loads(), test_invalid_files_are_ordered_by_case_sensitive_name(), test_missing_project(), test_project_without_tickets_folder(), test_read_errors_become_invalid_entries() (+1 more)

### Community 84 - "Community 84"
Cohesion: 0.27
Nodes (9): test_create_app_uses_token_file(), test_docs_and_openapi_are_served(), test_foreign_host_header_is_rejected(), test_health_needs_no_token(), test_host_header_must_match_port(), test_unknown_api_route_needs_token(), test_version_with_token_is_200(), test_version_with_wrong_token_is_401() (+1 more)

### Community 86 - "Community 86"
Cohesion: 0.22
Nodes (3): init(), validate_project(), version()

### Community 90 - "Community 90"
Cohesion: 0.47
Nodes (7): add_tickets(), test_invalid_ticket_reports_its_errors(), test_missing_dependency_is_shown(), test_override_error_exits_1(), test_show_prints_the_prompt(), test_show_reports_cuts_and_uses_an_override(), test_unknown_ticket()

### Community 92 - "Community 92"
Cohesion: 0.25
Nodes (3): assert_gone(), Recorder, test_cancel()

### Community 95 - "Community 95"
Cohesion: 0.32
Nodes (3): folders(), test_every_test_folder_has_init(), test_every_test_folder_mirrors_a_package()

### Community 98 - "Community 98"
Cohesion: 0.29
Nodes (7): scripts, build, dev, format, lint, tauri, test

### Community 101 - "Community 101"
Cohesion: 0.47
Nodes (3): policy(), user_home(), worktree()

### Community 102 - "Community 102"
Cohesion: 0.53
Nodes (4): test_no_heading_gives_no_items(), test_open_and_checked_items_keep_their_text(), test_the_section_ends_at_the_next_heading(), texts()

### Community 103 - "Community 103"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 104 - "Community 104"
Cohesion: 0.47
Nodes (3): is_test(), main(), oversized()

## Knowledge Gaps
- **145 isolated node(s):** `CopyState`, `RetryProps`, `DaemonReply`, `RawDaemonInfo`, `description` (+140 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 977 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **81 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorktreeManager` connect `Community 10` to `Community 64`, `Community 4`, `Community 5`, `Community 7`, `Community 8`, `Community 11`, `Community 45`, `Community 47`, `Community 50`, `Community 88`, `Community 29`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `RunLog` connect `Community 9` to `Community 100`, `Community 7`, `Community 71`, `Community 106`, `Community 47`, `Community 48`, `Community 52`, `Community 56`, `Community 24`, `Community 26`, `Community 27`, `Community 30`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `ClaudeCliRunner` connect `Community 40` to `Community 0`, `Community 1`, `Community 73`, `Community 79`, `Community 20`, `Community 23`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `RunLog` (e.g. with `EventBus` and `Attempt`) actually correct?**
  _`RunLog` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `WorktreeManager` (e.g. with `_recover_one()` and `recover_worktrees()`) actually correct?**
  _`WorktreeManager` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ClaudeStreamParser` (e.g. with `ClaudeCliRunner` and `_Session`) actually correct?**
  _`ClaudeStreamParser` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `AgentPolicy` (e.g. with `ClaudeCliRunner` and `build_argv()`) actually correct?**
  _`AgentPolicy` has 8 INFERRED edges - model-reasoned connections that need verification._