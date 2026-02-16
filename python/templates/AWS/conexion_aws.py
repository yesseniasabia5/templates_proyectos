
"""
#================================================== 
Script: conexion_aws.py
Author: Yessenia Sabia
#==================================================
AWS IAM Roles Anywhere Authentication via X.509 Certificate (Mutual TLS / SigV4)
==================================================================================

This module provides a certificate-based authentication flow against AWS IAM Roles Anywhere,
allowing workloads outside of AWS (e.g., on-premises servers, CI/CD pipelines) to obtain
temporary AWS credentials without long-lived IAM access keys.

Authentication flow:
--------------------
1. A PEM-encoded X.509 certificate and its corresponding RSA private key are loaded from
   memory (environment variables, secrets managers, etc.), with automatic normalization of
   escaped newlines that often appear when secrets are stored as single-line strings.

2. A canonical HTTP request is manually constructed following the AWS Signature Version 4
   (SigV4) specification, targeting the AWS Roles Anywhere `/sessions` endpoint:
     - The X.509 certificate is attached as the `X-Amz-X509` header (DER/base64 encoded).
     - The request payload specifies the Trust Anchor ARN, Profile ARN, target Role ARN,
       and credential duration (default: 3600 seconds / 1 hour).
     - The canonical request is hashed (SHA-256) and signed with the private key using
       PKCS#1 v1.5 padding, producing the `Authorization` header.

3. The signed request is sent to the regional Roles Anywhere endpoint via HTTPS POST.
   On success, AWS returns a `credentialSet` containing short-lived access key ID,
   secret access key, and session token.

4. Optionally, `assume_role()` can use those initial credentials to perform an STS
   `AssumeRole` call, switching into a second IAM role (e.g., a cross-account role),
   and returning a fresh `boto3.Session` ready for SDK usage.

Key functions:
--------------
- get_session(certificate_path, private_key_path, trust_anchor_arn, profile_arn,
              role_arn_aws, host, region)
      Authenticates via Roles Anywhere and returns the raw credential set.

- assume_role(credentials, assume_rol_arn, session_name)
      Takes a Roles Anywhere credential set and assumes a secondary IAM role via STS,
      returning a configured boto3.Session.

Dependencies:
-------------
  boto3, requests, cryptography (hazmat)

References:
-----------
  - AWS IAM Roles Anywhere: https://docs.aws.amazon.com/rolesanywhere/latest/userguide/
  - AWS Signature Version 4: https://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html
"""

import logging as log
import boto3
import requests
import json
import base64
import datetime
from botocore.exceptions import BotoCoreError, ClientError
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from cryptography.hazmat.backends import default_backend


log.basicConfig(level=log.INFO)

def Lowercase(H):
    return H.lower()

def Hex(S):
    return S.hex()

def SHA256(S):
    digest = hashes.Hash(hashes.SHA256())
    digest.update(S)
    return digest.finalize()

def canonical_headers(headers):
    return ''.join([f"{Lowercase(k)}:{v}\n" for k, v in headers.items()])

def signed_headers(headers):
    return ';'.join([Lowercase(k) for k in headers.keys()])

def sign(key, msg):
    return key.sign(
        msg,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

def get_session(certificate_path, private_key_path, trust_anchor_arn, profile_arn, role_arn_aws, host, region):
    try:
        if "\\n" in certificate_path:
            certificate_path = certificate_path.replace("\\n", "\n")
        cert = x509.load_pem_x509_certificate(certificate_path.encode("utf-8"), backend=default_backend())
    except Exception as e:
        raise Exception(f"Error al cargar el certificado desde memoria: {e}")

    if not certificate_path.startswith("-----BEGIN CERTIFICATE-----"):
        raise Exception("El certificado no está en formato PEM válido.")

    try:
        if "\\n" in private_key_path:
            private_key_path = private_key_path.replace("\\n", "\n")
        elif "-----BEGIN PRIVATE KEY-----" in private_key_path and "\n" not in private_key_path:
            private_key_path = private_key_path.replace(
                "-----BEGIN PRIVATE KEY----- ", "-----BEGIN PRIVATE KEY-----\n"
            ).replace(
                " -----END PRIVATE KEY-----", "\n-----END PRIVATE KEY-----"
            )

        private_key = serialization.load_pem_private_key(
            private_key_path.encode("utf-8"),
            password=None,
            backend=default_backend()
        )
    except Exception as e:
        raise Exception(f"Error al cargar la clave privada desde memoria: {e}")

    cert_b64 = base64.b64encode(cert.public_bytes(encoding=serialization.Encoding.DER)).decode('utf-8')

    HttpRequestMethod = 'POST'
    CanonicalUri = '/sessions'
    CanonicalQueryString = ''
    RequestDateTime = datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%SZ')

    Headers = {
        'Content-Type': 'application/json',
        'Host': host,
        'X-Amz-Date': RequestDateTime,
        'X-Amz-X509': cert_b64
    }

    RequestPayload = json.dumps({
        "durationSeconds": 3600,
        "roleArn": role_arn_aws,
        "trustAnchorArn": trust_anchor_arn,
        "profileArn": profile_arn
    }).encode('utf-8')

    CanonicalHeaders = canonical_headers(Headers)
    SignedHeaders = signed_headers(Headers)

    CanonicalRequest = (
        HttpRequestMethod + '\n' +
        CanonicalUri + '\n' +
        CanonicalQueryString + '\n' +
        CanonicalHeaders + '\n' +
        SignedHeaders + '\n' +
        Lowercase(Hex(SHA256(RequestPayload)))
    )

    Algorithm = "AWS4-HMAC-SHA256" # is not a sensible value since Roles Anywhere does not use a secret key for signing, but we include it for completeness No es un valor sensible ya que Roles Anywhere no utiliza una clave secreta para firmar.
    CredentialScope = RequestDateTime[:8] + '/' + region + '/rolesanywhere/aws4_request'
    HashedCanonicalRequest = Hex(SHA256(CanonicalRequest.encode('utf-8')))
    StringToSign = Algorithm + '\n' + RequestDateTime + '\n' + CredentialScope + '\n' + HashedCanonicalRequest
    Signature = Hex(sign(private_key, StringToSign.encode('utf-8')))
    CredentialString = str(cert.serial_number) + '/' + CredentialScope
    Authorization = f"{Algorithm} Credential={CredentialString}, SignedHeaders={SignedHeaders}, Signature={Signature}"

    Headers['Authorization'] = Authorization

    url = f'https://{host}{CanonicalUri}'
    response = requests.post(url, headers=Headers, data=RequestPayload)

    try:
        response.raise_for_status()
        return response.json().get("credentialSet")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Error HTTP: {e}, contenido: {response.content.decode('utf-8')}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error JSON: {e}, contenido: {response.content.decode('utf-8')}")

def assume_role(credentials, assume_rol_arn, session_name):
    session = boto3.Session(
        aws_access_key_id=credentials[0]["credentials"]["accessKeyId"],
        aws_secret_access_key=credentials[0]["credentials"]["secretAccessKey"],
        aws_session_token=credentials[0]["credentials"]["sessionToken"]
    )

    sts_client = session.client("sts")

    try:
        response = sts_client.assume_role(
            RoleArn=assume_rol_arn,
            RoleSessionName=session_name
        )
        new_session = boto3.Session(
            aws_access_key_id=response["Credentials"]["AccessKeyId"],
            aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
            aws_session_token=response["Credentials"]["SessionToken"]
        )
        return new_session

    except (BotoCoreError, ClientError) as err:
        return None
