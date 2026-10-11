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
    # ashcai:gm-hazard-analysis, ontology 0.20.0 / 2.13.0 (ASHFORGE-828). Six
    # methods chosen per hazard record at SOP-RM-01 Step 5.
    HAZARD_ANALYSIS = "hazard_analysis"


class ForbiddenDecision(str, Enum):
    """
    A decision that applying a method never makes, whoever or whatever applies
    it: a person, a tool, or an assistant proposing into the record. The closed
    list of ``MethodDefinition.forbidden_decisions``, defined in the header of
    the aigov-framework ``method_registry.yaml`` (family ``hazard_analysis``,
    ASHFORGE-828).

    Not ontology-anchored: no scheme mints these, and they are not applicability
    or identity (ontology ADR-006), so nothing in the ontology would carry them.
    """

    DEFINE_SCALES = "define_scales"
    """Set or change the harm model, the P1 and P2 bands, the matrix or an
    acceptability ceiling. They are brought forward at SOP-RM-01 Step 1."""

    SCORE_HARM = "score_harm"
    """Score harm on a dimension. The assessor of that dimension does
    (SOP-RM-01 Step 4)."""

    DECIDE_GATE = "decide_gate"
    """Decide a gate: depth (SOP-RM-01.G2), acceptance (SOP-RM-01.G4), or where
    the equity question is answered (SOP-RM-02.G3)."""

    DESIGN_BIAS_MITIGATION = "design_bias_mitigation"
    """Design a bias mitigation or define a fairness metric. That is the
    fairness practice's (SOP-EF-04)."""


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
    policy wizard responses, instantiation-time), ``system`` (per-AI-system
    attributes from the AI inventory and risk register, operational-time) or
    ``record`` (the features of ONE hazard record, operational-time; CLF
    v0.11.0, ASHFORGE-828). A method chosen per hazard record reads
    ``{{record.*}}``, never ``{{system.harmLevel}}``, which is the maximum over
    a system's records.
    """

    ORG = "org"
    SYSTEM = "system"
    RECORD = "record"


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
    # ontology ADR-008 (seed v2.4.0): the scheme had no continuous probability or
    # score, though cp-risk-stratification is a populated purpose. PROBABILITY is
    # distinct from CATEGORICAL, whose score is an enumerated grade.
    PROBABILITY = "of-probability"
    RISK_SCORE = "of-risk-score"
    LOCALIZATION = "of-localization"
    UNCERTAINTY_MAP = "of-uncertainty-map"


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


class MemberProvenance(str, Enum):
    """
    Where one member of an approved method set came from (ADR-022 D6).

    ``delivery_mode`` is set-level and cannot answer "why this method". An
    auditor's "why is this the bias method for this system" has a materially
    different answer per member, and only the exemplar carries Asher's
    warrant; a governance artifact that cannot distinguish them asserts a
    uniform warrant that does not exist.

    **Two values, where ADR-022 D6 names three origins.** The third,
    operator-selected-for-this-job, is by D5 recorded against the job in the
    customer's datastore and never claimed by CHAR — it cannot appear in an
    ``ApprovedMethodSet``, which is the org's standing approved set rather
    than a job record. No contract in this library represents a job record
    today, so a third member here would be a value nothing could ever
    produce. When that contract lands, it adds the third value; do not add it
    here in anticipation.

    Not ontology-anchored: no scheme mints these, and ADR-022 does not ask
    for one. Recorded as contract-level vocabulary, not an oversight.
    """

    ASHER_EXEMPLAR = "asher_exemplar"
    ORGANIZATIONALLY_ADJUDICATED = "organizationally_adjudicated"
