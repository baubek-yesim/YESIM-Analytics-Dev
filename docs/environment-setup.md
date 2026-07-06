# Setup: Spark Environment with the MariaDB JDBC driver

Fabric's default Spark runtime does **not** include a MariaDB/MySQL JDBC driver, so
`spark.read.jdbc(...)` fails with `ClassNotFoundException: org.mariadb.jdbc.Driver` until you
put the driver on the Spark classpath. Two ways to do that — a durable Environment (done for
this workspace) and a quick inline fallback.

## Option A — Fabric Environment with the driver jar (recommended, already set up)

This workspace uses an Environment named **`AnalyticsDev_Env`** with the MariaDB Connector/J
jar. Because Environments are Git-tracked, it's already in this repo at
`Fabric/AnalyticsDev_Env.Environment/` (including the jar under
`Libraries/CustomLibraries/mariadb-java-client-3.3.3.jar`). To recreate or update it:

1. **Download the driver** from Maven Central:
   [`mariadb-java-client-3.3.3.jar`](https://repo1.maven.org/maven2/org/mariadb/jdbc/mariadb-java-client/3.3.3/mariadb-java-client-3.3.3.jar).
2. Fabric workspace → **+ New item → Environment** → name it `AnalyticsDev_Env`.
3. In the Environment editor → **Libraries → Custom libraries → Upload** → select the jar.
4. **Publish** (top right) → **Publish all**, and **wait** — publishing takes ~5–15 minutes and
   the Environment isn't usable until it finishes.
5. Attach it to a notebook: open the notebook → **Home** ribbon → **Environment** dropdown →
   select `AnalyticsDev_Env`. (Or set it as the workspace default under
   **Workspace settings → Spark settings → Environment**.)

Once attached, `spark.read.jdbc(..., properties={"driver": "org.mariadb.jdbc.Driver", ...})`
resolves the driver with no per-notebook setup.

## Option B — inline `%%configure` (quick, no Environment)

Add this as the **first cell** of the notebook (it must run before the Spark session starts):

```
%%configure -f
{
    "conf": {
        "spark.jars.packages": "org.mariadb.jdbc:mariadb-java-client:3.3.3"
    }
}
```

It pulls the driver from Maven at session start. Caveats: it must be the first cell; the Spark
pool needs outbound access to Maven Central; and some capacity admins disable session-level
package installs (then Option A is the only path). Prefer Option A for anything durable.

## Verifying the driver is present

Run the JDBC read cell in `Fabric/MariaDB Sample Query.Notebook`. If it connects (or fails on
*connection*/auth rather than `ClassNotFoundException`), the driver is on the classpath. A
`ClassNotFoundException: org.mariadb.jdbc.Driver` means the Environment isn't attached/published
(or the `%%configure` cell wasn't run first).
