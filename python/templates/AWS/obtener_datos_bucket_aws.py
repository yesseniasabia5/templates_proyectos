"""
#================================================== 
Script: obtener_datos_bucket_aws.py
Author: Yessenia Sabia
#==================================================
S3 Data Retrieval with AWS IAM Roles Anywhere Authentication
=============================================================

This module handles the full pipeline for downloading and reading data files from an
AWS S3 bucket, using certificate-based authentication via AWS IAM Roles Anywhere
(no long-lived IAM access keys required).

Workflow:
---------
1. **Authentication** (`descargar_contenido_archivo`):
   - Calls `get_session()` from `conexion_aws` to authenticate against AWS Roles Anywhere
     using an X.509 certificate and private key, obtaining short-lived credentials.
   - Calls `assume_role()` to switch into a second IAM role (e.g., a cross-account role),
     returning a fully configured boto3 Session.

2. **File discovery by date** (`obtener_archivo_por_fecha`):
   - Lists objects in the target S3 bucket under a prefix built as `{folder}/{date}/`.
   - Returns the S3 key of the first matching object, or raises `FileNotFoundError` if
     no file exists for the given date.

3. **ZIP extraction and CSV parsing** (`leer_zip_s3`):
   - Downloads the ZIP file from S3 entirely into memory (no disk I/O).
   - Iterates over all entries inside the ZIP, reads every `.csv` file as a pandas
     DataFrame (all columns as strings to preserve formatting).
   - Concatenates all DataFrames into a single one and returns it.
   - Returns `None` if no CSV files are found inside the ZIP.

Key functions:
--------------
- descargar_contenido_archivo(fecha, bucket_name, carpeta)
      Entry point. Authenticates, locates the file for the given date, and returns
      a consolidated pandas DataFrame with the CSV contents.

- obtener_archivo_por_fecha(session, bucket_name, carpeta, fecha_objetivo)
      Finds the S3 key of the file matching the target date prefix.

- leer_zip_s3(session, bucket_name, key)
      Downloads a ZIP from S3 and returns a concatenated DataFrame of all CSVs inside.

Configuration (placeholders in `descargar_contenido_archivo`):
--------------------------------------------------------------
  - certificate_path   : PEM X.509 certificate (string, env var, or secrets manager).
  - private_key_path   : PEM RSA private key (string, env var, or secrets manager).
  - trust_anchor_arn   : ARN of the Roles Anywhere Trust Anchor.
  - profile_arn        : ARN of the Roles Anywhere Profile.
  - role_arn_aws       : ARN of the initial IAM role to obtain via Roles Anywhere.
  - assume_rol_arn     : ARN of the secondary IAM role to assume via STS.
  - region             : AWS region (default: us-east-1).

Dependencies:
-------------
  boto3, pandas, AWS.conexion_aws
"""

import logging as log
from botocore.exceptions import  ClientError
import io, os
import zipfile
import pandas as pd
from AWS.conexion_aws import get_session, assume_role

log.basicConfig(level=log.info)

def obtener_archivo_por_fecha(session, bucket_name,carpeta, fecha_objetivo):
    """
    Busca el archivo en el bucket cuyo prefix contenga la fecha dada.
    Retorna el key del archivo si se encuentra.
    """
    try:
        s3 = session.client("s3")
        prefix = f"{carpeta}/{fecha_objetivo}/"
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        if 'Contents' in response:
            for obj in response['Contents']:
                log.info(f"Archivo encontrado: {obj['Key']}")
                return obj['Key']
        else:
            mensaje = f"No se encontró archivo para la fecha: {fecha_objetivo}"
            log.error(mensaje)
            raise FileNotFoundError(mensaje)

    except ClientError as error:
        log.error(f"Error de AWS al listar objetos: {error}")
        raise 

    except Exception as error:
        log.error(f"Error inesperado al obtener archivo: {error}")
        raise 

def leer_zip_s3(session, bucket_name, key):
    try:
        s3 = session.client('s3')
        response = s3.get_object(Bucket=bucket_name, Key=key)
        zip_bytes = response['Body'].read()

        dataframes = []  # Acumular DataFrames

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for nombre_archivo in z.namelist():
                if nombre_archivo.endswith('.csv') and not nombre_archivo == 'NXERSSADECV_TRANSACTIONS_2025120.csv':
                    with z.open(nombre_archivo) as archivo:
                        df = pd.read_csv(archivo, dtype=str)
                        log.info(f"CSV {nombre_archivo} leído correctamente.")
                        dataframes.append(df)

        if dataframes:
            return pd.concat(dataframes, ignore_index=True)

        mensaje = f"No se encontró ningún archivo .csv dentro del ZIP: {key}"
        log.error(mensaje)
        return None

    except ClientError as e:
        log.error(f"Error al acceder al archivo ZIP en S3: {e}")
        raise 

    except zipfile.BadZipFile as e:
        log.error(f"El archivo no es un ZIP válido: {e}")
        raise

    except Exception as e:
        log.error(f"Error inesperado al leer ZIP desde S3: {e}")
        raise

    
def descargar_contenido_archivo(fecha,bucket_name, carpeta):
    # Configuración de AWS Roles Anywhere
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
    
    if not credentials_anywhere:
        return None

    new_session = assume_role(credentials_anywhere, assume_rol_arn, session_name)
    if not new_session:
        return None

    archivo = obtener_archivo_por_fecha(new_session, bucket_name, carpeta, fecha_objetivo=fecha)

    if not archivo:
        return None

    log.info(f"Archivo correspondiente a la fecha {fecha}: {archivo}")
    return leer_zip_s3(new_session, bucket_name=bucket_name, key=archivo)