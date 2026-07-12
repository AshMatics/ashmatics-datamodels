# Asher FORGE Clinical AI Use-Case Ontology and Information Architecture Update

## Overview

This document updates the earlier clinical AI use-case taxonomy and information architecture analysis in light of June 2026 platform direction, current ontology work, and the explicit need to represent agentic systems as first-class governed objects. The central conclusion is that the prior taxonomy remains structurally sound, but it now needs a formal agentic layer that captures planning, tool use, action authority, memory, and human control in a way that fits the existing governance, lifecycle, and knowledge graph architecture.[cite:81][cite:82][cite:84][cite:86]

The current product architecture is already well positioned for this extension. Asher FORGE now functions as the umbrella platform, with Asher Ontologies as the semantic layer, Asher Knowledge Graph as the connected reasoning layer, and the three studio surfaces—AI-Governance Studio, AI-Select Studio, and AI-Watch Studio—as the main operational products that consume and operationalize the ontology and graph.[cite:81][cite:86]

## Current architectural baseline

The February 2026 work established a mature governance structure organized into five capability clusters: Strategy and Leadership, Risk Ethics and Compliance, Data Model and System Lifecycle, Operations and Workflow Integration, and Vendor Partners and Ecosystem.[cite:81][cite:82] It also established an operational lifecycle split into pre-implementation, implementation or go-live, and post-implementation phases, with always-on oversight and administrative functions spanning the lifecycle.[cite:81]

That framing remains valid in June 2026 because it already separates organizational capability from runtime execution. This distinction is especially important for agentic systems, where the governance question is not only what a model predicts, but what the system may decide, invoke, or execute within a workflow.[cite:81][cite:84][cite:86]

The maturity questionnaire also already anticipates a more advanced operating model. It includes embedded leadership roles such as algorithmic consultants, mature lifecycle management, systematic measurement and learning, and proactive vendor and ecosystem strategy, all of which are highly relevant precursors to governing agentic systems.[cite:84]

## Existing ontology posture

The ontology and data model coupling ADR establishes a three-layer contract: the ontology owns concepts and legal relationship types, Pydantic models own the operational shape of instances, and the knowledge base owns runtime assertions about specific objects.[cite:86] That decision is a strong foundation for extending into agentic systems because it avoids overloading OWL classes with operational detail while still requiring a deterministic semantic backbone for agents and wizards.[cite:86]

The same ADR also states that ontology concepts should be promoted when they are shared across systems, participate in typed relationships, or are reasoned over by the platform.[cite:86] Agentic system concepts clearly meet all three criteria, since they cross product boundaries, require typed governance relationships, and will be used in scope-gating, recommendation, retrieval, and studio workflows.[cite:86]

The pasted ontology content confirms that the current semantic estate already spans multiple namespaces and responsibilities. The `ash` namespace appears to hold core clinical AI and product concepts such as `AIapplication`, `Regulatorystatus`, `Deviceclass`, and general semantic relationships like `supports`, `contradicts`, and `equivalent_to`, while the governance/process vocabulary currently appears in the CAI namespace shown as `https://ashmatics.com/ontology/cai#`, including `PolicyDomain`, `ProcessDomain`, `RegulatoryRequirement`, `ExemplarControl`, and related object properties such as `specifiedBy`, `validatedBy`, `implementedThrough`, and `governsProduct`.[cite:87]

The June 2026 ADR, however, refers to the namespaces as `ash`, `ashcai`, and `forge`, with PROV-O, SKOS, and P-Plan as underlying scaffolds.[cite:86] That suggests the pasted file likely reflects either a partial export, a prior serialization, or a mixed-state namespace posture rather than the complete current canonical ontology package.[cite:86][cite:87]

## Recommended namespace interpretation

The cleanest semantic interpretation of the current architecture is:

| Namespace | Recommended responsibility | Notes |
|---|---|---|
| `ash` | Core domain ontology for clinical AI concepts, products, clinical use cases, device classes, data types, regulatory statuses, and cross-domain semantic relationships | This is already visible in the pasted ontology with classes such as `AIapplication` and `Regulatorystatus`.[cite:87] |
| `ashcai` | Clinical AI governance, policy, process, controls, evidence, lifecycle templates, and operational governance semantics | ADR-002 uses `ashcai` in this role, and the pasted file shows this layer under a CAI namespace even if the prefix differs.[cite:86][cite:87] |
| `forge` | Customer- and runtime-scoped operating context for Asher FORGE, including organizational units, governance authority, deployment context, and studio-consumable instance semantics | ADR-002 explicitly places customer scope-gating and governance authority in `forge`.[cite:86] |

