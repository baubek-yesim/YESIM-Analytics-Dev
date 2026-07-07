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
# META     }
# META   }
# META }

# MARKDOWN ********************

# # mariadb_utils
# 
# Shared MariaDB connection helpers for this workspace. Don't run this notebook directly — load it from another notebook with:
# 
# ```
# %run mariadb_utils
# ```
# 
# After that, the functions below are available in the calling notebook's session, e.g.:
# 
# ```
# df = read_mariadb_table(
#     host="your-mariadb-host.example.com",
#     database="your_database",
#     table="your_table",
#     key_vault_uri="https://your-keyvault.vault.azure.net/",
# )
# ```
# 
# Requirements in the *calling* notebook's session: the MariaDB JDBC driver on the Spark classpath (Environment with `org.mariadb.jdbc:mariadb-java-client`, or the `%%configure` fallback) and `Get` access to the Key Vault secrets `mariadb-user` / `mariadb-password`.

# CELL ********************

MARIADB_DRIVER = "org.mariadb.jdbc.Driver"
DEFAULT_PORT = "3306"
USER_SECRET_NAME = "mariadb-user"
PASSWORD_SECRET_NAME = "mariadb-password"


def get_mariadb_credentials(key_vault_uri, user_secret=USER_SECRET_NAME, password_secret=PASSWORD_SECRET_NAME):
    """Fetch MariaDB credentials from Azure Key Vault at runtime.

    Returns a (user, password) tuple. Values are never persisted; Fabric
    redacts secret values in notebook output.
    """
    user = notebookutils.credentials.getSecret(key_vault_uri, user_secret)
    password = notebookutils.credentials.getSecret(key_vault_uri, password_secret)
    return user, password


def mariadb_jdbc_url(host, database, port=DEFAULT_PORT):
    """Build the JDBC URL for a MariaDB host/database."""
    return f"jdbc:mariadb://{host}:{port}/{database}"


def mariadb_connection_properties(user, password):
    """Build the JDBC connection-properties dict expected by spark.read.jdbc."""
    return {
        "user": user,
        "password": password,
        "driver": MARIADB_DRIVER,
    }

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def read_mariadb_table(host, database, table, key_vault_uri, port=DEFAULT_PORT):
    """Read a full MariaDB table into a Spark DataFrame.

    Credentials are fetched from Key Vault; nothing sensitive is stored in code.
    """
    user, password = get_mariadb_credentials(key_vault_uri)
    return spark.read.jdbc(
        url=mariadb_jdbc_url(host, database, port),
        table=table,
        properties=mariadb_connection_properties(user, password),
    )


def read_mariadb_query(host, database, query, key_vault_uri, port=DEFAULT_PORT, alias="q"):
    """Push a SQL query down to MariaDB and read the result into a Spark DataFrame.

    `query` is any valid MariaDB SELECT; it runs on the database server, so
    filters/aggregations don't require pulling the whole table into Spark.
    """
    user, password = get_mariadb_credentials(key_vault_uri)
    return spark.read.jdbc(
        url=mariadb_jdbc_url(host, database, port),
        table=f"({query}) AS {alias}",
        properties=mariadb_connection_properties(user, password),
    )


def snapshot_mariadb_table(host, database, table, key_vault_uri, lakehouse_table, port=DEFAULT_PORT, mode="overwrite"):
    """Read a MariaDB table and land it as a Delta table in the default Lakehouse.

    Requires a default lakehouse attached to the calling notebook. Returns the
    DataFrame that was written.
    """
    df = read_mariadb_table(host, database, table, key_vault_uri, port)
    # overwriteSchema=true (overwrite mode only) replaces the table's schema so a stale column
    # type from a prior run can't reject the current all-STRING read. Not valid for append mode.
    writer = df.write.mode(mode).format("delta")
    if mode == "overwrite":
        writer = writer.option("overwriteSchema", "true")
    writer.saveAsTable(lakehouse_table)
    print(f"Wrote {df.count()} rows to Lakehouse table: {lakehouse_table}")
    return df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Notes
# 
# - This is the workspace's "shared py file" pattern: logic lives in a notebook so it's versioned in Git (as `notebook-content.py`) and loaded into other notebooks with `%run mariadb_utils`. Files placed in a Lakehouse's **Files** section are *not* tracked by Git, which is why shared code shouldn't live there.
# - Keep all credential access inside `get_mariadb_credentials` — never accept or hardcode a literal password.
# - If you rename this notebook, update every `%run mariadb_utils` call site (`%run` resolves by notebook display name within the workspace).
