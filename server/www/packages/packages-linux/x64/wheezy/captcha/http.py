"""
"""

import random
from datetime import timedelta
from time import time
from uuid import uuid4

from wheezy.core.collections import last_item_adapter
from wheezy.core.uuid import shrink_uuid
from wheezy.http import (
    CacheProfile,
    HTTPResponse,
    accept_method,
    bad_request,
    response_cache,
)


class FileAdapter(object):
    def __init__(self, response):
        self.write = response.write_bytes


class CaptchaContext(object):
    def __init__(
        self,
        image,
        cache,
        prefix="captcha:",
        namespace=None,
        timeout=5 * 60,
        profile=None,
        chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789",
        max_chars=4,
        wait_timeout=2,
        challenge_key="c",
        turing_key="turing_number",
        enabled=True,
    ):
        self.image = image
        self.cache = cache
        self.prefix = prefix
        self.namespace = namespace
        self.timeout = timeout
        self.chars = chars
        self.wait_timeout = wait_timeout
        self.max_chars = max_chars
        self.challenge_key = challenge_key
        self.turing_key = turing_key
        self.enabled = enabled
        if profile:
            self.profile = profile
        else:
            self.profile = CacheProfile(
                "server",
                vary_query=[challenge_key],
                duration=timedelta(seconds=wait_timeout),
                no_store=True,
                namespace=namespace,
            )

    def create_handler(
        self, content_type="image/jpg", format="JPEG", **options
    ):
        @accept_method("GET")
        @response_cache(self.profile)
        def handler(request):
            if self.challenge_key not in request.query:
                return bad_request()
            challenge_code = last_item_adapter(request.query)[
                self.challenge_key
            ]
            turing_number = "".join(random.sample(self.chars, self.max_chars))
            if not self.cache.set(
                self.prefix + challenge_code,
                (int(time()), turing_number),
                self.timeout,
                self.namespace,
            ):
                return bad_request()
            response = HTTPResponse(content_type)
            self.image(turing_number).save(
                FileAdapter(response), format, **options
            )
            return response

        return handler

    def get_challenge_code(self, request):
        if self.challenge_key not in request.query:
            return shrink_uuid(uuid4())
        else:
            return request.query[self.challenge_key][0]

    def validate(self, request, errors, gettext):
        if not self.enabled:
            return True
        if self.challenge_key not in request.form:
            self.append_error(
                errors, gettext("The challenge code is not available.")
            )
            return False
        if self.turing_key not in request.form:
            self.append_error(
                errors, gettext("The turing number is not available.")
            )
            return False
        form = last_item_adapter(request.form)
        challenge_code = form[self.challenge_key]
        if len(challenge_code) != 22:
            self.append_error(
                errors, gettext("The challenge code is invalid.")
            )
            return False
        entered_turing_number = form[self.turing_key]
        if len(entered_turing_number) != self.max_chars:
            self.append_error(errors, gettext("The turing number is invalid."))
            return False

        key = self.prefix + challenge_code
        data = self.cache.get(key, self.namespace)
        if not data:
            self.append_error(
                errors,
                gettext("The code you typed has expired after %d seconds.")
                % self.timeout,
            )
            return False
        self.cache.delete(key, 0, self.namespace)
        issued, turing_number = data
        if issued + self.wait_timeout > int(time()):
            self.append_error(
                errors,
                gettext(
                    "The code was typed too quickly. Wait at least %d seconds."
                )
                % self.wait_timeout,
            )
            return False
        if turing_number != entered_turing_number.upper():
            self.append_error(
                errors, gettext("The code you typed has no match.")
            )
            return False
        return True

    def append_error(self, errors, message):
        errors.setdefault(self.turing_key, []).append(message)
