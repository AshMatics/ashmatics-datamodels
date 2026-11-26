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

"""
Plugin contracts for ChRIS plugins (ASHFORGE-980, forge/watch ADR-010).

A CUBE plugin parameter has a name, a type, a flag, a default and a help line, and
nothing else. A :class:`PluginContract` states what that leaves out: what the plugin
reads and writes, the allowed values of each parameter, rules across parameters,
named known-good presets, a test fixture and, for a de-identification plugin, what it
removes and how its output is checked.

One contract covers one plugin name at one exact version. Contracts are JSON, kept in
the plugin's repository (or, for an adopted public plugin, beside the workbench) and
checked by this model.

Two checks are shared by every consumer:

- :meth:`PluginContract.check_values` checks the parameter values of one step before
  it is submitted, and returns :class:`ContractProblem` rows that name the parameter,
  the value and what was expected.
- :meth:`PluginContract.compare_with_cube` compares the contract with CUBE's own
  parameter list (the plugin API or ``chris_plugin.json``). A contract may describe
  only some of a plugin's parameters: unlisted ones are warnings, while a name, flag,
  type or default that disagrees is an error.

Parameter values keep their whitespace: these models turn off the base model's
stripping, because a trailing space in a pattern is a real value.

Patterns are matched against the whole value, in Python here and in the browser by
the workbench editor, so they keep to the part of regex syntax both engines share
(see :func:`validate_portable_pattern`).

Record shape, not ontology-bound.
"""

import json
import re
from typing import Any, Literal

from pydantic import (
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from ashmatics_datamodels.common.base import AshMaticsBaseModel

from .enums import (
    ContractOrigin,
    ContractProblemSeverity,
    InputLayout,
    OutputPhi,
    ParameterRuleKind,
    PluginDataFormat,
    PluginParameterType,
    PluginRole,
    PluginType,
    TextFormat,
)

ParameterValue = StrictBool | StrictInt | StrictFloat | StrictStr
"""A parameter value, typed as CUBE types it. ``True`` is never an integer."""

PLUGIN_NAME_PATTERN = r"^pl-[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$"
PLUGIN_VERSION_PATTERN = r"^[0-9]+\.[0-9]+\.[0-9]+$"
PARAMETER_NAME_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]{0,99}$"
PARAMETER_FLAG_PATTERN = r"^--?[A-Za-z][A-Za-z0-9_-]{0,99}$"
SLUG_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"
DICOM_KEYWORD_PATTERN = r"^[A-Za-z][A-Za-z0-9]{0,63}$"
MODALITY_PATTERN = r"^[A-Z0-9]{2,16}$"
CONTRACT_SCHEMA_VERSION: Literal["1"] = "1"

_VALUE_PREVIEW = 80
_PORTABLE_GROUP_PREFIXES = ("(?:", "(?=", "(?!")
_NON_PORTABLE_ESCAPES = ("\\A", "\\Z", "\\z", "\\G")


def validate_portable_pattern(pattern: str) -> str:
    """Check a pattern that both Python's ``re`` and the browser's RegExp must read
    the same way, and return it unchanged.

    It must compile in Python. Of the ``(?`` group forms only non-capturing groups
    and lookaheads are allowed: named groups, lookbehinds and inline flags are
    written differently in the two engines or are missing from one. ``\\A``, ``\\Z``,
    ``\\z`` and ``\\G`` are refused for the same reason. Matching is always against
    the whole value, so no anchors are needed.
    """
    if not pattern:
        raise ValueError("a pattern may not be empty")
    i = pattern.find("(?")
    while i != -1:
        if not (i > 0 and pattern[i - 1] == "\\") and not pattern.startswith(
            _PORTABLE_GROUP_PREFIXES, i
        ):
            raise ValueError(
                "a pattern may use only (?: (?= and (?! groups, so the browser and "
                f"the backend read it the same way: {pattern!r}"
            )
        i = pattern.find("(?", i + 2)
    for escape in _NON_PORTABLE_ESCAPES:
        if escape in pattern:
            raise ValueError(f"a pattern may not use {escape}: {pattern!r}")
    try:
        re.compile(pattern)
    except re.error as err:
        raise ValueError(f"the pattern does not compile ({err}): {pattern!r}") from err
    return pattern


