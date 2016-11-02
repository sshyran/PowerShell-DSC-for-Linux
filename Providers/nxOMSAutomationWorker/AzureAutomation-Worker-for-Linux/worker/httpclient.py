#!/usr/bin/env python2
#
# Copyright (C) Microsoft Corporation, All rights reserved.

"""HttpClient base class."""

import os
import serializerfactory
import sys
import configuration


class HttpClient:
    """Base class to provide common attributes and functionality to all HttpClient implementation."""
    ACCEPT_HEADER_KEY = "Accept"
    CONNECTION_HEADER_KEY = "Connection"
    USER_AGENT_HEADER_KEY = "User-Agent"

    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"

    def __init__(self, cert_path, key_path, insecure=False):
        self.cert_path = cert_path
        self.key_path = key_path
        self.insecure = insecure

        if (cert_path is not None and not os.path.isfile(self.cert_path)) or \
           (key_path is not None and not os.path.isfile(self.key_path)):
            print cert_path
            raise Exception("Invalid certificate or key file path.")

        self.default_headers = {self.ACCEPT_HEADER_KEY: "application/json",
                                self.CONNECTION_HEADER_KEY: "keep-alive",
                                self.USER_AGENT_HEADER_KEY: "AzureAutomationHybridWorker/" +
                                                            configuration.get_worker_version()}
        self.json = serializerfactory.get_serializer(sys.version_info)

    @staticmethod
    def merge_headers(client_headers, request_headers):
        """Merges client_headers and request_headers into a single dictionary. If a request_header key is also present
        in the client_headers, the request_header value will override the client_header one.

        Args:
            client_headers  : dictionary, the default client's headers.
            request_headers : dictionary, request specific headers.

        Returns:
            A dictionary containing a set of both the client_headers and the request_headers
        """
        if request_headers is not None:
            client_headers.update(request_headers.copy())
        else:
            request_headers = client_headers.copy()
        return request_headers

    def get(self, url, headers=None):
        """Issues a GET request to the provided url using the provided headers.

        Args:
            url     : string    , the URl.
            headers : dictionary, contains the headers key value pair (defaults to None).

        Returns:
            A RequestResponse
        """
        pass

    def post(self, url, headers=None, data=None):
        """Issues a POST request to the provided url using the provided headers.

        Args:
            url     : string    , the URl.
            headers : dictionary, contains the headers key value pair (defaults to None).
            data    : dictionary, contains the non-serialized request body (defaults to None).

        Returns:
            A RequestResponse
        """
        pass
