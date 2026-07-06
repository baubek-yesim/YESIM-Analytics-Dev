# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "82616a7a-09d3-4b1a-9fe9-c16759f0bcff",
# META       "default_lakehouse_name": "AnalyticsDev_LH",
# META       "default_lakehouse_workspace_id": "dd37b2de-4623-431a-9049-194ff52a8cbb",
# META       "known_lakehouses": [
# META         {
# META           "id": "82616a7a-09d3-4b1a-9fe9-c16759f0bcff"
# META         }
# META       ]
# META     },
# META     "environment": {
# META       "environmentId": "c5de910a-ae3d-8a59-4279-089d862bdd34",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# MARKDOWN ********************

# # MariaDB Sample Query
# 
# Connects to the MariaDB source database over **Spark JDBC** and queries a table, using **Azure Key Vault** for credentials. No secrets are stored in this notebook or in Git.
# 
# **Before running this notebook:**
# 
# 1. Attach an **Environment** with the MariaDB JDBC driver (`org.mariadb.jdbc:mariadb-java-client`) published and attached to this notebook — or use the commented `%%configure` fallback described in the Notes cell at the end.
# 2. Confirm the Azure Key Vault has secrets `mariadb-user` and `mariadb-password`, and that this notebook's identity has `Get` permission on them.
# 3. Confirm the MariaDB host is reachable from Fabric (firewall allowlist for outbound traffic).
# 4. Edit the connection parameters in the next cell to match your database.
# 5. To run the "Land into the Lakehouse" cells further down, create a Fabric Lakehouse and attach it as this notebook's **default lakehouse** first — see `docs/lakehouse-walkthrough.md` in the repo root for a full walkthrough.


# CELL ********************

# Connection parameters (non-secret) — edit these to match your MariaDB instance.
db_host = "168.119.212.162"  # public host or IP
db_port = "3306"
db_name = "analytics_statistics"
source_table = "yesim_signup_info"
key_vault_uri = "https://yesim-analytics-kv.vault.azure.net/"
lakehouse_table = "bronze_mariadb_kay_revenue_upd"  # Delta table name to land data into (needs a default lakehouse attached)