def is_set(value: ParameterValue | None) -> bool:
    """Whether a value counts as set for a :class:`ParameterRule`.

    None, the empty string and False are unset; everything else, including 0 and a
    string of spaces, is set. Being different from the default is not the test.
    """
    return value is not None and value != "" and value is not False


def _preview(value: ParameterValue | None) -> str:
    text = repr(value)
    return text if len(text) <= _VALUE_PREVIEW else text[: _VALUE_PREVIEW - 3] + "..."


def _a(kind: str) -> str:
    return ("an " if kind[0] in "aeiou" else "a ") + kind


def _type_matches(kind: str, value: ParameterValue) -> bool:
    if kind == PluginParameterType.BOOLEAN.value:
        return isinstance(value, bool)
    if kind == PluginParameterType.INTEGER.value:
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == PluginParameterType.FLOAT.value:
        return isinstance(value, int | float) and not isinstance(value, bool)
    return isinstance(value, str)


def _same_value(theirs: Any, ours: Any) -> bool:
    """Equal, and of the same kind: numbers compare by value, but True is never 1."""
    if isinstance(theirs, bool) or isinstance(ours, bool):
        return type(theirs) is type(ours) and theirs == ours
    numbers = (int, float)
    if isinstance(theirs, numbers) and isinstance(ours, numbers):
        return bool(theirs == ours)
    return type(theirs) is type(ours) and theirs == ours


class ContractProblem(AshMaticsBaseModel):
    """One problem found by a contract check, written for the analyst who must fix it."""

    model_config = ConfigDict(str_strip_whitespace=False)

    severity: ContractProblemSeverity
    parameter: str | None = Field(
        default=None, description="The parameter concerned, when there is one"
    )
    rule: ParameterRuleKind | None = Field(
        default=None, description="The cross-parameter rule broken, when one was"
    )
    message: str = Field(
        ..., description="Names the parameter, the value it got and what it expected"
    )


