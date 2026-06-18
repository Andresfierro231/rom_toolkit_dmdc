# TAMU Dated Folder Executive Summary

Root: `../tamu_loop_data_25_mayo/Loop Operational Data`

## Scope

This summary focuses on top-level dated folders and highlights the main structural differences between them.

## Dated Folder Comparison

| folder | case_dirs | recursive_files | metadata_status | heater_W | air_flow_Lpm |
| --- | --- | --- | --- | --- | --- |
| `2024_03_13` | 3 | 19 | repaired=3 | 448 | 41 |
| `2024_05_04` | 7 | 43 | repaired=7 | 201 to 453 | 37 |
| `2024_09_30` | 0 | 11 | none | n/a | n/a |
| `2025_01_01_(ExampleFolder)` | 2 | 13 | valid=2 | 150 | n/a |
| `2025_03_19` | 7 | 43 | repaired=7 | 150 | 100 to 200 |
| `2025_05_20` | 4 | 25 | repaired=4 | 317 to 328 | 25 to 75 |
| `2025_06_19` | 17 | 124 | repaired=17 | 200 to 402 | 30 to 45 |
| `2025_12_30` | 5 | 11 | valid=5 | 355 to 430 | 21 to 63 |

## Folder Notes

### 2024_03_13

- Case-like subfolders: 3
- Recursive files: 19 across 3 nested directories
- Metadata status: repaired=3
- Recursive file mix: `.csv` x 12, `.json` x 3, `.mat` x 3, `.txt` x 1, `.xlsx` x 0
- Heater-power range: 448 W
- Air-flow range: 41 L/min
- Direct subfolders: `1`, `2`, `3`
- Direct files: `TestFile03132024.txt`

### 2024_05_04

- Case-like subfolders: 7
- Recursive files: 43 across 7 nested directories
- Metadata status: repaired=7
- Recursive file mix: `.csv` x 28, `.json` x 7, `.mat` x 7, `.txt` x 1, `.xlsx` x 0
- Heater-power range: 201 to 453 W
- Air-flow range: 37 L/min
- Direct subfolders: `1`, `2`, `3`, `4`, `5`, `6`, `7`
- Direct files: `TestFile05042024.txt`

### 2024_09_30

- Case-like subfolders: 0
- Recursive files: 11 across 0 nested directories
- Metadata status: none
- Recursive file mix: `.csv` x 0, `.json` x 0, `.mat` x 9, `.txt` x 1, `.xlsx` x 1
- No case-like subfolders were detected by the metadata/CSV heuristic.
- Direct files: `09302024_NC1_TransientWorkspace.mat`, `09302024_NC2_TransientWorkspace.mat`, `09302024_NC3_TransientWorkspace.mat`, `09302024_NC4_TransientWorkspace.mat`, `09302024_NC5_TransientWorkspace.mat`, `09302024_NC6_TransientWorkspace.mat`, `09302024_NC7_TransientWorkspace.mat`, `09302024_NC8_TransientWorkspace.mat`, `09302024_NC9_TransientWorkspace.mat`, `Bubble Data.xlsx`, `TestFile09302024.txt`

### 2025_01_01_(ExampleFolder)

- Case-like subfolders: 2
- Recursive files: 13 across 2 nested directories
- Metadata status: valid=2
- Recursive file mix: `.csv` x 8, `.json` x 2, `.mat` x 2, `.txt` x 1, `.xlsx` x 0
- Heater-power range: 150 W
- Air-flow range: n/a
- Direct subfolders: `0001`, `0002`
- Direct files: `Notes.txt`

### 2025_03_19

- Case-like subfolders: 7
- Recursive files: 43 across 7 nested directories
- Metadata status: repaired=7
- Recursive file mix: `.csv` x 28, `.json` x 7, `.mat` x 7, `.txt` x 1, `.xlsx` x 0
- Heater-power range: 150 W
- Air-flow range: 100 to 200 L/min
- Direct subfolders: `1`, `2`, `3`, `4`, `5`, `6`, `7`
- Direct files: `03192025_Water1.txt`

### 2025_05_20

- Case-like subfolders: 4
- Recursive files: 25 across 4 nested directories
- Metadata status: repaired=4
- Recursive file mix: `.csv` x 16, `.json` x 4, `.mat` x 4, `.txt` x 1, `.xlsx` x 0
- Heater-power range: 317 to 328 W
- Air-flow range: 25 to 75 L/min
- Direct subfolders: `1`, `2`, `3`, `4`
- Direct files: `TestFile05202025.txt`

### 2025_06_19

- Case-like subfolders: 17
- Recursive files: 124 across 17 nested directories
- Metadata status: repaired=17
- Recursive file mix: `.csv` x 71, `.json` x 17, `.mat` x 34, `.txt` x 2, `.xlsx` x 0
- Heater-power range: 200 to 402 W
- Air-flow range: 30 to 45 L/min
- Direct subfolders: `1`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `2`, `3`, `4` (+5 more)
- Direct files: `PIVuncertainty_Mag.csv`, `PIVuncertainty_U.csv`, `PIVuncertainty_V.csv`, `Summaries.txt`, `TestFile06192025.txt`

### 2025_12_30

- Case-like subfolders: 5
- Recursive files: 11 across 5 nested directories
- Metadata status: valid=5
- Recursive file mix: `.csv` x 0, `.json` x 5, `.mat` x 5, `.txt` x 1, `.xlsx` x 0
- Heater-power range: 355 to 430 W
- Air-flow range: 21 to 63 L/min
- Direct subfolders: `1`, `2`, `3`, `4`, `5`
- Direct files: `TestFile12302025.txt`

## Additional Non-Dated Top-Level Folders

| folder | case_dirs | recursive_files |
| --- | --- | --- |
| `Jadyn_runs` | 8 | 39 |
