import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from owl.safe_io import extract_zip_safely, require_local_document


class DocumentBoundaryTests(unittest.TestCase):
    def test_reject_remote_and_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("SECRET=hidden")
            with patch.dict(os.environ, {"OWL_DOCUMENT_ROOT": directory}):
                with self.assertRaises(PermissionError):
                    require_local_document("http://169.254.169.254/latest/meta-data")
                with self.assertRaises(PermissionError):
                    require_local_document(str(root / ".env"))
                with self.assertRaises(PermissionError):
                    require_local_document("/etc/passwd")

    def test_zip_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "data.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("nested/ok.txt", "example")
            with patch.dict(os.environ, {"OWL_DOCUMENT_ROOT": directory}):
                output = extract_zip_safely(str(archive), str(Path(directory) / "cache"))
            self.assertEqual(len(output), 1)
            self.assertEqual(Path(output[0]).read_text(), "example")

    def test_zip_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "evil.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("../../outside.txt", "unsafe")
            with patch.dict(os.environ, {"OWL_DOCUMENT_ROOT": directory}):
                with self.assertRaises(ValueError):
                    extract_zip_safely(str(archive), str(Path(directory) / "cache"))
            self.assertFalse((Path(directory) / "outside.txt").exists())


if __name__ == "__main__":
    unittest.main()