class ParameterContract(AshMaticsBaseModel):
    """What one CUBE parameter accepts, in words an analyst can use.

    ``name``, ``flag``, ``type``, ``optional`` and ``default`` restate CUBE's record
    (checked by :meth:`PluginContract.compare_with_cube`). ``default`` is recorded as
    CUBE has it, even when the contract's own rules refuse it: a default that makes
    the plugin do nothing is exactly what ``non_empty`` and presets exist to catch.
    """

    model_config = ConfigDict(str_strip_whitespace=False)

    name: str = Field(..., pattern=PARAMETER_NAME_PATTERN, description="CUBE's name")
    flag: str = Field(..., pattern=PARAMETER_FLAG_PATTERN, description="CLI flag")
    type: PluginParameterType
    optional: bool = True
    default: ParameterValue | None = None
    label: str = Field(..., min_length=1, max_length=80, description="Plain words")
    help: str = Field(..., min_length=1, max_length=500)
    advanced: bool = Field(
        default=False,
        description="Collapsed in the editor: presets cover it, and it rarely changes",
    )
    choices: list[ParameterValue] | None = Field(
        default=None, description="The only values allowed, where the set is known"
    )
    minimum: StrictInt | StrictFloat | None = None
    maximum: StrictInt | StrictFloat | None = None
    unit: str | None = Field(default=None, max_length=32)
    pattern: str | None = Field(
        default=None,
        description="A whole-value match for text; see validate_portable_pattern",
    )
    example: str | None = Field(
        default=None, description="A worked example, required with a pattern"
    )
    text_format: TextFormat = TextFormat.PLAIN
    non_empty: bool = Field(
        default=False,
        description="An empty value makes the plugin do nothing, so it is refused",
    )
    forbidden_tokens: list[str] = Field(
        default_factory=list,
        description="Substrings refused anywhere in the value, case-insensitively",
    )

    @field_validator("pattern")
    @classmethod
    def _pattern(cls, value: str | None) -> str | None:
        return None if value is None else validate_portable_pattern(value)

    @field_validator("forbidden_tokens")
    @classmethod
    def _tokens(cls, value: list[str]) -> list[str]:
        if any(not token for token in value):
            raise ValueError("a forbidden token may not be empty")
        return value

    @model_validator(mode="after")
    def _consistent(self) -> "ParameterContract":
        kind = self.type
        numeric = kind in (
            PluginParameterType.INTEGER.value,
            PluginParameterType.FLOAT.value,
        )
        textual = kind in (
            PluginParameterType.STRING.value,
            PluginParameterType.PATH.value,
            PluginParameterType.UNEXTPATH.value,
        )
        if self.default is not None and not _type_matches(kind, self.default):
            raise ValueError(
                f"{self.name}: the default {self.default!r} is not {_a(kind)}"
            )
        if self.choices is not None:
            if not self.choices:
                raise ValueError(f"{self.name}: choices, when given, are not empty")
            if kind == PluginParameterType.BOOLEAN.value:
                raise ValueError(f"{self.name}: a boolean takes no choices")
            for choice in self.choices:
                if not _type_matches(kind, choice):
                    raise ValueError(
                        f"{self.name}: the choice {choice!r} is not {_a(kind)}"
                    )
            if len(set(self.choices)) != len(self.choices):
                raise ValueError(f"{self.name}: each choice is listed once")
        if not numeric and (
            self.minimum is not None or self.maximum is not None or self.unit
        ):
            raise ValueError(f"{self.name}: minimum, maximum and unit are for numbers")
        if kind == PluginParameterType.INTEGER.value:
            for bound in (self.minimum, self.maximum):
                if bound is not None and not isinstance(bound, int):
                    raise ValueError(f"{self.name}: an integer's bounds are integers")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError(f"{self.name}: the minimum is above the maximum")
        if not textual and (
            self.pattern is not None
            or self.example is not None
            or self.text_format != TextFormat.PLAIN.value
            or self.non_empty
            or self.forbidden_tokens
        ):
            raise ValueError(
                f"{self.name}: pattern, example, text format, non-empty and forbidden "
                "tokens are for text parameters"
            )
        if self.pattern is not None and self.example is None:
            raise ValueError(f"{self.name}: a pattern needs a worked example")
        if self.example is not None:
            problems = self.check(self.example)
            if problems:
                raise ValueError(
                    f"{self.name}: the example fails its own checks: {problems[0].message}"
                )
        return self

    def check(self, value: ParameterValue | None) -> list[ContractProblem]:
        """Check one value against this parameter. An unset optional value with no
        ``non_empty`` rule passes; its default is what the plugin will use."""
        problems: list[ContractProblem] = []

        def fail(message: str) -> None:
            problems.append(
                ContractProblem(
                    severity=ContractProblemSeverity.ERROR,
                    parameter=self.name,
                    message=message,
                )
            )

        kind = self.type
        if value is None or value == "":
            if self.non_empty:
                fail(
                    f"{self.label} ({self.flag}) must not be empty: with no value the "
                    "plugin does nothing"
                )
            elif value is None and not self.optional:
                fail(f"{self.label} ({self.flag}) is required")
            return problems
        if not _type_matches(kind, value):
            fail(
                f"{self.label} ({self.flag}) got {_preview(value)}; expected {_a(kind)}"
            )
            return problems
        if self.choices is not None and value not in self.choices:
            allowed = ", ".join(repr(c) for c in self.choices)
            fail(
                f"{self.label} ({self.flag}) got {_preview(value)}; expected one of {allowed}"
            )
        if isinstance(value, int | float) and not isinstance(value, bool):
            unit = f" {self.unit}" if self.unit else ""
            if self.minimum is not None and value < self.minimum:
                fail(
                    f"{self.label} ({self.flag}) got {value}; the minimum is {self.minimum}{unit}"
                )
            if self.maximum is not None and value > self.maximum:
                fail(
                    f"{self.label} ({self.flag}) got {value}; the maximum is {self.maximum}{unit}"
                )
        if isinstance(value, str):
            if self.pattern is not None and re.fullmatch(self.pattern, value) is None:
                fail(
                    f"{self.label} ({self.flag}) got {_preview(value)}; it should look "
                    f"like {self.example!r}"
                )
            lowered = value.lower()
            for token in self.forbidden_tokens:
                if token.lower() in lowered:
                    fail(f"{self.label} ({self.flag}) may not contain {token!r}")
            if self.text_format == TextFormat.JSON.value:
                try:
                    json.loads(value)
                except ValueError as err:
                    fail(
                        f"{self.label} ({self.flag}) is not valid JSON ({err.args[0]})"
                    )
            elif self.text_format == TextFormat.REGEX.value:
                try:
                    re.compile(value)
                except re.error as err:
                    fail(f"{self.label} ({self.flag}) is not a valid pattern ({err})")
        return problems


