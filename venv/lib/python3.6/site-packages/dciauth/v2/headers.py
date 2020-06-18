#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License'); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import datetime
import hashlib
import hmac
import json
from collections import OrderedDict

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
DATESTAMP_FORMAT = "%Y%m%d"


def generate_headers(request, credentials):
    access_key = credentials.get("access_key")
    secret_key = credentials.get("secret_key")
    if not access_key or not secret_key:
        return {}
    if 'payload' in request:
        payload = request.pop('payload')
        request['data'] = json.dumps(payload)
    authorization_header = _build_authorization_header(request, access_key, secret_key)
    return {
        "X-DCI-Date": _get_timestamp(request),
        "Authorization": authorization_header,
    }


def _build_authorization_header(request, access_key, secret_key):
    string_to_sign = _get_string_to_sign(request)
    signing_key = _get_signing_key(request, secret_key)
    signature = hmac.new(signing_key, string_to_sign, hashlib.sha256).hexdigest()
    # pylint: disable=line-too-long
    return """{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}""".format(
        algorithm=_get_algorithm(request),
        access_key=access_key,
        credential_scope=_get_credential_scope(request),
        signed_headers=_get_signed_headers(request),
        signature=signature,
    )
    # pylint: enable=line-too-long


def _get_string_to_sign(request):
    string_to_sign = """{algorithm}
{timestamp}
{credential_scope}
{canonical_request}""".format(
        algorithm=_get_algorithm(request),
        timestamp=_get_timestamp(request),
        credential_scope=_get_credential_scope(request),
        canonical_request=_get_canonical_request(request),
    )
    return string_to_sign.encode("utf-8")


def _get_canonical_request(request):
    canonical_request = """{method}
{endpoint}
{canonical_querystring}
{canonical_headers}
{signed_headers}
{payload_hash}""".format(
        method=request.get("method", "GET"),
        endpoint=request.get("endpoint", "/"),
        canonical_querystring=_get_canonical_querystring(request),
        canonical_headers=_get_canonical_headers(request),
        signed_headers=_get_signed_headers(request),
        payload_hash=_get_payload_hash(request),
    )
    return hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()


def _get_canonical_querystring(request):
    params = request.get("params")
    return urlencode(_order_dict(params)) if params else ""


def _get_payload_hash(request):
    data = request.get("data", "")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _get_canonical_headers(request):
    canonical_headers = request.get(
        "canonical_headers",
        {
            "host": request.get("host", "api.distributed-ci.io"),
            "x-dci-date": _get_timestamp(request),
        },
    )
    signed_headers = _get_signed_headers(request)
    return (
        "\n".join(
            ["%s:%s" % (h, canonical_headers[h]) for h in signed_headers.split(";")]
        )
        + "\n"
    )


def _get_credential_scope(request):
    return """{datestamp}/{region}/{service}/{request_type}""".format(
        datestamp=_get_datestamp(request),
        region=_get_region(request),
        service=_get_service(request),
        request_type=_get_request_type(request),
    )


def _get_signing_key(request, key):
    algorithm = _get_algorithm(request)
    algo_version = algorithm.replace("-HMAC-SHA256", "")
    datestamp = _get_datestamp(request)
    key_date = _sign((algo_version + key).encode("utf-8"), datestamp)
    region = _get_region(request)
    key_region = _sign(key_date, region)
    service = _get_service(request)
    key_service = _sign(key_region, service)
    request_type = _get_request_type(request)
    return _sign(key_service, request_type)


def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_now(request):
    return request.get("now", datetime.datetime.utcnow())


def _get_datestamp(request):
    now = _get_now(request)
    return request.get("datestamp", now.strftime(DATESTAMP_FORMAT))


def _get_timestamp(request):
    now = _get_now(request)
    return request.get("timestamp", now.strftime(TIMESTAMP_FORMAT))


def _get_signed_headers(request):
    return request.get("signed_headers", "host;x-dci-date")


def _get_algorithm(request):
    return request.get("algorithm", "DCI2-HMAC-SHA256")


def _get_region(request):
    return request.get("region", "BHS3")


def _get_service(request):
    return request.get("service", "api")


def _get_request_type(request):
    return request.get("request_type", "dci2_request")


def _order_dict(dictionary):
    return OrderedDict(sorted(dictionary.items(), key=lambda k: k[0]))


def _lower(headers):
    return {key.lower(): value for key, value in headers.items()}


def parse_headers(headers):
    headers = _lower(headers)
    timestamp = _parse_timestamp(headers)
    authorization = headers.get("authorization")
    if not timestamp or not authorization:
        return None
    algorithm, credential, signed_headers, signature = authorization.split(" ")
    signature = signature.replace("Signature=", "")
    credential = _find_in_str_between(credential, "Credential=", ",").split("/")
    if len(credential) != 6:
        return None
    signed_headers = _find_in_str_between(signed_headers, "SignedHeaders=", ",")
    return {
        "host": headers.get("host"),
        "algorithm": algorithm,
        "client_type": credential[0],
        "client_id": credential[1],
        "datestamp": credential[2],
        "region": credential[3],
        "service": credential[4],
        "request_type": credential[5],
        "signed_headers": signed_headers,
        "canonical_headers": {h: headers[h] for h in signed_headers.split(";")},
        "timestamp": timestamp,
        "signature": signature,
    }


def _parse_timestamp(headers):
    aws_date_header = "x-amz-date"
    dci_date_header = "x-dci-date"
    if aws_date_header not in headers and dci_date_header not in headers:
        return None
    return (
        headers[aws_date_header]
        if aws_date_header in headers
        else headers[dci_date_header]
    )


def _find_in_str_between(string, first, last):
    try:
        start = string.index(first) + len(first)
        end = string.index(last, start)
        return string[start:end]
    except ValueError:
        return ""
