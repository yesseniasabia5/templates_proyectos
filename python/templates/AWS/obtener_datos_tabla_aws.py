"""
#================================================== 
Script: obtener_datos_tabla_aws.py
Author: Yessenia Sabia
#==================================================
DynamoDB Table Data Retrieval with AWS IAM Roles Anywhere Authentication
=========================================================================

This module handles the full pipeline for reading all items from an AWS DynamoDB table,
using certificate-based authentication via AWS IAM Roles Anywhere
(no long-lived IAM access keys required).

Workflow:
---------
1. **Authentication** (`obtener_datos_tabla`):
   - Calls `get_session()` from `conexion_aws` to authenticate against AWS Roles Anywhere
     using an X.509 certificate and private key, obtaining short-lived credentials.
   - Calls `assume_role()` to switch into a secondary IAM role (e.g., a cross-account role),
     returning a fully configured boto3 Session.

2. **Full table scan** (`listar_items_dynamodb`):
   - Performs a paginated `Scan` operation over the entire DynamoDB table using
     `ExclusiveStartKey` to handle tables larger than the 1 MB per-page limit.
   - Only retrieves the projected attributes: `external_id`, `reason`, and
     `source_account_number`.
   - Accumulates all pages into a single list and returns it.

3. **DynamoDB deserialization** (`deserializar_item`):
   - Converts each raw DynamoDB item (typed format, e.g. `{"S": "value"}`) into a plain
     Python dictionary using boto3's `TypeDeserializer`.

Key functions:
--------------
- obtener_datos_tabla(nombre_tabla)
      Entry point. Authenticates, assumes the target role, scans the table, and returns
      a list of deserialized Python dictionaries.

- listar_items_dynamodb(session, table_name)
      Paginates through the full DynamoDB table scan and returns all raw items.

- deserializar_item(item)
      Converts a single DynamoDB typed item into a plain Python dict.

Configuration (placeholders in `obtener_datos_tabla`):
------------------------------------------------------
  - certificate_path   : PEM X.509 certificate (string, env var, or secrets manager).
  - private_key_path   : PEM RSA private key (string, env var, or secrets manager).
  - trust_anchor_arn   : ARN of the Roles Anywhere Trust Anchor.
  - profile_arn        : ARN of the Roles Anywhere Profile.
  - role_arn_aws       : ARN of the initial IAM role to obtain via Roles Anywhere.
  - assume_rol_arn     : ARN of the secondary IAM role to assume via STS.
  - region             : AWS region (default: us-east-1).

Dependencies:
-------------
  boto3, AWS.conexion_aws
"""

import logging as log
from AWS.conexion_aws import get_session, assume_role
from botocore.exceptions import BotoCoreError, ClientError
from boto3.dynamodb.types import TypeDeserializer

# Configurar logging
log.basicConfig(level=log.INFO)

# Deserializar DynamoDB a formato Python legible
def deserializar_item(item):
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in item.items()}

# Listar contenido de la tabla DynamoDB
def listar_items_dynamodb(session, table_name):
    dynamodb = session.client("dynamodb", region_name="us-east-1")
    items = []
    start_key = None

    while True:
        params = {
            "TableName": table_name,
            "ProjectionExpression": "external_id, reason,source_account_number",
        }
        if start_key:
            params["ExclusiveStartKey"] = start_key

        response = dynamodb.scan(**params)
        items.extend(response.get("Items", []))

        start_key = response.get("LastEvaluatedKey")
        if not start_key:
            break

    log.info(f"Se recuperaron {len(items)} ítems de la tabla {table_name}.")
    return items


def obtener_datos_tabla(nombre_tabla="prodblue-GuaranteeTransactions"):
    certificate_path = "xxxxxxx" #aca va el certificado de AWS Roles Anywhere, se puede cargar desde un archivo o directamente desde una variable de entorno o secreto
    private_key_path = "xxxxxxx" #aca va la clave privada de AWS Roles Anywhere, se puede cargar desde un archivo o directamente desde una variable de entorno o secreto
    trust_anchor_arn = "xxxxxxx"  #aca va el ARN del Trust Anchor configurado en AWS Roles Anywhere, se puede cargar desde una variable de entorno o secreto
    profile_arn = "xxxxxxx"  #aca va el ARN del Profile configurado en AWS Roles Anywhere, se puede cargar desde una variable de entorno o secreto
    role_arn_aws = "xxxxxxx"  #aca va el ARN del rol de AWS que se desea asumir, se puede cargar desde una variable de entorno o secreto

    region = "us-east-1"
    host = f"rolesanywhere.{region}.amazonaws.com"
    
    # Rol a asumir en la cuenta de destino
    assume_rol_arn = "xxxxxxx"  #aca va el ARN del rol que se desea asumir en la cuenta de destino, se puede cargar desde una variable de entorno o secreto
    session_name = "AssumeRoleSession"
    

    credentials_anywhere = get_session(
        certificate_path, private_key_path, trust_anchor_arn,
        profile_arn, role_arn_aws, host, region
    )

    new_session = assume_role(credentials_anywhere, assume_rol_arn, session_name)

    if new_session:
        log.info("Rol asumido exitosamente.")
        try:
            datos_tabla = listar_items_dynamodb(new_session, nombre_tabla)
            log.info("Item asumido exitosamente.")
            return datos_tabla
        except Exception as e:
            log.error(f"Falló la obtención de ítems: {e}")
            raise
    else:
        log.error("No se pudo asumir el rol.")
        raise

