# Setup: Azure Key Vault for the MariaDB credentials

The notebooks never store the MariaDB username/password in code. They fetch them at runtime
with `notebookutils.credentials.getSecret(vaultUri, secretName)`, which reads from an Azure
Key Vault. This is a one-time setup.

## How Fabric authenticates to Key Vault (read this first)

`getSecret` authenticates as the **notebook owner's** Microsoft Entra identity — the account
that owns the notebook item in the Fabric workspace (your `@yesim.app` account). Fabric does
not yet support workspace identities with `notebookutils`, so that owner account is what needs
read access to the secrets.

> **The #1 gotcha:** being *Owner* of the Key Vault does **not** let you read or create
> secrets. With the RBAC permission model, ownership is management-plane only. You must
> explicitly assign a **secrets** role (data-plane). This is why a brand-new vault shows
> *"The operation is not allowed by RBAC / You are unauthorized to view these contents"* on
> the Secrets page.

## Step 1 — Create the Key Vault

1. [portal.azure.com](https://portal.azure.com) → search **Key vaults** → **Create**.
2. **Basics:** resource group, a globally-unique **name** (this workspace uses
   `yesim-analytics-kv`), **region West Europe** (matches the Fabric capacity), tier Standard.
3. **Access configuration** → Permission model → **Azure role-based access control (RBAC)**.
4. **Review + create** → **Create**.
5. Open the vault → **Overview** → copy the **Vault URI**
   (`https://yesim-analytics-kv.vault.azure.net/`). This is the `key_vault_uri` in the notebook.

## Step 2 — Grant yourself a secrets role (fixes "unauthorized")

1. Vault → **Access control (IAM)** → **+ Add → Add role assignment**.
2. **Role:** **Key Vault Secrets Officer** (create/read/update/delete secrets). *Read-only*
   consumers need only **Key Vault Secrets User** — but since the notebook runs as your
   account, Officer covers both creating and reading.
3. **Members:** *User, group, or service principal* → select **your own `@yesim.app` account**.
4. **Review + assign**.
5. **Wait 2–5 minutes** for the assignment to propagate, then refresh the Secrets page. (If it
   stays unauthorized, sign out of the portal and back in so your token picks up the new role.)

## Step 3 — Add the secrets

1. Vault → **Objects → Secrets → + Generate/Import**.
2. Upload options **Manual**, Name **`mariadb-user`**, value = the MariaDB username → **Create**.
3. Repeat: Name **`mariadb-password`**, value = the MariaDB password.

Secret names must match the notebook **exactly** (`mariadb-user`, `mariadb-password`).

## Step 4 — Grant the notebook owner read access (if a different account)

If the account that owns the notebook in Fabric is **not** the account you used above, assign
that account **Key Vault Secrets User** as well (same flow as Step 2). Otherwise skip — your
Officer role already grants read.

## Step 5 — Network access

Vault → **Networking**. Default **Allow public access from all networks** works with Fabric.
If the vault is locked down, enable **Allow trusted Microsoft services to bypass this firewall**.

## Step 6 — Point the notebook at the vault and test

In `Fabric/MariaDB Sample Query.Notebook`, the connection-parameters cell is already set to:

```python
key_vault_uri = "https://yesim-analytics-kv.vault.azure.net/"
```

Run the "Fetch credentials from Azure Key Vault" cell. Success prints
`Fetched MariaDB credentials from Key Vault.` (the values display as `[REDACTED]`).

## Troubleshooting

| Error | Cause / fix |
|---|---|
| Portal: *"operation not allowed by RBAC" / "unauthorized to view contents"* | You have no secrets role yet — Step 2 (Officer). Wait for propagation. |
| Notebook: `403 Forbidden` / "caller is not authorized" | The **notebook owner** account lacks **Key Vault Secrets User/Officer**, or the role hasn't propagated. |
| Notebook: `404 SecretNotFound` | Secret name typo, or wrong Vault URI. |
| Notebook: timeout / connection refused | Vault firewall — Step 5. |
