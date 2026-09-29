from __future__ import annotations

import ssl

from openai_responses_plugins.verified_ssl import verified_ssl_context


def test_verified_ssl_context_requires_certificate_validation() -> None:
    context = verified_ssl_context()

    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert context.get_ca_certs()