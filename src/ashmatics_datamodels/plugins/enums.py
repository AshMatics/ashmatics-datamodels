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

"""Vocabularies for ChRIS plugin contracts (forge/watch ADR-010). Record shape, not
ontology-bound."""

from enum import Enum


class PluginType(str, Enum):
    """A ChRIS plugin's type, as CUBE records it."""

    DS = "ds"  # reads an input folder, writes an output folder
    FS = "fs"  # creates data: no input folder
    TS = "ts"  # topology: joins several parents


class PluginParameterType(str, Enum):
    """The parameter types CUBE knows. A CUBE parameter has nothing richer."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PATH = "path"
    UNEXTPATH = "unextpath"


class ContractOrigin(str, Enum):
    """Who wrote the contract (ADR-010 decisions 3 and 4)."""

    ASHER = "asher"  # Asher's own plugin: runtime rules apply, fixture required
    ADOPTED = "adopted"  # a public plugin: Asher wrote the contract, not the code


class PluginRole(str, Enum):
    """What a plugin is for, where that changes the rules (ADR-010 Amendment 1)."""

    GENERAL = "general"
    DEIDENTIFICATION = "deidentification"


class PluginDataFormat(str, Enum):
    """What a plugin reads or writes."""

    DICOM = "dicom"
    JSON = "json"
    CSV = "csv"
    TEXT = "text"
    IMAGE = "image"  # PNG, JPEG and similar renderings
    NIFTI = "nifti"
    OTHER = "other"


class InputLayout(str, Enum):
    """How a plugin expects its input folder to be laid out."""

    ANY_TREE = "any_tree"  # files anywhere below the input folder
    FLAT = "flat"  # files directly in the input folder
    SERIES_PER_FOLDER = "series_per_folder"  # one DICOM series per leaf folder


class OutputPhi(str, Enum):
    """Whether a plugin's output can hold PHI (ADR-010 decision 1; Amendment 1)."""

    NONE = "none"  # cannot hold PHI by construction
    POSSIBLE = "possible"  # may hold PHI: handled like images (ADR-007 decision 3)
    # Headers de-identified by a de-identification plugin; pixel data unchecked.
    HEADERS_DEIDENTIFIED = "headers_deidentified"


class TextFormat(str, Enum):
    """What a string parameter's text is, beyond its pattern."""

    PLAIN = "plain"
    JSON = "json"  # must parse as JSON
    REGEX = "regex"  # must compile as a regular expression


class ParameterRuleKind(str, Enum):
    """Rules across parameters. "Set" means not None, not "" and not False."""

    EXACTLY_ONE_OF = "exactly_one_of"
    AT_MOST_ONE_OF = "at_most_one_of"
    AT_LEAST_ONE_OF = "at_least_one_of"
    REQUIRES = "requires"  # when the first is set, every other one must be set


class ContractProblemSeverity(str, Enum):
    """How serious a problem found by a contract check is."""

    ERROR = "error"  # the run or the contract is refused
    WARNING = "warning"  # shown, but nothing is refused
