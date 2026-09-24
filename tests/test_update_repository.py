from __future__ import annotations

import json
import sys
import tempfile
import unittest
import struct
import zlib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import update_repository as updater  # noqa: E402


class PipeRecordTests(unittest.TestCase):
    def test_utf8_value_wins_over_legacy_fallback(self) -> None:
        raw = (
            b"|RECORD=41|%UTF8%Text=Za\xc5\xbc\xc3\xb3\xc5\x82\xc4\x87|||"
            b"Text=Zazolc|Name=Value\x00"
        )
        parsed = updater.parse_pipe_record(raw)
        self.assertEqual(parsed["Text"], "Zażółć")
        self.assertEqual(parsed["Name"], "Value")

    def test_parameter_aliases_ignore_spacing_and_punctuation(self) -> None:
        parameters = {"Mfr. Part Number": "ABC-123"}
        value = updater.get_parameter(parameters, ["Part Number", "Mfr Part Number"])
        self.assertEqual(value, "ABC-123")

    def test_primary_manufacturer_fields_are_supported_by_config(self) -> None:
        config = json.loads(
            (REPOSITORY_ROOT / "config" / "catalog_schema.json").read_text(
                encoding="utf-8"
            )
        )
        aliases = config["catalog_aliases"]
        parameters = {
            "Manufacturer 1": "Example Inc.",
            "Part Number 1": "ABC-123",
        }

        self.assertEqual(
            updater.get_parameter(parameters, aliases["manufacturer"]),
            "Example Inc.",
        )
        self.assertEqual(
            updater.get_parameter(parameters, aliases["manufacturer_part_number"]),
            "ABC-123",
        )

    def test_mixed_utf8_and_cp1252_text_is_preserved(self) -> None:
        raw = b"Manufacturer=W\xfcrth|Description=5 \xc2\xb5A \xae\x00"
        parsed = updater.parse_pipe_record(raw)
        self.assertEqual(parsed["Manufacturer"], "Würth")
        self.assertEqual(parsed["Description"], "5 µA ®")

    def test_compiled_parameter_blob_ignores_footprint_records(self) -> None:
        component = (
            b"Library Reference=ABC-123|Manufacturer=Example|"
            b"Part Number=ABC-123|Package=QFN-16\x00"
        )
        footprint = b"Description=QFN footprint|Height=1|Pad Count=16\x00"
        blob = (
            struct.pack("<I", len(component))
            + component
            + struct.pack("<I", len(footprint))
            + footprint
        )
        aliases = {
            "manufacturer_part_number": ["Part Number"],
            "manufacturer": ["Manufacturer"],
            "package": ["Package"],
        }

        parsed = updater.parse_parameter_blob(
            blob,
            category="IC",
            intlib=Path("compiled/IC.IntLib"),
            aliases=aliases,
        )

        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].manufacturer_part_number, "ABC-123")

    def test_intlib_stream_compression_markers(self) -> None:
        payload = b"compiled-parameters"
        source = Path("TEST.IntLib")
        self.assertEqual(
            updater.decode_intlib_payload(b"\x00" + payload, source=source, stream_name="p"),
            payload,
        )
        self.assertEqual(
            updater.decode_intlib_payload(
                b"\x02" + zlib.compress(payload), source=source, stream_name="p"
            ),
            payload,
        )


class IntLibSynchronizationTests(unittest.TestCase):
    def test_collects_intlib_and_removes_generated_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            compiled = root / "compiled"
            output = source / "IC" / "Project Outputs for IC"
            output.mkdir(parents=True)
            compiled.mkdir()
            (output / "IC.IntLib").write_bytes(b"new-library")
            (compiled / "IC.IntLib").write_bytes(b"old-library")

            result = updater.sync_intlibs(source, compiled)

            self.assertEqual((compiled / "IC.IntLib").read_bytes(), b"new-library")
            self.assertFalse(output.exists())
            self.assertEqual(result.intlibs_changed, 1)
            self.assertEqual(result.output_directories, 1)
            self.assertEqual(result.intlib_categories["IC.IntLib"], "IC")
            manifest = (compiled / updater.MANIFEST_FILENAME).read_text(encoding="utf-8")
            self.assertIn('"IC.IntLib": "IC"', manifest)

    def test_conflict_is_detected_before_generated_directories_are_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            compiled = root / "compiled"
            first = source / "IC" / "Project Outputs for IC"
            second = source / "MODULES" / "Project Outputs for MODULES"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "LIB.IntLib").write_bytes(b"first")
            (second / "lib.intlib").write_bytes(b"second")

            with self.assertRaises(updater.RepositoryUpdateError):
                updater.sync_intlibs(source, compiled)

            self.assertTrue(first.exists())
            self.assertTrue(second.exists())
            self.assertFalse(compiled.exists())


class ReadmeTests(unittest.TestCase):
    def test_only_marked_catalog_block_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            readme = Path(temp) / "README.md"
            readme.write_text(
                "# Fixed description\n\n"
                f"{updater.CATALOG_START}\nold\n{updater.CATALOG_END}\n",
                encoding="utf-8",
            )

            changed = updater.update_readme(readme, "## New catalog\n\nContent")
            result = readme.read_text(encoding="utf-8")

            self.assertTrue(changed)
            self.assertTrue(result.startswith("# Fixed description\n\n"))
            self.assertIn("## New catalog", result)
            self.assertNotIn("\nold\n", result)

    def test_catalog_has_requested_columns_and_escapes_pipes(self) -> None:
        component = updater.Component(
            category="IC",
            symbol="EXAMPLE",
            manufacturer_part_number="ABC|123",
            manufacturer="Example Inc.",
            package="QFN-32",
            intlib=Path("compiled/IC.IntLib"),
            parameters={},
        )
        catalog = updater.render_catalog([component], ["IC", "MISC"])

        self.assertIn("## Compiled Library Contents", catalog)
        self.assertIn("### Category Summary", catalog)
        self.assertNotIn("Automatyczny katalog komponentów", catalog)
        self.assertIn(
            "| Manufacturer part number | Manufacturer | Package |",
            catalog,
        )
        self.assertIn("| ABC\\|123 | Example Inc. | QFN-32 |", catalog)
        self.assertIn("| MISC | 0 | 0 |", catalog)


if __name__ == "__main__":
    unittest.main()
