# Walkthrough: create your own Lakehouse and sync it via Git

This is a hands-on walkthrough for creating a Fabric Lakehouse yourself and understanding
exactly what Git sync does (and doesn't) do to it. It ends with the
[`MariaDB Sample Query`](../Fabric/MariaDB%20Sample%20Query.Notebook/notebook-content.py)
notebook landing MariaDB data into your new lakehouse and querying it back.

## Read this first: what does and doesn't sync

Before touching anything, the one fact that matters most:

> **Only lakehouse *metadata* is tracked in Git. Table data is never uploaded, downloaded, or
> overwritten by Git or deployment operations.**

| Tracked in Git | Never tracked (data always preserved) |
|---|---|
| Display name, description, logical GUID (`.platform`) | Tables — Delta and non-Delta |
| SQL analytics endpoint metadata | Spark views |
| OneLake shortcut definitions (`shortcuts.metadata.json`) | Folders in the **Files** section |
| Tracking config (`alm.settings.json`) | |
| OneLake security data access roles, preview (`data-access-roles.json`) | |

Source: [Lakehouse Git integration and deployment pipelines](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-git-deployment-pipelines).

Practically, this means "syncing a lakehouse" syncs an **empty container** plus its
metadata. If you connect a second workspace to this repo, *Update from Git* creates a
lakehouse with the same name/GUID — but with no tables in it. Data has to be (re)produced by
running a notebook or pipeline in that workspace.

## Step 1 — Create the lakehouse in the Fabric UI

Creating it in the UI (rather than hand-authoring files in Git) is the reliable path: Fabric
generates a correct `.platform` for you, so you don't hit the "corrupted files" import error
that hand-authored items can trigger if metadata is malformed.

1. In the **YESIM Analytics Dev** workspace, select **+ New item → Lakehouse**.
2. Name it something recognizable, e.g. `AnalyticsDev_LH`, and create it.
3. Fabric automatically provisions a **SQL analytics endpoint** and a **default semantic
   model** alongside the lakehouse — you'll see all three in the workspace item list.

## Step 2 — Commit it to Git

1. Open **Source control** in the workspace. The new lakehouse (and its endpoint/semantic
   model, if you've enabled tracking for them) shows up as an uncommitted change.
2. Review the change, then **Commit**.
3. Back in this repo, `git pull origin dev` — you should now see a new folder:
   ```
   Fabric/AnalyticsDev_LH.Lakehouse/
   ├── .platform
   └── (shortcuts.metadata.json / alm.settings.json if applicable)
   ```
4. Open `.platform` and note the `logicalId` — this is the real, Fabric-generated GUID that
   ties this Git folder to the lakehouse object across workspaces. Compare it with how we had
   to fix the notebook's `.platform` by hand (see the git history on this repo) — creating in
   the UI sidesteps that whole class of mistake.

## Step 3 — Attach it to the MariaDB notebook

1. Open the **MariaDB Sample Query** notebook.
2. In the notebook's **Explorer** panel, add your lakehouse and set it as the **default
   lakehouse**. This is what lets `saveAsTable(...)` in the notebook resolve to your
   lakehouse without you specifying an ID anywhere in the code.
3. Commit again from **Source control**. You'll see the notebook's `.platform`/content
   metadata update (the lakehouse's *physical* ID is replaced by its *logical* ID) — this is
   expected and is how the binding survives being synced to a different workspace later.

## Step 4 — Ingest and query

1. Fill in the connection-parameters cell in the notebook (MariaDB host/port/db/table, Key
   Vault URI) if you haven't already, per `Fabric/Readme.md`.
2. **Run all.** In order, the notebook:
   - reads the MariaDB table over Spark JDBC,
   - writes it as a Delta table (`bronze_mariadb` by default) into your lakehouse,
   - reads that table back with `spark.sql`.
3. Open the lakehouse and check the **Tables** section — `bronze_mariadb` is there, backed by
   real Parquet/Delta files in OneLake.

## Step 5 — Prove the metadata/data boundary yourself

1. Go back to **Source control** in the workspace and look at what's pending.
2. You should see **no pending change for the new table** — creating `bronze_mariadb` did not
   touch anything trackable in Git. If you commit now, the diff (if any) is limited to things
   like lakehouse or notebook metadata — never the table's rows.
3. This is the payoff of Step 1's warning: Git is tracking the *shape* of your workspace, not
   its data.

## Reproducing this in another workspace

1. Connect a fresh Fabric workspace to this same `dev` branch / `Fabric/` folder.
2. **Update from Git** — `AnalyticsDev_LH` appears, but empty (no `bronze_mariadb` table yet).
3. Re-attach the lakehouse as the notebook's default (Step 3) and **Run all** again — the
   notebook reproduces the table from the live MariaDB source. This is exactly the pattern
   CI/CD and deployment pipelines rely on: Git carries structure, notebooks/pipelines carry
   data reproduction.

## See also

- [`Fabric/Readme.md`](../Fabric/Readme.md) — item inventory and one-time setup for this workspace.
- [`README.md`](../README.md) — overall branch strategy and Git ↔ Fabric round-trip.
- [Lakehouse Git integration and deployment pipelines](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-git-deployment-pipelines) (Microsoft Learn).
