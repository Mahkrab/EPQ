"""Qualification preserves raw failures and rejects stale or escaping source paths."""

import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from tools.cuda.qualify import invoke, verify_source


class QualificationBoundaryTests(unittest.TestCase):
    def test_source_identity_requires_current_bytes_within_the_source_directory(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "source"
            source.mkdir()
            (source / "input").write_bytes(b"original")
            manifest = {"files_sha256": {"input": hashlib.sha256(b"original").hexdigest()}}
            verify_source(source, manifest)
            (source / "input").write_bytes(b"changed")
            with self.assertRaises(ValueError):
                verify_source(source, manifest)
            (root / "outside").write_bytes(b"original")
            with self.assertRaises(ValueError):
                verify_source(source, {"files_sha256": {"../outside": hashlib.sha256(b"original").hexdigest()}})

    def test_failed_application_keeps_exit_stderr_and_original_partial_output(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            evidence, document = invoke(Path(sys.executable), root,
                ["-c", "import sys; print('{partial'); print('failure',file=sys.stderr); sys.exit(3)"], root / "failed.json.gz")
            self.assertEqual(evidence["exit_code"], 3)
            self.assertEqual(evidence["stderr"], "failure\n")
            self.assertEqual(document, {})
            self.assertEqual(gzip.decompress((root / "failed.json.gz").read_bytes()), b"{partial\n")

    def test_success_returns_the_complete_original_document_without_overwriting_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            output = root / "complete.json.gz"
            evidence, document = invoke(Path(sys.executable), root,
                ["-c", "print('{\"status\":\"completed\"}')"], output)
            self.assertEqual(evidence["exit_code"], 0)
            self.assertEqual(document, {"status": "completed"})
            self.assertEqual(json.loads(gzip.decompress(output.read_bytes())), document)
