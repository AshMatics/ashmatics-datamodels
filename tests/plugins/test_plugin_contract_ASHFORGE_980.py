# Copyright 2026 Asher Informatics PBC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Plugin contracts (ASHFORGE-980, forge/watch ADR-010 and its Amendment 1).

The two contracts here are built on real CUBE parameter lists, saved in ``data/``:
``pl-pfdicom_tagExtract`` 3.2.4 from the distributed-site sandbox CUBE, and
``pl-dicom_headerEdit`` 1.1.8 from the public ChRIS CUBE. They are test contracts,
not the reviewed ones the workbench will ship.
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ashmatics_datamodels.plugins import (
    ParameterContract,
    PluginContract,
    is_set,
    validate_portable_pattern,
)

DATA = Path(__file__).parent / "data"
STEM_EXAMPLE = "tags"


def _cube(name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = json.loads((DATA / name).read_text())
    return rows


def tag_extract() -> dict[str, Any]:
    return {
        "plugin_name": "pl-pfdicom_tagExtract",
        "plugin_version": "3.2.4",
        "plugin_type": "ds",
        "origin": "adopted",
        "title": "DICOM header tags as JSON",
        "description": "Reads DICOM headers and writes their tags.",
        "inputs": [
            {
                "name": "dicom",
                "format": "dicom",
                "file_pattern": "*.dcm",
                "layout": "series_per_folder",
                "description": "DICOM files, one series per folder",
            }
        ],
        "outputs": [
            {
                "name": "tags",
                "format": "json",
                "file_pattern": "*.json",
                "phi": "possible",
                "description": "One JSON file of header tags per series",
            }
        ],
        "parameters": [
            {
                "name": "fileFilter",
                "flag": "--fileFilter",
                "type": "string",
                "default": "",
                "label": "File filter",
                "help": "Only files whose names contain this are read",
                "non_empty": True,
            },
            {
                "name": "outputFileStem",
                "flag": "--outputFileStem",
                "type": "string",
                "default": "",
                "label": "Output file name",
                "help": "Stem of each output file; empty means nothing is written",
                "pattern": r"[A-Za-z0-9_-]{1,64}",
                "example": STEM_EXAMPLE,
                "non_empty": True,
                "empty_reason": "with no value the plugin writes nothing",
                "forbidden_tokens": ["%Patient", "%Accession"],
            },
            {
                "name": "outputFileType",
                "flag": "--outputFileType",
                "type": "string",
                "default": "raw",
                "label": "Output formats",
                "help": "Comma-separated output formats",
                "pattern": r"(?:raw|json|html|dict|col|csv)(?:,(?:raw|json|html|dict|col|csv))*",
                "example": "json",
                "advanced": True,
            },
            {
                "name": "threads",
                "flag": "--threads",
                "type": "string",
                "default": "0",
                "label": "Threads",
                "help": "Worker threads; 0 lets the plugin choose",
                "pattern": r"[0-9]{1,3}",
                "example": "0",
                "advanced": True,
            },
        ],
        "presets": [
            {
                "name": "series-metadata-json",
                "label": "Series metadata as JSON",
                "description": "One JSON file of tags per series (the ASHFORGE-979 fix)",
                "values": {
                    "fileFilter": "dcm",
                    "outputFileStem": STEM_EXAMPLE,
                    "outputFileType": "json",
                },
            }
        ],
    }


TAG_STRUCT = json.dumps(
    {
        "PatientName": "%_name|patientID_PatientName",
        "PatientID": "%_md5|7_PatientID",
        "AccessionNumber": "%_md5|8_AccessionNumber",
        "PatientBirthDate": "%_strmsk|******01_PatientBirthDate",
    }
)


def header_edit() -> dict[str, Any]:
    return {
        "plugin_name": "pl-dicom_headerEdit",
        "plugin_version": "1.1.8",
        "plugin_type": "ds",
        "origin": "adopted",
        "role": "deidentification",
        "title": "De-identify DICOM headers",
        "description": "Edits DICOM headers with pfdicom_tagSub rules.",
        "source_repository": "https://github.com/FNNDSC/pl-dicom_headerEdit",
        "inputs": [
            {
                "name": "dicom",
                "format": "dicom",
                "file_pattern": "*.dcm",
                "modalities": ["CT"],
                "description": "DICOM files in any folder tree",
            }
        ],
        "outputs": [
            {
                "name": "dicom",
                "format": "dicom",
                "file_pattern": "*.dcm",
                "phi": "possible",  # 1.1.8 keeps private tags (ADR-010 C2)
                "description": "The same files with edited headers, in the same tree",
            }
        ],
        "parameters": [
            {
                "name": "fileFilter",
                "flag": "--fileFilter",
                "type": "string",
                "default": "",
                "label": "File filter",
                "help": "Only files whose names contain this are edited",
                "non_empty": True,
            },
            {
                "name": "tagStruct",
                "flag": "--tagStruct",
                "type": "string",
                "default": "",
                "label": "Tag rules (JSON)",
                "help": "A JSON object of tag keyword to substitution",
                "text_format": "json",
            },
            {
                "name": "tagInfo",
                "flag": "--tagInfo",
                "type": "string",
                "default": "",
                "label": "Tag rules (text)",
                "help": "Rules as text, split by the two split settings",
                "advanced": True,
            },
            {
                "name": "splitToken",
                "flag": "--splitToken",
                "type": "string",
                "default": "++",
                "label": "Rule separator",
                "help": "Separates rules in the text form",
                "advanced": True,
            },
            {
                "name": "splitKeyValue",
                "flag": "--splitKeyValue",
                "type": "string",
                "default": ",",
                "label": "Key and value separator",
                "help": "Separates a tag from its substitution in the text form",
                "advanced": True,
            },
        ],
        "rules": [
            {
                "kind": "exactly_one_of",
                "parameters": ["tagStruct", "tagInfo"],
                "message": (
                    "Give the tag rules once, as JSON or as text. With neither, the "
                    "plugin copies every file unchanged and still reports success."
                ),
            }
        ],
        "presets": [
            {
                "name": "basic-header-deid",
                "label": "Basic header de-identification",
                "description": "Pseudonymises name, IDs and accession; keeps the birth year",
                "values": {"fileFilter": "dcm", "tagStruct": TAG_STRUCT},
            }
        ],
        "deidentification": {
            "verify_tags": [
                "PatientName",
                "PatientID",
                "AccessionNumber",
                "PatientBirthDate",
            ],
            "removes_private_tags": False,
            "handles_burned_in_pixels": False,
            "notes": "1.1.8 has no removePrivateTags; 1.2.0 adds it.",
        },
    }


def _errors(contract: PluginContract, values: dict[str, Any]) -> list[str]:
    return [p.message for p in contract.check_values(values) if p.severity == "error"]


# The two contracts, as written


def test_tag_extract_contract_is_valid_and_roundtrips() -> None:
    contract = PluginContract.model_validate(tag_extract())
    again = PluginContract.model_validate_json(contract.model_dump_json())
    assert again == contract
    assert contract.schema_version == "1"


def test_tag_extract_defaults_are_refused_like_ashforge_979() -> None:
    contract = PluginContract.model_validate(tag_extract())
    errors = _errors(contract, {})
    assert (
        "Output file name (--outputFileStem) must not be empty: with no value the "
        "plugin writes nothing"
    ) in errors
    assert "File filter (--fileFilter) must not be empty" in errors


def test_the_preset_passes_and_a_patient_token_does_not() -> None:
    contract = PluginContract.model_validate(tag_extract())
    preset = contract.presets[0].values
    assert contract.check_values(preset) == []
    bad = dict(preset, outputFileStem="%PatientName")
    errors = _errors(contract, bad)
    assert any("may not contain '%Patient'" in e for e in errors)
    assert any("should look like 'tags'" in e for e in errors)


def test_a_bad_list_value_names_the_parameter_and_the_value() -> None:
    contract = PluginContract.model_validate(tag_extract())
    values = dict(contract.presets[0].values, outputFileType="json, csv")
    [message] = _errors(contract, values)
    assert message == (
        "Output formats (--outputFileType) got 'json, csv'; it should look like 'json'"
    )


def test_unknown_parameters_are_errors() -> None:
    contract = PluginContract.model_validate(tag_extract())
    values = dict(contract.presets[0].values, outputfilestem="x")
    assert "outputfilestem is not a parameter this contract knows" in _errors(
        contract, values
    )


def test_whitespace_in_values_is_kept() -> None:
    contract = PluginContract.model_validate(header_edit())
    split = contract.check_values(
        {"fileFilter": "dcm", "tagInfo": "PatientID , #tag", "splitKeyValue": " , "}
    )
    assert split == []
    assert contract.effective_values({"splitKeyValue": " , "})["splitKeyValue"] == " , "


def test_whitespace_survives_a_json_roundtrip() -> None:
    data = header_edit()
    data["parameters"][3]["default"] = "++ "
    data["presets"][0]["values"]["splitToken"] = " ++ "
    contract = PluginContract.model_validate_json(json.dumps(data))
    again = PluginContract.model_validate_json(contract.model_dump_json())
    assert again.parameter("splitToken").default == "++ "  # type: ignore[union-attr]
    assert again.presets[0].values["splitToken"] == " ++ "


# De-identification (ADR-010 Amendment 1)


def test_header_edit_contract_is_valid() -> None:
    contract = PluginContract.model_validate(header_edit())
    assert contract.role == "deidentification"
    assert contract.check_values(contract.presets[0].values) == []


@pytest.mark.parametrize(
    "values",
    [
        {"fileFilter": "dcm"},  # neither: the plugin would copy PHI through
        {"fileFilter": "dcm", "tagStruct": TAG_STRUCT, "tagInfo": "PatientID,#tag"},
    ],
)
def test_header_edit_needs_exactly_one_rule_set(values: dict[str, Any]) -> None:
    contract = PluginContract.model_validate(header_edit())
    problems = contract.check_values(values)
    assert [p.rule for p in problems] == ["exactly_one_of"]
    assert "copies every file unchanged" in problems[0].message


def test_malformed_json_rules_are_refused() -> None:
    contract = PluginContract.model_validate(header_edit())
    errors = _errors(contract, {"fileFilter": "dcm", "tagStruct": '{"PatientID": '})
    assert (
        len(errors) == 1
        and "Tag rules (JSON) (--tagStruct) is not valid JSON" in errors[0]
    )


def test_a_preset_that_breaks_its_contract_refuses_the_contract() -> None:
    data = header_edit()
    data["presets"][0]["values"] = {"fileFilter": "dcm"}
    with pytest.raises(ValidationError, match="preset 'basic-header-deid' fails"):
        PluginContract.model_validate(data)


def test_header_only_deid_cannot_declare_dicom_output_phi_free() -> None:
    data = header_edit()
    data["outputs"][0]["phi"] = "none"
    with pytest.raises(ValidationError, match="burned-in pixel data"):
        PluginContract.model_validate(data)
    data["deidentification"]["handles_burned_in_pixels"] = True
    assert PluginContract.model_validate(data).outputs[0].phi == "none"


def test_deidentified_headers_need_private_tags_removed() -> None:
    data = header_edit()
    data["outputs"][0]["phi"] = "headers_deidentified"
    with pytest.raises(ValidationError, match="private tags remain"):
        PluginContract.model_validate(data)
    data["deidentification"]["removes_private_tags"] = True  # as from 1.2.0
    assert PluginContract.model_validate(data).outputs[0].phi == "headers_deidentified"


def test_only_deid_contracts_declare_deidentified_headers() -> None:
    data = tag_extract()
    data["outputs"][0]["phi"] = "headers_deidentified"
    with pytest.raises(ValidationError, match="only a de-identification plugin"):
        PluginContract.model_validate(data)


def test_deid_contracts_need_a_spec_and_a_preset() -> None:
    data = header_edit()
    del data["deidentification"]
    with pytest.raises(ValidationError, match="states what it removes"):
        PluginContract.model_validate(data)
    data = header_edit()
    data["presets"] = []
    with pytest.raises(ValidationError, match="at least one preset"):
        PluginContract.model_validate(data)
    data = tag_extract()
    data["deidentification"] = deepcopy(header_edit()["deidentification"])
    with pytest.raises(ValidationError, match="only a de-identification contract"):
        PluginContract.model_validate(data)


def test_verify_tags_are_keywords() -> None:
    data = header_edit()
    data["deidentification"]["verify_tags"] = ["(0010,0010)"]
    with pytest.raises(ValidationError, match="not a DICOM attribute keyword"):
        PluginContract.model_validate(data)


def test_outputs_always_state_phi() -> None:
    data = tag_extract()
    del data["outputs"][0]["phi"]
    with pytest.raises(ValidationError, match="phi"):
        PluginContract.model_validate(data)


# Against CUBE's own record


@pytest.mark.parametrize(
    ("factory", "cube_file"),
    [
        (tag_extract, "cube-pl-pfdicom_tagExtract-3.2.4.json"),
        (header_edit, "cube-pl-dicom_headerEdit-1.1.8.json"),
    ],
)
def test_contracts_agree_with_cube(factory: Any, cube_file: str) -> None:
    contract = PluginContract.model_validate(factory())
    cube = _cube(cube_file)
    problems = contract.compare_with_cube(cube)
    assert [p for p in problems if p.severity == "error"] == []
    warned = {p.parameter for p in problems}
    assert warned == {row["name"] for row in cube} - {
        p.name for p in contract.parameters
    }


def test_cube_disagreements_are_errors() -> None:
    contract = PluginContract.model_validate(tag_extract())
    cube = _cube("cube-pl-pfdicom_tagExtract-3.2.4.json")
    for row in cube:
        if row["name"] == "outputFileStem":
            row["default"] = "tags"
        if row["name"] == "threads":
            row["type"] = "integer"
    cube = [row for row in cube if row["name"] != "fileFilter"]
    errors = {
        p.message for p in contract.compare_with_cube(cube) if p.severity == "error"
    }
    assert errors == {
        "outputFileStem: the contract's default is '', CUBE's is 'tags'",
        "threads: the contract's type is 'string', CUBE's is 'integer'",
        "fileFilter is in the contract but not in CUBE",
    }


# Contract rules


def test_versions_are_exact() -> None:
    for version in ("^3.2", "3.2", "3.2.x", ">=3.2.4", "v3.2.4"):
        data = tag_extract()
        data["plugin_version"] = version
        with pytest.raises(ValidationError, match="plugin_version"):
            PluginContract.model_validate(data)


def test_plugin_types_and_inputs_agree() -> None:
    data = tag_extract()
    data["inputs"] = []
    with pytest.raises(ValidationError, match="at least one input"):
        PluginContract.model_validate(data)
    data = tag_extract()
    data["plugin_type"] = "fs"
    with pytest.raises(ValidationError, match="no inputs"):
        PluginContract.model_validate(data)


def test_asher_plugins_carry_a_fixture() -> None:
    data = tag_extract()
    data["origin"] = "asher"
    with pytest.raises(ValidationError, match="fixture"):
        PluginContract.model_validate(data)
    data["fixture"] = {
        "description": "One de-identified CT series",
        "location": "tests/fixtures/ct-series",
        "preset": "series-metadata-json",
        "command": "docker run --rm -v $PWD/in:/in -v $PWD/out:/out img tagExtract /in /out",
        "expected_outputs": [{"file_pattern": "*.json"}],
    }
    assert PluginContract.model_validate(data).fixture is not None
    data["fixture"]["preset"] = "nope"
    with pytest.raises(ValidationError, match="unknown preset"):
        PluginContract.model_validate(data)


def test_rules_name_listed_parameters() -> None:
    data = header_edit()
    data["rules"][0]["parameters"] = ["tagStruct", "tagFile"]
    with pytest.raises(ValidationError, match="unknown parameters: tagFile"):
        PluginContract.model_validate(data)


def test_parameter_names_and_flags_are_unique() -> None:
    data = tag_extract()
    data["parameters"].append(deepcopy(data["parameters"][0]))
    with pytest.raises(ValidationError, match="each parameter is listed once"):
        PluginContract.model_validate(data)


# Parameters


def _param(**overrides: Any) -> dict[str, Any]:
    base = {"name": "n", "flag": "--n", "type": "integer", "label": "N", "help": "h"}
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"default": "3"}, "is not an integer"),
        ({"default": True}, "is not an integer"),
        ({"choices": [1, "2"]}, "is not an integer"),
        ({"minimum": 0.5}, "bounds are integers"),
        ({"minimum": 5, "maximum": 1}, "above the maximum"),
        ({"pattern": "[0-9]+", "example": "1"}, "are for text parameters"),
        ({"type": "string", "minimum": 1}, "are for numbers"),
        ({"type": "boolean", "choices": [True]}, "takes no choices"),
        ({"type": "string", "pattern": "[a-z]+"}, "needs a worked example"),
        ({"type": "string", "empty_reason": "x"}, "goes with non_empty"),
        (
            {"type": "string", "pattern": "[a-z]+", "example": "A1"},
            "fails its own checks",
        ),
    ],
)
def test_parameter_definitions_are_checked(
    overrides: dict[str, Any], fragment: str
) -> None:
    with pytest.raises(ValidationError, match=fragment):
        ParameterContract.model_validate(_param(**overrides))


