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
import hmac
from datetime import datetime, timedelta

from dciauth.v2.headers import generate_headers, TIMESTAMP_FORMAT, _lower


def is_valid(request, credential, parsed_headers):
    if parsed_headers is None:
        return False, "headers are malformated"

    if is_expired(request, parsed_headers):
        return False, "signature is expired"

    claimed_request = _get_claimed_request(request, parsed_headers)
    claimed_credential = _get_claimed_credential(credential, parsed_headers)
    claimed_headers = generate_headers(claimed_request, claimed_credential)
    signature = parsed_headers.get("signature")
    claimed_signature = _get_signature(_lower(claimed_headers))
    if _signature_equals(signature, claimed_signature):
        return True, ""

    return False, "signature is invalid"


def is_expired(request, parsed_headers):
    timestamp = parsed_headers["timestamp"]
    if timestamp:
        timestamp = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        now = request.get("now", datetime.utcnow())
        fifteen_min = timedelta(minutes=15)
        return abs(now - timestamp) > fifteen_min
    return True


def _get_claimed_request(request, headers):
    claimed_request = headers
    claimed_request.update(
        {
            "method": request.get("method", "GET"),
            "endpoint": request.get("endpoint", "/"),
            "params": request.get("params", {}),
            "data": request.get("data", ""),
        }
    )
    return claimed_request


def _get_claimed_credential(credential, headers):
    return {
        "access_key": "%s/%s" % (headers["client_type"], headers["client_id"]),
        "secret_key": credential["secret_key"],
    }


def _get_signature(headers):
    kv_signature = headers.get("authorization").split(" ")[3]
    signature = kv_signature.split("Signature=")[1]
    return signature


def _signature_equals(signature1, signature2):
    return hmac.compare_digest(signature1.encode("utf-8"), signature2.encode("utf-8"))
