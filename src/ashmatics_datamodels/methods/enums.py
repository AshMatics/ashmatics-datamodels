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
CHAR method-registry and conditional-logic-framework enumerations.

Single source of truth for the governance-method vocabulary shared by the
aigov-framework method registry (``method_registry.yaml``), the CLF v0.6.0
rule grammar (``process-domain-registry.json``), and coreapp's MethodRoute
work (coreapp ADR-031). Authored per aigov-framework ADR-011 §5 and the
Phase 2 handoff (ASHKBAPP-99).

Ontology binding follows the ADR-002 convention: ``x_ontology_scheme`` is
asserted on the model fields that use these enums (``methods.py``), and the
CI guard (``tests/methods/test_ontology_binding.py``) checks every member
resolves in its scheme in ``ashmatics-unified-ontology.ttl``.

Value convention: the five ash facet-scheme enums (and ``ModelClass``) use the
ontology concept LOCAL NAMES (``ap-predictive``, ``of-categorical``, ...) —
these are the canonical CHAR concept IDs used throughout method_registry.yaml
and CLF condition expressions. The ash concepts' ``skos:notation`` values
predate CHAR and differ (``"predictive"``), which is why the binding guard
accepts local names. ``MethodFamily`` values match the family concepts'
``skos:notation`` exactly (minted together in ontology ADR-006).
"""

from enum import Enum


class MethodFamily(str, Enum):
    """
    Method family, the ``skos:broader`` parent of each method concept in
    ``ashcai:GovernanceMethodScheme``. Values match the family concepts'
    ``skos:notation`` and method_registry.yaml ``family`` keys 1:1.
    """

    GROUP_FAIRNESS = "group_fairness"
    INDIVIDUAL_FAIRNESS = "individual_fairness"
    BIAS_MITIGATION = "bias_mitigation"
    VALIDATION_STATISTICS = "validation_statistics"
    DRIFT_DETECTION = "drift_detection"
    EXPLAINABILITY = "explainability"


class MethodPhase(str, Enum):
    """
    Lifecycle phase a method serves: local validation, production
    operations, or both. Method-set ``members`` keys use only the two
    concrete phases; ``both`` appears on methods and junction bindings.
    """

    VALIDATION = "validation"
    OPERATIONAL = "operational"
    BOTH = "both"


class EvidenceType(str, Enum):
    """Kind of reference in a method's mandatory evidence basis (ADR-011)."""

    DOI = "doi"
    ARXIV = "arxiv"
    REF = "ref"
    GUIDANCE = "guidance"
    STANDARD = "standard"
    REGULATION = "regulation"


class DeliveryMode(str, Enum):
    """
    Blueprint delivery mode for a client-approved method set
    (Generate / Augment / Align / Reference, per ADR-011 pipeline).
    """

    GENERATE = "generate"
    AUGMENT = "augment"
    ALIGN = "align"
    REFERENCE = "reference"


# ---------------------------------------------------------------------------
# CLF v0.6.0 rule-grammar enums (process-domain-registry.json,
# conditional_logic_framework; shared with coreapp MethodRoute per ADR-031)
# ---------------------------------------------------------------------------


class ConditionScope(str, Enum):
    """
    Where a CLF condition token resolves: ``org`` (Blueprint context /
    policy wizard responses, instantiation-time) or ``system`` (per-AI-system
    attributes from the AI inventory and risk register, operational-time).
    """

    ORG = "org"
    SYSTEM = "system"


class EvaluationTime(str, Enum):
    """
    When a CLF rule fires: once at Blueprint instantiation (v0.5.0
    behavior, the default) or re-resolved each time an analyst opens a
    review of an AI system.
    """

    INSTANTIATION = "instantiation"
    OPERATIONAL = "operational"


class MethodControlAction(str, Enum):
    """The CLF v0.6.0 ``method_control`` action family (ADR-011 §3)."""

    SET_APPROVED_METHODS = "set_approved_methods"
    RECOMMEND_METHODS = "recommend_methods"
    EXCLUDE_METHODS = "exclude_methods"
    REQUIRE_METHOD_RATIONALE_ON_OVERRIDE = "require_method_rationale_on_override"


# ---------------------------------------------------------------------------
# ash facet-scheme enums (applicability axes). Values are concept local names;
# see module docstring for the local-name-vs-notation convention.
# ---------------------------------------------------------------------------