def test_numbers_are_checked_against_range_and_type() -> None:
    param = ParameterContract.model_validate(
        _param(minimum=1, maximum=8, unit="threads", default=2)
    )
    assert param.check(4) == []
    assert param.check(9)[0].message == "N (--n) got 9; the maximum is 8 threads"
    assert param.check(True)[0].message == "N (--n) got True; expected an integer"
    floats = ParameterContract.model_validate(
        _param(type="float", minimum=0, maximum=1)
    )
    assert floats.check(1) == [] and floats.check(0.5) == []


def test_required_parameters_need_a_value() -> None:
    param = ParameterContract.model_validate(_param(optional=False))
    assert param.check(None)[0].message == "N (--n) is required"


def test_regex_text_must_compile() -> None:
    param = ParameterContract.model_validate(
        _param(type="string", text_format="regex", label="Match")
    )
    assert param.check("^CT ") == []
    assert "is not a valid pattern" in param.check("([")[0].message


@pytest.mark.parametrize(
    "pattern",
    ["(?P<x>a)", "(?<x>a)", "(?i)ct", "(?<=a)b", r"\Aab", "[", ""],
)
def test_patterns_must_be_portable(pattern: str) -> None:
    with pytest.raises(ValueError):
        validate_portable_pattern(pattern)


