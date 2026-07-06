# Fabric

This folder is the Git root that the **YESIM Analytics Dev** Fabric workspace is synced to
(on the `dev` branch). Every Fabric item (notebook, lakehouse, environment, etc.) lives in
its own subfolder here, named `<Display Name>.<Item Type>` (for example
`MariaDB Sample Query.Notebook/`), containing a `.platform` metadata file plus the item's
content file(s). These subfolders are managed by Fabric's Git integration — don't rename
them by hand unless you also update any dependent items' references.

## Items in this folder

### `MariaDB Sample Query.Notebook`

A PySpark notebook that connects to the MariaDB source database over Spark JDBC and queries
a table, using Azure Key Vault for credentials (nothing sensitive is stored in Git).

**One-time setup before running it** (each has a dedicated step-by-step guide):

1. **Driver** — a Spark Environment with the MariaDB JDBC driver on the classpath.
   See [`docs/environment-setup.md`](../docs/environment-setup.md). This workspace uses
   `AnalyticsDev_Env` (already created and Git-tracked).
2. **Key Vault** — an Azure Key Vault holding `mariadb-user` / `mariadb-password`, with the
   notebook owner granted a secrets role. See [`docs/keyvault-setup.md`](../docs/keyvault-setup.md).
   This workspace uses `https://yesim-analytics-kv.vault.azure.net/` (already set in the notebook).
3. **Network** — make sure the MariaDB host allows inbound connections from Fabric
   (firewall allowlist).
4. Open the notebook, set the remaining connection parameters (host/port/database/table) to
   match your instance, then **Run all**.

### `mariadb_utils.Notebook`

Shared MariaDB connection helpers (Key Vault credentials + Spark JDBC): this is the
workspace's "shared py file" pattern. Code in a Lakehouse's **Files** section isn't tracked
by Git, so reusable logic lives in this notebook instead — versioned as
`notebook-content.py` and loaded into any other notebook with:

```
%run mariadb_utils
df = read_mariadb_table(host=..., database=..., table=..., key_vault_uri=...)
```

Helpers: `get_mariadb_credentials`, `mariadb_jdbc_url`, `mariadb_connection_properties`,
`read_mariadb_table`, `read_mariadb_query` (SQL pushdown), and `snapshot_mariadb_table`
(land a table into the default Lakehouse as Delta). Same prerequisites as the sample
notebook: JDBC driver on the classpath and Key Vault access in the *calling* notebook's
session.

### Your Lakehouse

The `MariaDB Sample Query` notebook can land data into a Lakehouse you create yourself
(separate from any lakehouse your data-analytics head has set up, like `Testing_Lakehouse`).
Creating and syncing a lakehouse works differently from a notebook: **only its metadata
(name, GUID, shortcuts) is tracked in Git — table data never is.** For the full step-by-step
(create in the UI → commit → attach to the notebook → ingest → verify what did/didn't sync),
see [`docs/lakehouse-walkthrough.md`](../docs/lakehouse-walkthrough.md).

## Syncing changes

- **Git → Fabric:** commit and push changes on `dev`, then in the Fabric workspace go to
  **Source control** and select **Update from Git**.
- **Fabric → Git:** edits made in the Fabric web UI can be committed back to this branch
  from the same **Source control** panel.

See the repository root [README.md](../README.md) for the overall branch strategy.