# Optional server-side row filter. This is a plain SELECT condition sent to MariaDB — it is
# read-only and does NOT modify or delete anything in the source. Some source tables contain a
# stray header-style row whose integer columns hold text (e.g. id = 'id'), which breaks Spark's
# integer decoding; keeping only numeric-id rows skips it. It's a no-op on a clean id column.
# Set to None to read the whole table, or change `id` if the offending column is different.
row_filter = "id REGEXP '^-?[0-9]+$'"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Fetch credentials from Azure Key Vault at runtime. Values are never persisted in Git,
# and notebook output automatically redacts secret values (shown as [REDACTED]).
db_user = notebookutils.credentials.getSecret(key_vault_uri, "my-maria-db-user")
db_password = notebookutils.credentials.getSecret(key_vault_uri, "my-maria-db-pass")
print("Fetched MariaDB credentials from Key Vault.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Connect to MariaDB over Spark JDBC and read the target table.
jdbc_url = f"jdbc:mariadb://{db_host}:{db_port}/{db_name}"
connection_properties = {
    "user": db_user,
    "password": db_password,
    "driver": "org.mariadb.jdbc.Driver",
}

# Apply the optional row_filter by wrapping the table in a subquery. Still a plain read —
# nothing in the source database is changed.
if row_filter:
    dbtable = f"(SELECT * FROM {source_table} WHERE {row_filter}) AS src"
else:
    dbtable = source_table

df = spark.read.jdbc(url=jdbc_url, table=dbtable, properties=connection_properties)

print(f"Row count: {df.count()}")
display(df.limit(100))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# (Diagnostic) Which columns did Spark infer as integer? Run after the read cell above.
df.printSchema()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# (Diagnostic) Find non-numeric values in a suspected integer column (pushed down to MariaDB).
# Change `id` to each integer column from printSchema until one returns rows.
probe = "(SELECT id, COUNT(*) AS n FROM {t} WHERE id NOT REGEXP '^-?[0-9]+$' GROUP BY id LIMIT 20) AS p".format(t=source_table)
spark.read.jdbc(url=jdbc_url, table=probe, properties=connection_properties).show(truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Land into the Lakehouse
# 
# The cells below write the MariaDB data into a Delta table in this notebook's **default
# lakehouse**, then read it back with Spark SQL. This requires a Fabric Lakehouse to be
# attached as the default lakehouse first (see prerequisite 5 above) — if none is attached,
# `saveAsTable` fails with a "no default lakehouse" error.
# 
# Only the table's *metadata* (name, schema) is ever tracked in Git via the lakehouse's
# `.platform`/`shortcuts.metadata.json` files — the actual rows live in OneLake and are
# never committed. See `docs/lakehouse-walkthrough.md` for the full create → commit → sync
# lifecycle and a hands-on demonstration of that boundary.

# CELL ********************

# Write the MariaDB result into a Delta table in the attached default Lakehouse.
df.write.mode("overwrite").format("delta").saveAsTable(lakehouse_table)
print(f"Wrote {df.count()} rows to Lakehouse table: {lakehouse_table}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Read the landed table back with Spark SQL, straight from the Lakehouse.
result = spark.sql(f"SELECT * FROM {lakehouse_table} LIMIT 100")
display(result)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Optional patterns — uncomment and adapt as needed.

# 1) Push a filter/aggregation down to MariaDB instead of reading the whole table:
# query = "(SELECT col_a, col_b FROM your_table WHERE col_a > 100) AS filtered"
# df_filtered = spark.read.jdbc(url=jdbc_url, table=query, properties=connection_properties)
# display(df_filtered.limit(100))

# 2) Parallel read for large tables (splits the read across partitions):
# df_parallel = spark.read.jdbc(
#     url=jdbc_url,
#     table=source_table,
#     column="id",
#     lowerBound=1,
#     upperBound=1000000,
#     numPartitions=8,
#     properties=connection_properties,
# )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Notes
# 
# - **Driver delivery:** the recommended path is a Fabric **Environment** with the MariaDB Connector/J jar (Maven `org.mariadb.jdbc:mariadb-java-client:3.3.3`) published and attached to this notebook. If you'd rather not create an Environment, add a first cell with the `%%configure` magic instead:
#   ```
#   %%configure
#   { "conf": { "spark.jars.packages": "org.mariadb.jdbc:mariadb-java-client:3.3.3" } }
#   ```
# - **Security:** credentials are read only from Azure Key Vault via `notebookutils.credentials.getSecret`. Never hardcode a username or password in a cell — Fabric redacts secret values in output, but a literal password typed into a cell is still committed to Git in plain text.
# - **Troubleshooting:** a `ClassNotFoundException` for `org.mariadb.jdbc.Driver` means the Environment isn't attached/published (or the `%%configure` fallback wasn't run first). A connection timeout/refused error means the MariaDB host isn't reachable from Fabric — check the firewall allowlist. A "no default lakehouse" error on `saveAsTable` means no Lakehouse is attached as this notebook's default yet.
# - **`value '...' cannot be decoded as Integer`:** the source table has a malformed row (for example a header row that was imported as data) where an integer column holds text. The `row_filter` in the parameters cell skips it server-side with a read-only `SELECT` — the source is never modified. To eyeball the bad row, run a pushdown query that wraps the integer columns in `CAST(col AS CHAR)`.
# - **Lakehouse data vs. Git:** committing this workspace to Git never uploads or overwrites table data — only item metadata (like the lakehouse's display name and logical ID) is tracked. Each workspace that syncs this repo starts with an *empty* lakehouse and repopulates it by rerunning this notebook. See `docs/lakehouse-walkthrough.md` for the full walkthrough.

