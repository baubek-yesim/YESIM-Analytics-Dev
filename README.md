# YESIM-Analytics-Dev

This repository is the **Git integration backing for the YESIM Analytics Dev Microsoft
Fabric workspace**. Fabric items (notebooks, lakehouses, environments, etc.) are version
controlled here and kept in sync with the Fabric workspace via Fabric's built-in Git
integration.

## Branch strategy

- **`dev`** — connected to the Fabric workspace's Git integration, with `Fabric/` as the
  workspace root directory. This is where day-to-day Fabric development happens: items
  edited in the Fabric web UI are committed here, and changes authored directly in Git
  (e.g. a new notebook) are pulled into the workspace from here.
- **`main`** — promotion target once changes on `dev` are validated.

## Repository layout

- `Fabric/` — the Fabric workspace's Git root. See [`Fabric/Readme.md`](Fabric/Readme.md)
  for the item inventory and one-time setup steps for each item.

## Git ↔ Fabric round-trip

1. **Author in Git:** add/edit files under `Fabric/` following Fabric's
   [item folder format](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format)
   (`<Display Name>.<Item Type>/` folder with a `.platform` file), commit, and push to `dev`.
2. **Pull into Fabric:** in the Fabric workspace, open **Source control** and select
   **Update from Git** — new/changed items appear in the workspace.
3. **Edit in Fabric:** conversely, changes made in the Fabric web UI can be committed back
   to `dev` from the same **Source control** panel.

## Security note

Database credentials and other secrets are **never committed to this repository**. Fabric
notebooks that need credentials (for example, to connect to the MariaDB source database)
fetch them at runtime from **Azure Key Vault** via `notebookutils.credentials.getSecret`.
See `Fabric/Readme.md` for the required one-time Key Vault setup.