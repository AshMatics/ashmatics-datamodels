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
AI System Registry rule vocabularies (ASHFORGE-412, ADR-036 §2.5).

The vocabularies the AI System Registry writes and the governance rule files
will read. Stored per-entry: category, AI type, sourcing channel, deployment
topology (plus ``DeploymentStatus``, bound ahead of coreapp adoption).
Derived, never stored: the SRS-REG-15a obligation triad (``RegistrySourcing``),
the two org-level rollups (``PortfolioSizeBucket``, ``OrgSourcingMix``), and the
CHAR content selector (``SystemClass``, ADR-015) — their derivations live in
:mod:`.derive`. This module is the single source of
truth: coreapp's Django ``TextChoices`` (``core/models/ai_registry.py``) and
the frontend's ``aiRegistryTaxonomies.ts`` are downstream mirrors pinned by
parity tests, and scoring-rule YAMLs must test only these values.

Every value here is a rule-engine key. Changing one is a vocabulary decision
that moves data migrations and rule files with it — never a rename
(SRS-REG-AC-6).

Ontology anchoring is declared in :mod:`.bindings` and enforced by
``tests/registry/test_ontology_binding.py``. Current state (ontology v2.3.0 /
ADR-007): category, AI type, sourcing channel, and deployment status are
BOUND; deployment topology and the derived rollups are deliberately
product-level. ``SystemClass`` is PENDING (ADR-015 open item 5).
"""

from enum import Enum


class RegistryCategory(str, Enum):
    """
    What the system's output is *about* — the customer-facing classification,
    and the registry's most load-bearing vocabulary.

    Decision test: **does the system's output assert something about an
    individual patient's condition or care?**

    - ``CLINICAL`` — yes: detection, diagnosis, treatment planning, monitoring,
      rehab, follow-up. An ICH triage tool is clinical — it detects hemorrhage
      in a specific patient's scan — even though its visible action is worklist
      reordering (cf. ``ash:cp-triage``, a ClinicalPurposeScheme concept).
    - ``OPERATIONAL`` — no individual-patient assertion; the object is care
      delivery itself: patient/staff/resource flow, capacity, census
      forecasting, care-pathway metrics.
    - ``ADMINISTRATIVE`` — the business of healthcare: revenue cycle, coding,
      supply chain, inventory, call-center and refill agents, back-office
      documentation.

    Only the clinical / non-clinical edge carries governance obligations, and
    :func:`ashmatics_datamodels.registry.derive.is_clinical_use` is the
    rule-facing predicate for it — the SRS-REG-03 ``clinical_use`` boolean is
    DERIVED, never stored (ASHFORGE-412 AC-2). The operational /
    administrative boundary is deliberately descriptive-only: a borderline
    call there miscategorizes nothing that rules act on.

    Binds to ``ash:ScopeZoneScheme`` (ontology v2.3.0 / ADR-007, concepts
    ``ash:sz-*``). The ontology allows a system to span zones (multi-value);
    the registry stores ONE primary zone for now — the safe direction, since
    single → multi is an additive migration and multi → single is lossy.
    """

    CLINICAL = "clinical"
    OPERATIONAL = "operational"
    ADMINISTRATIVE = "administrative"


class SystemClass(str, Enum):
    """
    CHAR system class — *what the system does for the organization*, as CHAR's
    content layer asks it (ADR-015). DERIVED from :class:`RegistryCategory` by
    :func:`ashmatics_datamodels.registry.derive.system_class`, never stored:
    the registry stays the single written source, exactly as ``clinical_use``
    and the obligation triad do.

    CHAR splits its corpus into a scope-neutral **core** and **system classes**
    that specialize it. The class is the selector — ``{{system.class}}`` in the
    Conditional Logic Framework, ``class_applicability`` on registry entries —
    so a two-value axis is what the content needs:

    - ``CLINICAL`` — ``RegistryCategory.CLINICAL``. The flagship class; the
      clinical content CHAR ships today.
    - ``ADMINISTRATIVE_OPERATIONAL`` — ``RegistryCategory.OPERATIONAL`` and
      ``RegistryCategory.ADMINISTRATIVE``, collapsed. ADR-015 open item 1 keeps
      these one class id until the second class's content plan shows whether
      revenue cycle, supply chain and facilities actually diverge. The three-way
      :class:`RegistryCategory` remains the stored truth, so splitting later
      widens this derivation rather than re-classifying any entry.

    Three things this is NOT, each of which it has already been mistaken for:

    - **Not a risk tier.** ADR-015 D1 forbids reading "administrative" as
      "low risk"; a prior-authorization denial agent is administrative and
      high-risk. Risk tiering operates *within* a class.
    - **Not ``modelClass``.** ``{{system.class}}`` and ``{{system.modelClass}}``
      sit side by side in the CLF ``system`` scope and are unrelated axes:
      ``modelClass`` is the *technique* (cnn, transformer, tree_ensemble).
      ADR-015's Consequences names reviewer confusion between the two as a real
      failure mode.
    - **Not agentic.** How the system *acts* is
      :class:`RegistryAIType` / ``{{system.actionAuthority}}``, orthogonal to
      what it does. An ambient scribe that files orders is clinical and agentic.

    Values are kebab-case (ADR-015 D4, one canonical spelling), which is why
    ``ADMINISTRATIVE_OPERATIONAL`` is ``"administrative-operational"`` and not
    the snake_case used elsewhere in this module — CHAR's registry validates
    class ids as kebab-case and this enum is the contract for those ids.

    Deliberately unanchored for now: ADR-015 open item 5 defers minting
    ``ashcai:SystemClassScheme`` until the second class's ids are final, since a
    notation fixed in the data plane (ADR-006) is expensive to split. Declared
    ``PENDING`` in :mod:`.bindings` so the gap stays visible.
    """

    CLINICAL = "clinical"
    ADMINISTRATIVE_OPERATIONAL = "administrative-operational"


class SolutionShape(str, Enum):
    """
    CHAR solution shape: *what the solution is, structurally*, as CHAR's
    content layer asks it (SA-11). It is ``{{system.solutionShape}}`` in the
    Conditional Logic Framework.

    - ``VENDED_APPLICATION`` — a supplier's application, used as supplied. The
      organization configures its settings, connects it and monitors it.
    - ``LOCAL_CORE`` — a model or algorithmic core the organization trained,
      adapted or wrote.
    - ``COMPOSED_AGENT`` — an agent or automation the organization authored on
      a supplier's platform. The prompts, tools and knowledge sources are its
      own work. The model and the platform are not.

    Asked at intake as a first read (Triage Record, screen 10), the same way
    ``system.sourcing`` is. CHAR derives the value from the layer dispositions
    of the Sourcing Decision Record at SA.BP01 (``model-core`` built here gives
    ``LOCAL_CORE``, else an orchestration, agent-platform or knowledge-sources
    layer configured or built here gives ``COMPOSED_AGENT``, else
    ``VENDED_APPLICATION``). The derived value governs after registration. A
    difference from the intake answer re-opens the triage route. No function
    in this package derives it yet, because the layer record has no model here.

    Not :class:`RegistrySourcing`. Sourcing says who must originate the
    governance evidence. Shape says what the thing is. A composed agent is
    usually ``hybrid``, but neither value can be read from the other.

    Kebab-case, one canonical spelling, as :class:`SystemClass`. Declared
    ``PRODUCT`` in :mod:`.bindings`.
    """

    VENDED_APPLICATION = "vended-application"
    LOCAL_CORE = "local-core"
    COMPOSED_AGENT = "composed-agent"


class RegistryAIType(str, Enum):
    """
    AI architectural paradigm, for governance routing.

    Binds to ``ash:AIParadigmScheme`` (concepts ``ash:ap-*``; member values
    match ``skos:notation``). ``OTHER`` is a deliberate UI collapse of the
    scheme's finer paradigms (forecasting, hybrid, neurosymbolic, rule-based,
    causal) — a product escape value with no single concept, carved out in
    :mod:`.bindings`. If the registry ever needs the finer split, promote
    members from the scheme; do not invent values.
    """

    PREDICTIVE = "predictive"
    GENERATIVE = "generative"
    AGENTIC = "agentic"
    OTHER = "other"


class SourcingChannel(str, Enum):
    """
    How the system was acquired — the STORED per-entry sourcing field
    (decision 2026-08-03 on ASHFORGE-412: channel is observable fact, so it
    is what the customer answers; the obligation reading is derived). Binds
    to ``ash:SourcingScheme`` (ontology v2.3.0 / ADR-007, ``ash:src-*``).

    - ``COMMERCIAL`` — purchased/licensed product from an AI vendor.
    - ``EHR_EMBEDDED`` — feature of the EHR platform (e.g. an Epic model).
    - ``HOMEGROWN`` — built by or for the organization, including
      commissioned or consultancy-built systems (SRS-REG-15a).
    - ``RESEARCH`` — research-grade system in translational use.
    """

    COMMERCIAL = "commercial"
    EHR_EMBEDDED = "ehr_embedded"
    HOMEGROWN = "homegrown"
    RESEARCH = "research"


class RegistrySourcing(str, Enum):
    """
    Where the validation obligation sits — not who wrote the code. DERIVED
    from :class:`SourcingChannel` by
    :func:`ashmatics_datamodels.registry.derive.sourcing_obligation`, never
    stored (same philosophy as ``clinical_use``): commercial and EHR-embedded
    systems carry a vendor obligation; homegrown and research systems put it
    on the customer (SRS-REG-15a). ``HYBRID`` is reached only via the
    local-adaptation flag — a vendor-channel system the org has tuned or
    retrained. Per-system; the org-level rollup is :class:`OrgSourcingMix`.
    """

    VENDOR = "vendor"
    IN_HOUSE = "in_house"
    HYBRID = "hybrid"


class RegistryDeployment(str, Enum):
    """
    Integration topology, ordered device → cloud. The member order is
    meaningful (SRS-REG-03) and consumers must preserve it — never sort for
    display.

    ``EHR``, ``ENTERPRISE_SYSTEM``, and ``AGENTIC_PLATFORM`` were added for
    ASHFORGE-530/-534's admin/operational catalog broadening: a system
    embedded in the EHR or a broader enterprise application (RCM, ERP, ITSM)
    is a different topology from a device or a PACS worklist, and an
    agent-orchestration platform (Microsoft Copilot Studio and similar) is
    increasingly how administrative and operational AI is actually run.
    ``ENTERPRISE_SYSTEM`` is deliberately one bucket rather than a picker over
    named system types (RCM, ERP, ...) — that finer split, if ever needed, is
    a second-level configuration question, not a first-level deployment
    bucket.

    ``UNKNOWN`` is an answer the customer chose ("not sure yet"). It is never
    a default, and a NULL/unset deployment is never coerced to it
    (SRS-REG-09): the two states mean different things and nothing may
    collapse them.
    """

    EMBEDDED = "embedded"
    PACS = "pacs"
    EHR = "ehr"
    ENTERPRISE_SYSTEM = "enterprise_system"
    PLATFORM = "platform"
    AGENTIC_PLATFORM = "agentic_platform"
    ONPREM = "onprem"
    CLOUD = "cloud"
    UNKNOWN = "unknown"


class DeploymentStatus(str, Enum):
    """
    Lifecycle stage of one deployment — an attribute of the org × application
    edge (``forge:deploysApplication``), never of the product itself. Binds to
    ``ash:DeploymentStatusScheme`` (ontology v2.4.0 / ADR-007 + ADR-008,
    ``ash:ds-*``).

    ``INVESTIGATIONAL`` (ADR-008) is a deployment running under an IRB-reviewed
    research protocol. It is drawn against ``PILOT`` on **oversight, not scale**:
    a pilot is an operational trial of fit the organization decides on its own,
    while an investigational deployment carries human-subjects protections and
    consent obligations. Entries recorded as ``PILOT`` before v2.4.0 may be
    mis-stated; review with the site rather than migrating automatically.

    Orthogonal to :class:`RegistryDeployment` (integration topology). Not yet
    adopted by coreapp's registry model, whose ``RegistryEntryStatus`` stays
    deliberately minimal (active/retired per ADR-036 §2.1) — note ``retired``
    appears in both vocabularies; coreapp adoption is a separate decision.
    """

    EVALUATING = "evaluating"
    PILOT = "pilot"
    VALIDATING = "validating"
    INVESTIGATIONAL = "investigational"
    LIVE = "live"
    PAUSED = "paused"
    RETIRED = "retired"


class PortfolioSizeBucket(str, Enum):
    """
    Org-level portfolio-size bucket, DERIVED from the count of active registry
    entries (ASHFORGE-412 AC-3). The Stage A typed question retires: under
    ADR-035 the count is derived from confirmed systems, so the bucket is
    computed by :func:`ashmatics_datamodels.registry.derive.portfolio_size_bucket`
    (ranges 0 / 1–3 / 4–10 / 11–25 / 26+), never customer-typed.

    Values are the ``token_mappings`` vocabulary the scoring context already
    carries (``governance_context.yaml`` q_ai_portfolio_size) — NOT the
    question option ids. The ``ai_portfolio_size: 25_plus`` example in
    assessment_scoring_engine's docstring uses an option id that never reaches
    the context dict; that live drift specimen is why this module exists.
    """

    NONE = "none"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTENSIVE = "extensive"


class OrgSourcingMix(str, Enum):
    """
    Org-level sourcing rollup, DERIVED from per-system
    :class:`RegistrySourcing` values by
    :func:`ashmatics_datamodels.registry.derive.org_sourcing_mix`
    (ASHFORGE-412 AC-3). The Stage A typed question retires; this preserves
    its proportion vocabulary as a derivation output. Encodes the vendor /
    in-house *mix* — a different axis from the per-system obligation triad.
    """

    VENDOR_ONLY = "vendor_only"
    MOSTLY_VENDOR = "mostly_vendor"
    MIXED = "mixed"
    MOSTLY_INTERNAL = "mostly_internal"
    INTERNAL_ONLY = "internal_only"