This three-namespace model is coherent and should be retained. It gives Asher FORGE a clear separation between domain semantics, governance semantics, and deployed enterprise context, which is exactly what is needed if studios are to work deterministically over customer-specific scope and policy state.[cite:86]

## What changes in June 2026

The main update is not a replacement of the prior taxonomy. The update is that agentic systems must now be represented as a first-class semantic layer above the classical model taxonomy and below governance and operational controls.[cite:81][cite:86]

In earlier clinical AI catalogs, most use cases could be described using categories such as assessment, triage, diagnosis, prediction, quantification, monitoring, and intervention. That remains necessary, but it is no longer sufficient because a contemporary clinical AI system may also plan, orchestrate, call tools, maintain memory, route tasks, draft actions, or initiate multi-step workflows under bounded authority.[cite:81][cite:84][cite:86]

This means a use case like “draft a prior-authorization summary,” “prepare follow-up actions from a radiology result,” or “triage inbox messages and launch downstream tasks” is not adequately described by clinical purpose alone. It also needs a machine-readable description of agency, execution rights, oversight model, and memory scope.[cite:86]

## Agentic extension to the ontology

The recommended approach is to preserve the existing clinical use-case taxonomy and add a new cross-cutting layer called an Agentic System Profile. This should be modeled as a governed concept set and relationship pattern rather than as a loose note or free-text tag, because the platform will need to reason over it inside selection, governance, and monitoring workflows.[cite:81][cite:86]

A practical high-level pattern would look like this:

- `ash:ClinicalAIUseCase` or equivalent core use-case concept remains the anchor use-case object.[cite:87]
- `ash:AIapplication` remains the application or product-level object for a specific system or tool.[cite:87]
- A new `ash:AgenticCapabilityProfile` or `forge:AgenticSystemProfile` represents the operational agency characteristics of the system.[cite:86]
- The governance layer in `ashcai` binds that profile to oversight, validation, change, transparency, and monitoring requirements.[cite:81][cite:86]

The profile should capture at least the following semantic dimensions.

| Dimension | Why it matters | Suggested modeling posture |
|---|---|---|
| Agency level | Distinguishes assistive AI from delegated execution | Controlled vocabulary / concept scheme |
| Goal scope | Distinguishes single-step help from episode or longitudinal workflow management | Controlled vocabulary |
| Planning behavior | Captures whether the system creates and revises action sequences | Boolean plus concept scheme |
| Tool authority | Captures external system access and callable actions | Object properties to allowed tools or system functions |
| Memory scope | Captures whether context is session-only, episodic, or persistent | Controlled vocabulary |
| Human approval model | Captures approval gates and override authority | Link to oversight policy and runtime control model |
| Autonomy failure mode | Captures principal governance risk | Controlled vocabulary linked to risk controls |
| Execution environment | Distinguishes advisory interface, orchestration layer, embedded workflow engine, or autonomous background process | Controlled vocabulary |

These dimensions fit the existing ontology-coupling ADR because they are shared, typed, and reasoned-over concepts. The more detailed runtime payloads, event logs, prompts, confidence traces, and execution metadata should remain in Pydantic and the knowledge base rather than being elevated into the ontology itself.[cite:86]

## Proposed semantic additions

The following additions would be consistent with the current architecture.

### Core classes

| Proposed class | Likely namespace | Purpose |
|---|---|---|
| `ash:AgenticSystem` | `ash` | A clinical AI application or software system with bounded capability to plan, invoke tools, or execute actions toward a goal |
| `ash:AgenticCapabilityProfile` | `ash` | Semantic profile that characterizes agency, planning, memory, tool use, and execution posture |
| `ash:AgencyLevel` | `ash` | Controlled concept scheme for degree of autonomy |
| `ash:ToolCapability` | `ash` | Declared callable capability or tool type |
| `ash:MemoryScope` | `ash` | Session, encounter, episode, longitudinal, or persistent memory semantics |
| `ash:PlanningMode` | `ash` | No planning, single-step planning, multi-step planning, adaptive planning |
| `ash:ExecutionAuthority` | `ash` | Read-only, propose-only, prepare-only, approve-required, bounded-execute |
| `ash:HumanControlModel` | `ash` | Human in the loop, on the loop, in command, retrospective review |
| `ash:AgenticRiskType` | `ash` | Common risk patterns for goal drift, unsafe execution, overreach, memory leakage, or inappropriate tool invocation |

### Key relationships

