# Python Integration Templates

A collection of reusable Python templates for integrating with **AWS** cloud services and **Slack**, built for production workloads. These templates were developed during real-world projects and are designed to be dropped into any Python application with minimal configuration.

---

## Repository Structure

```
templates_proyectos/
└── python/
    └── templates/
        ├── AWS/          # AWS authentication and data retrieval templates
        │   ├── conexion_aws.py
        │   ├── obtener_datos_bucket_aws.py
        │   ├── obtener_datos_tabla_aws.py
        │   └── README.md
        │
        └── Slack/        # Slack bot and interactive UI templates
            ├── slack_bot.py
            ├── modal_slack.py
            ├── publicar_datos_home_slack.py
            └── README.md
```

---

## Modules

### AWS — IAM Roles Anywhere + S3 + DynamoDB

Certificate-based authentication for workloads running **outside of AWS** (on-premises, CI/CD pipelines), using **IAM Roles Anywhere** and AWS Signature Version 4 — no long-lived access keys required.

| Template | What it does |
|----------|-------------|
| `conexion_aws.py` | Authenticates via X.509 certificate + SigV4, obtains short-lived AWS credentials, and optionally assumes a cross-account IAM role. |
| `obtener_datos_bucket_aws.py` | Finds a date-partitioned file in S3, downloads the ZIP, and returns all CSVs inside as a pandas DataFrame. |
| `obtener_datos_tabla_aws.py` | Performs a full paginated scan of a DynamoDB table and returns all items as Python dicts. |

→ [AWS README](python/templates/AWS/README.md)

---

### Slack — Interactive Bot with Socket Mode

A fully interactive Slack bot that connects via **WebSocket (Socket Mode)**, sends messages with interactive buttons, opens modals to collect user input, and publishes results to the **Slack Home Tab**.

| Template | What it does |
|----------|-------------|
| `slack_bot.py` | Core bot class. Manages Socket Mode connection, handles events, button clicks, and modal submissions. |
| `modal_slack.py` | Defines the Block Kit modal structure (date pickers + numeric input fields). |
| `publicar_datos_home_slack.py` | Formats processing results as a text table and publishes them to the user's Home Tab. |

→ [Slack README](python/templates/Slack/README.md)

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![AWS](https://img.shields.io/badge/AWS-boto3-orange?logo=amazonaws)
![Slack](https://img.shields.io/badge/Slack-SDK-4A154B?logo=slack)

| Technology | Usage |
|------------|-------|
| Python 3.10+ | Core language |
| boto3 | AWS SDK |
| slack-sdk | Slack Web API + Socket Mode |
| cryptography | X.509 certificate handling and RSA signing |
| pandas | CSV/DataFrame processing |
| requests | HTTP calls to AWS Roles Anywhere |

---

## Key Design Decisions

- **No long-lived credentials** — AWS authentication is handled entirely via X.509 certificates and IAM Roles Anywhere, following the same security model as EC2 instance profiles.
- **Secrets-first** — all sensitive values (tokens, certificates, ARNs) are loaded from environment variables or a secrets manager. Nothing is hardcoded.
- **In-memory processing** — S3 ZIP files are downloaded and parsed entirely in memory, with no disk I/O.
- **Real-time Slack interaction** — Socket Mode avoids the need for a public HTTP endpoint, making the bot suitable for internal or air-gapped environments.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/templates_proyectos.git
```

### 2. Install dependencies

```bash
pip install boto3 slack-sdk cryptography pandas requests
```

### 3. Set environment variables

```bash
# AWS
export CERT="-----BEGIN CERTIFICATE-----\n..."
export PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
export TRUST_ANCHOR_ARN="arn:aws:rolesanywhere:..."
export PROFILE_ARN="arn:aws:rolesanywhere:..."
export ROLE_ARN="arn:aws:iam::..."
export ASSUME_ROLE_ARN="arn:aws:iam::..."

# Slack
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_APP_TOKEN="xapp-..."
export CHANNEL_ID="C0123456789"
```

### 4. Use any template independently

```python
# Example: authenticate to AWS and read a DynamoDB table
from python.templates.AWS.obtener_datos_tabla_aws import obtener_datos_tabla

items = obtener_datos_tabla(nombre_tabla="my-table")
```

---

## Author

**Yessenia Sabia**
