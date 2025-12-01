# Copyright 2025 Asher Informatics PBC
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
Enumerations for Clinical AI Governance Framework documents.

Defines process domain codes, content categories, and other governance-specific
classifications used across the CAI framework.

Reference: ASHKBAPP-47 - Refactor CAI Framework to Common Datamodels
"""

from enum import Enum


class ProcessDomainCode(str, Enum):
    """
    Two or three-letter codes for CAI Governance Framework process domains.

    These correspond to the 11 process areas defined in the Ashmatics
    Clinical AI Governance Framework.
    """

    PV = "PV"  # Problem & Value Quantification
    SA = "SA"  # Solution Architecting & Local Validation
    MON = "MON"  # Monitoring & Lifecycle Management
    OVR = "OVR"  # Oversight & Steering
    ORG = "ORG"  # Organization & Strategy Alignment
    IT = "IT"  # IT Systems & Data Management
    RM = "RM"  # Clinical AI Risk Management
    HO = "HO"  # Human Oversight & AI Interaction
    EF = "EF"  # AI Ethics & Fairness Assessment
    TR = "TR"  # AI Transparency & Explainability
    UG = "UG"  # AI Usage Governance & User Compliance
    XX = "XX"  # Unknown/unclassified
    YY = "YY"  # Policy domain (miscellaneous)


class GovernanceCategory(str, Enum):
    """
    Tier 1 content categories for governance artifacts.

    These are the primary categories used to classify CAI framework content.
    """

    CAI_GOVERNANCE = "cai_governance"
    POLICY_DOMAIN = "policy_domain"
    PROCESS_DOMAIN = "process_domain"
    VALIDATION_TOOLS = "validation_tools"
    MASTER_REGISTRY = "master_registry"
    FRAMEWORK_DOCUMENTATION = "framework_documentation"
    DOMAIN_DEFINITIONS = "domain_definitions"


class GovernanceSubcategory(str, Enum):
    """
    Tier 2 detailed subcategories for governance artifacts.

    These provide more specific classification within primary categories.
    """

    # CAI Governance subcategories
    CAI_GOVERNANCE_MASTER_REGISTRY = "cai_governance_master_registry"
    CAI_GOVERNANCE_OVERVIEW = "cai_governance_overview"
    CAI_GOVERNANCE_IMPLEMENTATION_GUIDE = "cai_governance_implementation_guide"
    CAI_GOVERNANCE_ARCHITECTURE = "cai_governance_architecture"

    # Policy domain subcategories
    POLICY_DOMAIN_OVERVIEW_CONTENT = "policy_domain_overview_content"
    POLICY_DOMAIN_TEMPLATE_PRIMITIVES = "policy_domain_template_primitives"
    POLICY_DOMAIN_GLUE_FILES = "policy_domain_glue_files"
    POLICY_DOMAIN_TEMP_POLICIES = "policy_domain_temp_policies"

    # Process domain subcategories
    PROCESS_DOMAIN_BASE_DOCUMENTS = "process_domain_base_documents"
    PROCESS_DOMAIN_SOP = "process_domain_sop"
    PROCESS_DOMAIN_WORK_PRODUCTS = "process_domain_work_products"
    PROCESS_DOMAIN_WIZARD_GUIDES = "process_domain_wizard_guides"
    PROCESS_DOMAIN_TRACEABILITY = "process_domain_traceability"
    PROCESS_DOMAIN_POLICY_BINDINGS = "process_domain_policy_bindings"
    PROCESS_DOMAIN_LOGS = "process_domain_logs"

    # Controls subcategories
    CONTROLS_TOOLS_REGISTRY = "controls_tools_registry"
    CONTROLS_ISO_MAPPINGS = "controls_iso_mappings"
    CONTROLS_FRAMEWORK = "controls_framework"
    CONTROLS_ARCHITECTURE_DESIGN = "controls_architecture_design"


class DomainType(str, Enum):
    """
    Domain type classification for governance artifacts.
    """

    PROCESS = "process"
    POLICY = "policy"
    CONTROLS = "controls"
    GOVERNANCE = "governance"


class ContentFormat(str, Enum):
    """
    Content format (Tier 4) for governance artifacts.

    Indicates the source file format of the content.
    """

    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    PYTHON = "python"
    OTHER = "other"


class GovernanceContentType(str, Enum):
    """
    Content type classifications for governance documents.

    These correspond to the _content_type field in MongoDB.
    """

    COMPILED_MARKDOWN = "compiled_markdown"
    JSON_NATIVE = "json_native"
    YAML_NATIVE = "yaml_native"


class GovernanceArtifactType(str, Enum):
    """
    High-level artifact types for governance documents.
    """

    POLICY = "policy"
    SOP = "sop"
    WORK_PRODUCT = "work_product"
    PROCESS = "process"
    FRAMEWORK = "framework"
    CONTROLS = "controls"