| Proposed property | Purpose |
|---|---|
| `ash:hasAgenticProfile` | Links application or use case to its capability profile |
| `ash:hasAgencyLevel` | Links profile to autonomy concept |
| `ash:hasPlanningMode` | Links profile to planning concept |
| `ash:hasMemoryScope` | Links profile to memory concept |
| `ash:mayInvoke` | Links profile or system to approved tools/capabilities |
| `ash:requiresApprovalModel` | Links profile to human control model |
| `ash:hasExecutionAuthority` | Links profile to bounded action authority |
| `ash:hasPrimaryAgenticRisk` | Links profile to risk concepts |
| `ashcai:governedUnder` | Links agentic profile or system to the relevant policy domain(s) |
| `ashcai:monitoredBy` | Links to monitoring and oversight controls |
| `ashcai:validatedBy` | Reuses existing validation linkage patterns where appropriate |

These additions can be implemented incrementally. They do not require a rewrite of the ontology, and they align with the current ADR guidance to bind operational detail selectively while keeping the ontology as the deterministic contract.[cite:86]

## Recommended agentic vocabulary

A compact initial vocabulary is better than an elaborate one. The following five-level agency scheme would work well for Asher FORGE because it is interpretable by users, governable by policy, and queryable in the graph.

| Level | Label | Meaning |
|---|---|---|
| A0 | Non-agentic | Produces output but does not plan or invoke tools |
| A1 | Assistive | Supports a user in one step; no tool use beyond immediate task support |
| A2 | Tool-using | Can call approved tools or retrieve context, but action remains user-mediated |
| A3 | Orchestrating | Can coordinate multi-step tasks across tools under bounded policy and approval gates |
| A4 | Delegated | Can execute bounded actions in production workflows with active monitoring, override, and strict scope controls |

This should be paired with a separate execution authority scheme so that planning ability and action rights do not get conflated. A system may be sophisticated in planning but still have propose-only authority, which is an important governance distinction.[cite:81][cite:86]

## Integration with the five capability clusters

The existing five-cluster governance model remains the right shell for agentic governance, but each cluster should now explicitly account for agentic systems.[cite:81][cite:82]

| Capability cluster | Agentic update |
|---|---|
| Strategy and Leadership | Add explicit portfolio posture on agentic AI, delegation limits, and approved operating models for different clinical domains.[cite:81][cite:84] |
| Risk Ethics and Compliance | Add goal-drift risk, unsafe action risk, memory/privacy leakage, tool misuse, and escalation design for agentic execution.[cite:81][cite:86] |
| Data Model and System Lifecycle | Add prompt and tool configuration versioning, memory policy, orchestration design review, and scenario-based validation for multi-step execution.[cite:81][cite:86] |
| Operations and Workflow Integration | Add runtime observability of action chains, approval checkpoints, reversible actions, and incident analysis for agentic workflows.[cite:81] |
| Vendor Partners and Ecosystem | Add vendor due diligence specific to agent frameworks, tool permissions, hosted memory, auditability, and external action boundaries.[cite:81][cite:84] |

The five-cluster model therefore does not need replacement. It needs an explicit agentic interpretation layer and some new controls, evidence artifacts, and maturity criteria.[cite:81][cite:84]

## Implications for the studios

The current branded studio structure is strong and should now be sharpened around the agentic extension.

### AI-Governance Studio

AI-Governance Studio should be the place where organizations define allowable agency levels, required approval models, memory rules, escalation design, and risk controls for agentic systems. In ontology terms, this studio consumes `ashcai` governance concepts and binds them to `ash` use cases and `forge` customer scope context.[cite:81][cite:86]

### AI-Select Studio

AI-Select Studio should use the ontology and graph to classify candidate use cases and products by both clinical purpose and agentic posture. This is where the new profile becomes highly valuable, because selection decisions in 2026 increasingly depend not just on model quality but on whether the system is advisory, tool-using, orchestrating, or delegated.[cite:81][cite:86]

### AI-Watch Studio

AI-Watch Studio should operationalize post-deployment monitoring for both classical and agentic systems. For agentic systems in particular, it should monitor not only performance drift and bias, but also action-chain integrity, approval bypass attempts, unexpected tool sequences, override patterns, memory-boundary violations, and incidents tied to orchestration behavior.[cite:81][cite:84][cite:86]

## Data model and ontology coupling implications

The June 2026 ADR already gives the right mechanism for introducing this into the code stack. Agentic concepts should be introduced as ontology classes and properties only where they are shared, typed, and reasoned over, while detailed payloads remain in `ashmatics-datamodels` with `x_ontology_class`, `x_ontology_property`, and `x_ontology_scheme` annotations validated in CI.[cite:86]

