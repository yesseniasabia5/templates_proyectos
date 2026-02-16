# AWS Integration Templates — IAM Roles Anywhere

Reusable Python templates for authenticating against AWS services using **IAM Roles Anywhere** and X.509 certificates, with no long-lived IAM access keys required.

These templates are designed for workloads running **outside of AWS** (on-premises servers, CI/CD pipelines, external services) that need secure, short-lived access to AWS resources.

---

## Architecture Overview

```
X.509 Certificate + Private Key
         │
         ▼
  AWS IAM Roles Anywhere          ← SigV4 signed request with certificate
  (get_session)
         │
         ▼
  Short-lived credentials (1h)
         │
         ▼
  AWS STS AssumeRole               ← Optional: switch to a cross-account role
  (assume_role)
         │
         ▼
  boto3 Session  ──► S3 / DynamoDB / ...
```

---

## Files

| File | Description |
|------|-------------|
| `conexion_aws.py` | Core authentication module. Handles SigV4 signing and Roles Anywhere session creation. |
| `obtener_datos_bucket_aws.py` | Downloads a date-partitioned ZIP from S3 and returns its CSV contents as a pandas DataFrame. |
| `obtener_datos_tabla_aws.py` | Performs a full paginated scan of a DynamoDB table and returns deserialized Python dicts. |

---

## Requirements

```bash
pip install boto3 requests cryptography pandas
```

---

## Configuration

All sensitive values are passed as parameters (no hardcoded secrets). The recommended approach is to load them from environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.).

| Parameter | Description |
|-----------|-------------|
| `certificate_path` | PEM-encoded X.509 certificate (string) |
| `private_key_path` | PEM-encoded RSA private key (string) |
| `trust_anchor_arn` | ARN of the Roles Anywhere Trust Anchor |
| `profile_arn` | ARN of the Roles Anywhere Profile |
| `role_arn_aws` | ARN of the IAM role to obtain via Roles Anywhere |
| `assume_rol_arn` | ARN of the secondary IAM role to assume via STS |
| `region` | AWS region (e.g. `us-east-1`) |

---

## Usage

### 1. Authenticate and get a boto3 session

```python
from AWS.conexion_aws import get_session, assume_role

credentials = get_session(
    certificate_path=os.environ["CERT"],
    private_key_path=os.environ["PRIVATE_KEY"],
    trust_anchor_arn=os.environ["TRUST_ANCHOR_ARN"],
    profile_arn=os.environ["PROFILE_ARN"],
    role_arn_aws=os.environ["ROLE_ARN"],
    host="rolesanywhere.us-east-1.amazonaws.com",
    region="us-east-1"
)

session = assume_role(credentials, assume_rol_arn=os.environ["ASSUME_ROLE_ARN"], session_name="MySession")
```

### 2. Download a date-partitioned ZIP from S3

```python
from AWS.obtener_datos_bucket_aws import descargar_contenido_archivo

df = descargar_contenido_archivo(
    fecha="2024-01-15",
    bucket_name="my-bucket",
    carpeta="reports"
)
print(df.head())
```

### 3. Read all items from a DynamoDB table

```python
from AWS.obtener_datos_tabla_aws import obtener_datos_tabla

items = obtener_datos_tabla(nombre_tabla="my-table")
for item in items:
    print(item)
```

---

## Key Concepts

**IAM Roles Anywhere** allows external workloads to exchange a trusted X.509 certificate for temporary AWS credentials, following the same security model as EC2 instance profiles — without requiring AWS infrastructure.

**SigV4 (Signature Version 4)** is AWS's request signing protocol. This implementation builds the canonical request and signs it manually using the private key, without relying on the AWS CLI helper (`aws_signing_helper`).

---

## Security Notes

- Never hardcode certificates, private keys, or ARNs in source code.
- Credentials obtained via Roles Anywhere expire after 1 hour (configurable up to 12h).
- Use IAM policies with least-privilege on both the Roles Anywhere profile and the assumed role.

---

## References

- [AWS IAM Roles Anywhere Documentation](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/)
- [AWS Signature Version 4](https://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
