# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # MariaDB Sample Query
#
# Connects to the MariaDB source database over **Spark JDBC** and queries a table, using **Azure Key Vault** for credentials. No secrets are stored in this notebook or in Git.
#
# **Before running this notebook:**
# 1. Attach an **Environment** with the MariaDB JDBC driver (`org.mariadb.jdbc:mariadb-java-client`) published and attached to this notebook — or use the commented `%%configure` fallback described in the Notes cell at the end.
# 2. Confirm the Azure Key Vault has secrets `mariadb-user` and `mariadb-password`, and that this notebook's identity has `Get` permission on them.
# 3. Confirm the MariaDB host is reachable from Fabric (firewall allowlist for outbound traffic).
# 4. Edit the connection parameters in the next cell to match your database.

# CELL ********************

# Connection parameters (non-secret) — edit these to match your MariaDB instance.
db_host = "your-mariadb-host.example.com"  # public host or IP
db_port = "3306"
db_name = "your_database"
source_table = "your_table"
key_vault_uri = "https://your-keyvault.vault.azure.net/"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Fetch credentials from Azure Key Vault at runtime. Values are never persisted in Git,
# and notebook output automatically redacts secret values (shown as [REDACTED]).
db_user = notebookutils.credentials.getSecret(key_vault_uri, "mariadb-user")
db_password = notebookutils.credentials.getSecret(key_vault_uri, "mariadb-password")
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

df = spark.read.jdbc(url=jdbc_url, table=source_table, properties=connection_properties)

print(f"Row count: {df.count()}")
display(df.limit(100))

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

# 3) Persist a snapshot into a Fabric Lakehouse (requires a default Lakehouse attached):
# df.write.mode("overwrite").format("delta").saveAsTable("mariadb_snapshot")

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
# - **Troubleshooting:** a `ClassNotFoundException` for `org.mariadb.jdbc.Driver` means the Environment isn't attached/published (or the `%%configure` fallback wasn't run first). A connection timeout/refused error means the MariaDB host isn't reachable from Fabric — check the firewall allowlist.