That means the ontology should define concepts like agentic system, agency level, memory scope, planning mode, execution authority, and tool capability, while the Pydantic models should carry concrete fields such as:

- `approval_required: bool`
- `max_tools_per_run: int`
- `allowed_tool_ids: list[str]`
- `memory_retention_days: int | None`
- `action_categories: list[str]`
- `can_write_back_to_ehr: bool`
- `human_reviewer_role: str | None`
- `runtime_trace_id: str`

These are operationally necessary but should not all become ontology terms. The ontology should name the categories and legal relationships; the data models should carry the full wire/storage shape.[cite:86]

## Suggested documentation and naming refinements

A few naming refinements would improve coherence.

1. Use **Asher FORGE** consistently as the umbrella platform name in architecture and product documents.[cite:86]
2. Prefer **Asher Ontologies** for the full semantic estate and reserve namespace terms such as `ash`, `ashcai`, and `forge` for technical documentation.[cite:86][cite:87]
3. Use **Asher Knowledge Graph** for the connected runtime and reasoning layer that projects ontology truth plus instance assertions into the operational graph.[cite:86]
4. In studio-facing materials, describe the stack as: Ontologies → Knowledge Graph → Studios, because that accurately reflects the semantic dependency chain.[cite:81][cite:86]

## Recommended next moves

The recommended next sequence is:

1. Confirm the canonical namespace posture in the current ontology repo and decide whether the CAI namespace in the pasted file should be normalized to `ashcai` in the next ontology release.[cite:86][cite:87]
2. Add a compact agentic vocabulary and capability profile to the ontology, starting with agency level, planning mode, memory scope, execution authority, human control model, tool capability, and agentic risk type.[cite:86]
3. Add corresponding `x_ontology_*` annotations to a small number of Pydantic models representing agentic systems, tool permissions, and governance review artifacts, then enforce them with the CI approach already chosen in ADR-002.[cite:86]
4. Update the five-cluster governance documentation and maturity questionnaire so that each cluster has an explicit agentic interpretation.[cite:81][cite:84]
5. Introduce agentic-aware classification and recommendation logic in AI-Select Studio and monitoring semantics in AI-Watch Studio, with AI-Governance Studio as the policy-authoring and approval surface.[cite:81][cite:86]

## Proposed compact JSON shape

The following JSON shape is a practical bridge between ontology and datamodel work. It is not intended to replace existing models, but to show how a use case can carry an agentic profile cleanly.

```json
{
  "use_case_id": "UC-1234",
  "title": "Radiology follow-up orchestration assistant",
  "clinical_purpose": "care_coordination",
  "ai_mode": ["generative", "agentic"],
  "agentic_profile": {
    "agency_level": "A3",
    "planning_mode": "multi_step_adaptive",
    "goal_scope": "episode_of_care",
    "memory_scope": "encounter_plus_episode",
    "execution_authority": "approve_required",
    "human_control_model": "human_on_the_loop_with_required_signoff",
    "allowed_tools": ["ehr_inbasket", "task_router", "document_summarizer"],
    "primary_agentic_risks": ["goal_drift", "tool_misuse", "privacy_leakage"],
    "writes_to_system_of_record": false
  },
  "governance_bindings": {
    "policy_domains": ["HOP-001", "RMP-001", "MMP-001", "LTP-001"],
    "required_validation": ["scenario_validation", "human_factors_review"],
    "monitoring_profile": "agentic_orchestration_standard"
  }
}
```

This pattern respects the ADR-002 contract because the ontology owns the semantic categories and legal relationships, while the runtime model carries the operational fields that products and services need.[cite:86]

## Conclusion

The earlier Ashmatics work remains directionally correct and still provides the right backbone for Asher FORGE in June 2026.[cite:81][cite:82] The most important update is to make agentic systems first-class governed entities by introducing an explicit Agentic System Profile that sits between the clinical use-case layer and the governance/runtime layers.[cite:86]

The current three-namespace posture—`ash`, `ashcai`, and `forge`—is a strength, not a complication, so long as their responsibilities are made explicit and kept stable.[cite:86] In practical terms, `ash` should continue to hold the core domain concepts, `ashcai` should hold governance and operational governance semantics, and `forge` should hold customer and runtime operating context for the platform and its studios.[cite:86][cite:87]

With that extension, Asher FORGE can represent not only what a clinical AI use case is about, but also how independently the system acts, what it is allowed to do, how it is controlled, and how it should be monitored over time. That is the key semantic move that makes the platform fit for the June 2026 generation of clinical AI systems.[cite:81][cite:84][cite:86]