@pytest.mark.parametrize("pattern", [r"(?:a|b)+", r"a(?=b)", r"a(?!b)", r"\(?x\)?"])
def test_portable_patterns_pass(pattern: str) -> None:
    assert validate_portable_pattern(pattern) == pattern


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, False),
        ("", False),
        (False, False),
        (" ", True),
        (0, True),
        ("x", True),
        (True, True),
    ],
)
def test_what_counts_as_set(value: Any, expected: bool) -> None:
    assert is_set(value) is expected


# 0.28.1: chris_plugin.json type names


def lungai() -> dict[str, Any]:
    params = []
    for row in _cube("chris_plugin-pl-lungai-demo-0.1.1.json"):
        kind = {"int": "integer", "bool": "boolean"}.get(row["type"], row["type"])
        params.append(
            {
                "name": row["name"],
                "flag": row["flag"],
                "type": kind,
                "optional": row["optional"],
                "default": row["default"],
                "label": row["name"],
                "help": "h",
            }
        )
    return {
        "plugin_name": "pl-lungai-demo",
        "plugin_version": "0.1.1",
        "plugin_type": "ds",
        "origin": "adopted",
        "title": "LungAI demo",
        "description": "d",
        "inputs": [
            {
                "name": "ct",
                "format": "dicom",
                "file_pattern": "*.dcm",
                "description": "CT",
            }
        ],
        "outputs": [
            {
                "name": "summary",
                "format": "json",
                "file_pattern": "summary.json",
                "phi": "none",
                "description": "counts",
            }
        ],
        "parameters": params,
    }


def test_chris_plugin_json_type_names_are_accepted() -> None:
    contract = PluginContract.model_validate(lungai())
    descriptor = _cube("chris_plugin-pl-lungai-demo-0.1.1.json")
    assert {row["type"] for row in descriptor} == {"bool", "float", "int"}
    assert contract.compare_with_cube(descriptor) == []
    wrong = [
        dict(row, type="str") if row["name"] == "topK" else row for row in descriptor
    ]
    [problem] = contract.compare_with_cube(wrong)
    assert (
        problem.message == "topK: the contract's type is 'integer', CUBE's is 'string'"
    )