class AIParadigm(str, Enum):
    """``ash:AIParadigmScheme`` — what the AI system does, architecturally."""

    PREDICTIVE = "ap-predictive"
    FORECASTING = "ap-forecasting"
    GENERATIVE = "ap-generative"
    AGENTIC = "ap-agentic"
    HYBRID = "ap-hybrid"
    NEUROSYMBOLIC = "ap-neurosymbolic"
    RULE_BASED = "ap-rule-based"
    CAUSAL = "ap-causal"


class OutputForm(str, Enum):
    """``ash:OutputFormScheme`` — what kind of artifact the system emits."""

    CATEGORICAL = "of-categorical"
    MEASUREMENT = "of-measurement"
    SEGMENTATION_MASK = "of-segmentation-mask"
    SENTENCE_LABEL = "of-sentence-label"
    STRUCTURED_FINDING = "of-structured-finding"
    NARRATIVE_REPORT = "of-narrative-report"
    REPORT_SECTION = "of-report-section"
    QUESTION_ANSWER = "of-question-answer"
    RECOMMENDATION = "of-recommendation"
    PRIOR_AUTH_DECISION = "of-prior-auth-decision"


class InputModality(str, Enum):
    """``ash:InputModalityScheme`` — data modalities the system consumes."""

    IMAGING = "im-imaging"
    IMAGING_2D = "im-imaging-2d"
    IMAGING_SERIES = "im-imaging-series"
    IMAGING_VOLUMETRIC = "im-imaging-volumetric"
    CLINICAL_TEXT = "im-clinical-text"
    STRUCTURED_CLINICAL = "im-structured-clinical"
    WAVEFORM = "im-waveform"
    AUDIO = "im-audio"
    GENOMIC = "im-genomic"
    ADMINISTRATIVE = "im-administrative"
    VIDEO = "im-video"


class FairnessFactor(str, Enum):
    """``ash:FairnessFactorScheme`` — fairness stratification axes."""

    FAIRNESS = "ff-fairness"
    AGE = "ff-age"
    SEX = "ff-sex"
    GENDER = "ff-gender"
    RACE = "ff-race"
    ETHNICITY = "ff-ethnicity"
    DEMOGRAPHIC = "ff-demographic"
    EDUCATION_LEVEL = "ff-education-level"
    GEOGRAPHIC_LOCATION = "ff-geographic-location"
    HEALTHCARE_ACCESS = "ff-healthcare-access"
    INTERSECTIONALITY = "ff-intersectionality"
    PATIENT_FACTOR = "ff-patient-factor"
    REPRESENTATION = "ff-representation"
    SDOH = "ff-sdoh"
    SOCIOECONOMIC_STATUS = "ff-socioeconomic-status"
    UNDERREPRESENTED_GROUP = "ff-underrepresented-group"


class RobustnessFactor(str, Enum):
    """``ash:RobustnessFactorScheme`` — robustness/artifact stratification axes."""

    ROBUSTNESS = "rf-robustness"
    DATA_ARTIFACT = "rf-data-artifact"
    INTRINSIC_ARTIFACT = "rf-intrinsic-artifact"
    EXTRINSIC_ARTIFACT = "rf-extrinsic-artifact"
    MOTION = "rf-motion"
    ANATOMICAL_VARIATION = "rf-anatomical-variation"
    PATHOLOGICAL_VARIATION = "rf-pathological-variation"
    SCANNER_NOISE = "rf-scanner-noise"
    DISTORTION = "rf-distortion"
    CALIBRATION = "rf-calibration"
    RECONSTRUCTION = "rf-reconstruction"
    ENHANCEMENT = "rf-enhancement"
    ACQUISITION_VARIATION = "rf-acquisition-variation"
    MANUFACTURER = "rf-manufacturer"
    SCANNER_TYPE = "rf-scanner-type"
    SCANNER_CONFIGURATION = "rf-scanner-configuration"
    PROTOCOL = "rf-protocol"


class ModelClass(str, Enum):
    """
    ``ash:ModelClassScheme`` — algorithm/model class, one level finer than
    paradigm (ontology ADR-006). Drives method amenability (e.g. TreeSHAP
    exactness for tree ensembles). No registry v0.1.0 method binds this
    axis yet; the enum lands with the scheme so CLF ``system.modelClass``
    and future applicability entries validate from day one.
    """

    LINEAR = "mc-linear"
    DECISION_RULES = "mc-decision-rules"
    TREE_ENSEMBLE = "mc-tree-ensemble"
    SVM = "mc-svm"
    BAYESIAN_NETWORK = "mc-bayesian-network"
    NEURAL_NETWORK = "mc-neural-network"
    CNN = "mc-cnn"
    RNN_SEQUENCE = "mc-rnn-sequence"
    TRANSFORMER = "mc-transformer"
