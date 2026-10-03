"""Credential handling and failure-path regression checks; no real network/key."""

import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import api_common


FAKE_KEY = "test-credential-with-plus+slash/equals="
ENDPOINT = "https://apis.data.go.kr/test/service"


class CredentialTests(unittest.TestCase):
    def test_kosis_uses_api_key_without_data_go_kr_parameter(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(b'[{"PRD_DE": "2025", "DT": "84.1"}]')
        with patch.object(api_common.urllib.request, "build_opener", return_value=opener):
            payload, _ = api_common.request_json(
                "https://kosis.kr/openapi/Param/statisticsParameterData.do",
                {"method": "getList", "format": "json"}, FAKE_KEY)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(opener.open.call_args.args[0].full_url).query)
        self.assertEqual(query["apiKey"], [FAKE_KEY])
        self.assertNotIn("serviceKey", query)
        self.assertEqual(payload[0]["PRD_DE"], "2025")

    def test_kosis_rejects_non_api_paths_and_query_credentials(self):
        with self.assertRaises(api_common.ApiError):
            api_common.request_json("https://kosis.kr/statHtml/statHtml.do", {}, FAKE_KEY)
        with self.assertRaises(api_common.ApiError):
            api_common.request_json("https://kosis.kr/openapi/x.do?apiKey=not-allowed", {}, FAKE_KEY)

    def test_encoded_key_round_trip_preserves_literal_plus(self):
        with patch.dict(os.environ, {"TEST_SERVICE_KEY": urllib.parse.quote(FAKE_KEY, safe="")}):
            decoded = api_common.load_key("TEST_SERVICE_KEY")
        self.assertEqual(decoded, FAKE_KEY)
        opener = Mock()
        opener.open.return_value = io.BytesIO(b'{"ok": true}')
        with patch.object(api_common.urllib.request, "build_opener", return_value=opener):
            payload, _ = api_common.request_json(ENDPOINT, {"pageNo": 1}, decoded)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(opener.open.call_args.args[0].full_url).query)
        self.assertEqual(query["serviceKey"], [FAKE_KEY])
        self.assertTrue(payload["ok"])

    def test_dotenv_quotes_and_duplicate_entries(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(api_common, "ROOT", Path(directory)):
            path = Path(directory) / ".env"
            path.write_text(f'export TEST_SERVICE_KEY="{FAKE_KEY}"\n', encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(api_common.load_key("TEST_SERVICE_KEY"), FAKE_KEY)
                path.write_text(f'TEST_SERVICE_KEY={FAKE_KEY}\nTEST_SERVICE_KEY={FAKE_KEY}\n')
                with self.assertRaises(api_common.ApiError):
                    api_common.load_key("TEST_SERVICE_KEY")

    def test_http_error_does_not_expose_url_or_key(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            ENDPOINT + "?serviceKey=" + FAKE_KEY, 401, "Bad credential: " + FAKE_KEY,
            {}, io.BytesIO(b'<returnReasonCode>30</returnReasonCode>'),
        )
        with patch.object(api_common.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(api_common.ApiError) as caught:
                api_common.request_json(ENDPOINT, {}, FAKE_KEY)
        self.assertEqual(str(caught.exception), "HTTP 401; API error code: 30")
        self.assertNotIn(FAKE_KEY, str(caught.exception))

    def test_refuses_response_that_echoes_credential(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(json.dumps({"credential": FAKE_KEY}).encode())
        with patch.object(api_common.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(api_common.ApiError) as caught:
                api_common.request_json(ENDPOINT, {}, FAKE_KEY)
        self.assertNotIn(FAKE_KEY, str(caught.exception))

    def test_refuses_unapproved_host_and_credential_in_recordable_params(self):
        with self.assertRaises(api_common.ApiError):
            api_common.request_json("https://example.org/service", {}, FAKE_KEY)
        with self.assertRaises(api_common.ApiError):
            api_common.request_json(ENDPOINT, {"serviceKey": FAKE_KEY}, FAKE_KEY)

    def test_xml_error_is_not_mistaken_for_empty_json_success(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(b'<returnReasonCode>22</returnReasonCode>')
        with patch.object(api_common.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(api_common.ApiError, "API error code: 22"):
                api_common.request_json(ENDPOINT, {}, FAKE_KEY)


if __name__ == "__main__":
    unittest.main()