class ParameterRule(AshMaticsBaseModel):
    """A rule across parameters, which CUBE cannot express. See :func:`is_set`."""

    kind: ParameterRuleKind
    parameters: list[str] = Field(..., min_length=2)
    message: str = Field(..., min_length=1, description="Shown when the rule is broken")

    @model_validator(mode="after")
    def _distinct(self) -> "ParameterRule":
        if len(set(self.parameters)) != len(self.parameters):
            raise ValueError("a rule names each parameter once")
        return self

    def broken(self, values: dict[str, ParameterValue | None]) -> bool:
        flags = [is_set(values.get(name)) for name in self.parameters]
        count = sum(flags)
        if self.kind == ParameterRuleKind.EXACTLY_ONE_OF.value:
            return count != 1
        if self.kind == ParameterRuleKind.AT_MOST_ONE_OF.value:
            return count > 1
        if self.kind == ParameterRuleKind.AT_LEAST_ONE_OF.value:
            return count < 1
        return flags[0] and not all(flags[1:])


class PluginInput(AshMaticsBaseModel):
    """What a plugin reads from its input folder."""

    name: str = Field(..., pattern=SLUG_PATTERN)
    format: PluginDataFormat
    file_pattern: str = Field(..., min_length=1, description="A glob, e.g. *.dcm")
    min_files: int = Field(default=1, ge=1)
    layout: InputLayout = InputLayout.ANY_TREE
    modalities: list[str] = Field(
        default_factory=list, description="DICOM modality codes, e.g. CT; empty = any"
    )
    description: str = Field(..., min_length=1)

    @field_validator("modalities")
    @classmethod
    def _modalities(cls, value: list[str]) -> list[str]:
        for code in value:
            if re.fullmatch(MODALITY_PATTERN, code) is None:
                raise ValueError(f"{code!r} is not a DICOM modality code")
        if len(set(value)) != len(value):
            raise ValueError("each modality is listed once")
        return value


class PluginOutput(AshMaticsBaseModel):
    """What a plugin promises to write. ``phi`` has no default: it is always stated."""

    name: str = Field(..., pattern=SLUG_PATTERN)
    format: PluginDataFormat
    file_pattern: str = Field(..., min_length=1, description="A glob, e.g. *.json")
    min_count: int = Field(
        default=1,
        ge=0,
        description="Fewer files than this after a run is a failure, not a success",
    )
    phi: OutputPhi
    description: str = Field(..., min_length=1)


class PluginPreset(AshMaticsBaseModel):
    """A named, known-good setting. It must pass every check of its contract."""

    model_config = ConfigDict(str_strip_whitespace=False)

    name: str = Field(..., pattern=SLUG_PATTERN)
    label: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1)
    values: dict[str, ParameterValue] = Field(default_factory=dict)


class FixtureOutput(AshMaticsBaseModel):
    """An output that running on the fixture must produce."""

    file_pattern: str = Field(..., min_length=1)
    min_count: int = Field(default=1, ge=1)


class PluginFixture(AshMaticsBaseModel):
    """A small test dataset and what running on it must produce (ADR-010 decision 1)."""

    model_config = ConfigDict(str_strip_whitespace=False)

    description: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1, description="Repository path or URI")
    preset: str | None = Field(default=None, description="The preset the run uses")
    command: str | None = Field(
        default=None, description="The one-line local docker run (decision 3)"
    )
    expected_outputs: list[FixtureOutput] = Field(..., min_length=1)


