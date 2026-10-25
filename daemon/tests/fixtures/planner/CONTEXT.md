# Simulation results dashboard

## Goal

Engineers run simulations for every revision of a product and drop the results as CSV files into a shared folder. Today they compare revisions by hand in spreadsheets. Build a small web dashboard that imports those results, checks them against agreed demands and shows how each revision compares with the last.

## Users

Simulation engineers who upload results and review regressions, and team leads who set the demands a result must meet.

## Features

- Import every CSV folder into a database and keep it in sync when files change; report malformed rows with their line numbers instead of dropping them.
- Give each result a pass, warn or fail verdict against its demand.
- A revisions page that lists revisions with their verdicts and drills into one.
- A compare page that puts two revisions side by side as a table and a chart and highlights regressions.
- A demands page to create, edit and delete demands in dialogs.
- Every page copes with empty, partial and malformed data.

## Stack

A FastAPI backend with SQLite and migrations, a React frontend, one repository with `just lint` and `just test`, and CI on every push.

## Done

The team can run the app from the README, the test suite covers the verdict rules and the import, and a maintainer has a handover note.