class DeidentificationSpec(AshMaticsBaseModel):
    """What a de-identification plugin's presets guarantee (ADR-010 Amendment 1).

    ``verify_tags`` are the attributes the post-run check reads back: after the step
    each must be absent, empty or different from its input value. The check reports
    tag keywords only, never values.
    """

    verify_tags: list[str] = Field(..., min_length=1)
    removes_private_tags: bool
    handles_burned_in_pixels: bool
    notes: str | None = None

    @field_validator("verify_tags")
    @classmethod
    def _keywords(cls, value: list[str]) -> list[str]:
        for keyword in value:
            if re.fullmatch(DICOM_KEYWORD_PATTERN, keyword) is None:
                raise ValueError(f"{keyword!r} is not a DICOM attribute keyword")
        if len(set(value)) != len(value):
            raise ValueError("each tag is listed once")
        return value


class PluginContract(AshMaticsBaseModel):
    """The contract for one ChRIS plugin at one exact version (ADR-010 decision 2)."""

    schema_version: Literal["1"] = CONTRACT_SCHEMA_VERSION
    plugin_name: str = Field(..., pattern=PLUGIN_NAME_PATTERN)
    plugin_version: str = Field(
        ...,
        pattern=PLUGIN_VERSION_PATTERN,
        description="One exact version, never a range",
    )
    plugin_type: PluginType
    origin: ContractOrigin
    role: PluginRole = PluginRole.GENERAL
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1)
    source_repository: str | None = None
    image: str | None = Field(default=None, description="Container image reference")
    inputs: list[PluginInput] = Field(default_factory=list)
    outputs: list[PluginOutput] = Field(..., min_length=1)
    parameters: list[ParameterContract] = Field(default_factory=list)
    rules: list[ParameterRule] = Field(default_factory=list)
    presets: list[PluginPreset] = Field(default_factory=list)
    fixture: PluginFixture | None = None
    deidentification: DeidentificationSpec | None = None

    @model_validator(mode="after")
    def _consistent(self) -> "PluginContract":
        names = [p.name for p in self.parameters]
        if len(set(names)) != len(names):
            raise ValueError("each parameter is listed once")
        flags = [p.flag for p in self.parameters]
        if len(set(flags)) != len(flags):
            raise ValueError("each flag is listed once")
        for group, items in (("input", self.inputs), ("output", self.outputs)):
            item_names = [i.name for i in items]
            if len(set(item_names)) != len(item_names):
                raise ValueError(f"each {group} name is listed once")

        if self.plugin_type == PluginType.FS.value and self.inputs:
            raise ValueError("an fs plugin reads no input folder, so it has no inputs")
        if self.plugin_type != PluginType.FS.value and not self.inputs:
            raise ValueError("a ds or ts plugin states at least one input")

        known = set(names)
        for rule in self.rules:
            unknown = [n for n in rule.parameters if n not in known]
            if unknown:
                raise ValueError(
                    f"a rule names unknown parameters: {', '.join(unknown)}"
                )

        preset_names = [p.name for p in self.presets]
        if len(set(preset_names)) != len(preset_names):
            raise ValueError("each preset name is used once")
        for preset in self.presets:
            errors = [
                p
                for p in self.check_values(preset.values)
                if p.severity == ContractProblemSeverity.ERROR.value
            ]
            if errors:
                raise ValueError(
                    f"preset {preset.name!r} fails its contract: {errors[0].message}"
                )

        if self.origin == ContractOrigin.ASHER.value and self.fixture is None:
            raise ValueError(
                "an Asher plugin's contract carries its fixture (decision 3)"
            )
        if self.fixture is not None and self.fixture.preset is not None:
            if self.fixture.preset not in preset_names:
                raise ValueError(
                    f"the fixture names an unknown preset {self.fixture.preset!r}"
                )

        deid = self.role == PluginRole.DEIDENTIFICATION.value
        if deid and self.deidentification is None:
            raise ValueError("a de-identification contract states what it removes")
        if not deid and self.deidentification is not None:
            raise ValueError(
                "only a de-identification contract has a de-identification spec"
            )
        if deid and not self.presets:
            raise ValueError("a de-identification contract has at least one preset")
        for output in self.outputs:
            if output.phi == OutputPhi.HEADERS_DEIDENTIFIED.value and not deid:
                raise ValueError(
                    f"output {output.name!r}: only a de-identification plugin can "
                    "declare de-identified headers"
                )
            if (
                deid
                and self.deidentification is not None
                and not self.deidentification.handles_burned_in_pixels
                and output.format == PluginDataFormat.DICOM.value
                and output.phi == OutputPhi.NONE.value
            ):
                raise ValueError(
                    f"output {output.name!r}: a plugin that does not handle burned-in "
                    "pixel data cannot declare its DICOM output free of PHI"
                )
        return self

    def parameter(self, name: str) -> ParameterContract | None:
        """The parameter called ``name``, if the contract lists it."""
        return next((p for p in self.parameters if p.name == name), None)

    def effective_values(
        self, values: dict[str, ParameterValue]
    ) -> dict[str, ParameterValue | None]:
        """The listed parameters' defaults, overlaid with ``values``."""
        merged: dict[str, ParameterValue | None] = {
            p.name: p.default for p in self.parameters
        }
        merged.update(values)
        return merged

    def check_values(self, values: dict[str, ParameterValue]) -> list[ContractProblem]:
        """Check one step's parameter values, over the defaults, before it is submitted.

        Returns every problem rather than the first, so the editor can mark each
        field. An empty list means the contract accepts the step.
        """
        problems: list[ContractProblem] = []
        for name in values:
            if self.parameter(name) is None:
                problems.append(
                    ContractProblem(
                        severity=ContractProblemSeverity.ERROR,
                        parameter=name,
                        message=f"{name} is not a parameter this contract knows",
                    )
                )
        effective = self.effective_values(values)
        for param in self.parameters:
            problems.extend(param.check(effective.get(param.name)))
        for rule in self.rules:
            if rule.broken(effective):
                problems.append(
                    ContractProblem(
                        severity=ContractProblemSeverity.ERROR,
                        rule=rule.kind,
                        message=rule.message,
                    )
                )
        return problems

    def compare_with_cube(
        self, cube_parameters: list[dict[str, Any]]
    ) -> list[ContractProblem]:
        """Compare the contract with CUBE's parameter list for the same plugin version.

        ``cube_parameters`` is the plugin API's ``results`` or ``chris_plugin.json``'s
        ``parameters``: dicts with ``name``, ``type``, ``flag``, ``optional`` and
        ``default``. A listed parameter missing from CUBE, or disagreeing with it, is
        an error. A CUBE parameter the contract leaves out is a warning.
        """
        problems: list[ContractProblem] = []
        by_name = {str(p.get("name")): p for p in cube_parameters}
        for param in self.parameters:
            cube = by_name.get(param.name)
            if cube is None:
                problems.append(
                    ContractProblem(
                        severity=ContractProblemSeverity.ERROR,
                        parameter=param.name,
                        message=f"{param.name} is in the contract but not in CUBE",
                    )
                )
                continue
            for field, ours in (
                ("type", param.type),
                ("flag", param.flag),
                ("optional", param.optional),
                ("default", param.default),
            ):
                theirs = cube.get(field)
                if field == "default" and theirs is None and not param.optional:
                    continue  # CUBE keeps no default for a required parameter
                if not _same_value(theirs, ours):
                    problems.append(
                        ContractProblem(
                            severity=ContractProblemSeverity.ERROR,
                            parameter=param.name,
                            message=(
                                f"{param.name}: the contract's {field} is {ours!r}, "
                                f"CUBE's is {theirs!r}"
                            ),
                        )
                    )
        listed = {p.name for p in self.parameters}
        for name in by_name:
            if name not in listed:
                problems.append(
                    ContractProblem(
                        severity=ContractProblemSeverity.WARNING,
                        parameter=name,
                        message=f"{name} is in CUBE but the contract leaves it out",
                    )
                )
        return problems
