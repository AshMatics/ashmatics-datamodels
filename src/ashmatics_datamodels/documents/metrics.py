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
Performance metrics shared by regulatory summaries and research papers.

MetricType and PerformanceMetric were defined in documents/regulatory.py
until 0.23.0. IN-13 (research-paper profile, ASHFORGE-866 RP-9) lifts them here
so a metric read from an FDA summary and one read from a paper table are the same
record; regulatory.py re-exports both names, so existing imports keep working
and the classes are the same objects.

0.23.0 adds, optionally: where on the page and in which table cell a metric was
read (source_page, source_cell as a TableCellRef), what kind of source
it was (source_kind), and the printed text.
"""

from enum import Enum
from typing import Optional

from pydantic import Field, model_validator

from ashmatics_datamodels.common.base import AshMaticsBaseModel


class MetricType(str, Enum):
    """
    Type of performance metric (REQ-3.1).

    Standardized metric types for querying and analysis across devices.
    """

    SENSITIVITY = "sensitivity"  # True positive rate
    SPECIFICITY = "specificity"  # True negative rate
    AUC = "auc"  # Area under ROC curve
    DICE = "dice"  # DICE coefficient (segmentation overlap)
    ACCURACY = "accuracy"  # Overall accuracy
    PPV = "ppv"  # Positive predictive value
    NPV = "npv"  # Negative predictive value
    F1_SCORE = "f1_score"  # F1 score (harmonic mean of precision/recall)
    PRECISION = "precision"  # Precision (same as PPV)
    RECALL = "recall"  # Recall (same as sensitivity)
    HAUSDORFF_DISTANCE = "hausdorff_distance"  # Hausdorff distance (segmentation)
    TIME_TO_DETECTION = "time_to_detection"  # Time to detect finding
    TIME_TO_NOTIFICATION = "time_to_notification"  # Time to notify clinician
    DETECTION_RATE = "detection_rate"  # Detection rate (e.g., adenoma, fracture)
    FALSE_POSITIVE_RATE = "false_positive_rate"  # False positive rate
    OTHER = "other"  # Other metric types not in standard list


class MetricSourceKind(str, Enum):
    """What a metric was read from (0.23.0)."""

    TABLE_CELL = "table_cell"  # A cell of a table; source_cell says which
    TEXT = "text"  # Running text of the body
    ABSTRACT = "abstract"  # The abstract (IN-13 decision 6: allowed without full text)


class TableCellRef(AshMaticsBaseModel):
    """A pointer to one cell of one table in the same document (0.23.0).

    row and col are 0-based grid positions of the cell's top-left corner,
    counting header rows, the same positions PaperTableCell records. The
    table id is the document's own (T1 for a paper, table_18 for an FDA
    summary), so no format is imposed here.
    """

    table_id: str = Field(..., min_length=1, description="Table id within the document")
    row: int = Field(
        ..., ge=0, description="0-based row of the cell, header rows included"
    )
    col: int = Field(..., ge=0, description="0-based column of the cell")


class PerformanceMetric(AshMaticsBaseModel):
    """
    Individual performance metric with statistical context and stratification.

    Addresses REQ-3.1 (Performance Metrics Extraction) from Phase 2E design plan.
    Captures quantitative performance metrics with confidence intervals, p-values,
    and stratification dimensions for comparative effectiveness analysis.

    Example:
        >>> metric = PerformanceMetric(
        ...     metric_name="sensitivity",
        ...     metric_type=MetricType.SENSITIVITY,
        ...     value=0.906,
        ...     ci_lower=0.822,
        ...     ci_upper=0.959,
        ...     sample_size=184,
        ...     stratification={"study": "pivotal", "site": "multi_site"},
        ...     source_table="table_18"
        ... )

    Provenance (0.23.0, ASHFORGE-866 RP-9): source_kind, source_page,
    source_cell and source_text say where the number was read, for FDA
    summaries and research papers alike. All four are optional, so every metric
    written before 0.23.0 validates unchanged. A metric read from a paper's
    abstract (IN-13 decision 6) is source_kind="abstract" with no cell.
    """

    metric_name: str = Field(
        ...,
        description="Metric name as appears in document (e.g., 'sensitivity', 'DICE', 'AUC')",
    )
    metric_type: Optional[MetricType] = Field(
        None,
        description="Standardized metric type for querying across devices",
    )
    value: float = Field(
        ...,
        description="Metric value (proportion 0-1 for percentages, raw value otherwise)",
    )
    unit: Optional[str] = Field(
        None,
        description="Unit if applicable (e.g., 'seconds', 'mm', 'minutes')",
    )

    # Statistical measures (REQ-3.3)
    ci_lower: Optional[float] = Field(
        None,
        description="95% confidence interval lower bound",
    )
    ci_upper: Optional[float] = Field(
        None,
        description="95% confidence interval upper bound",
    )
    p_value: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="p-value for statistical testing",
    )
    standard_error: Optional[float] = Field(
        None,
        ge=0.0,
        description="Standard error of metric",
    )
    sample_size: Optional[int] = Field(
        None,
        ge=0,
        description="Sample size (N) for this metric calculation",
    )

    # Stratification (REQ-3.4)
    stratification: Optional[dict[str, str]] = Field(
        None,
        description="Stratification dimensions (e.g., {'gender': 'female', 'age_group': '50-70', 'study': 'pivotal'})",
    )

    # Source attribution (REQ-8.1)
    source_table: Optional[str] = Field(
        None,
        description="Source table ID (e.g., 'table_18')",
    )
    source_section: Optional[str] = Field(
        None,
        description="Source section if extracted from narrative text",
    )

    # Provenance: page and table cell (0.23.0, ASHFORGE-866 RP-9). Additive.
    source_kind: MetricSourceKind | None = Field(
        None,
        description=(
            "What the metric was read from: a table cell, running text, or the "
            "abstract (IN-13 decision 6)"
        ),
    )
    source_page: int | None = Field(
        None,
        ge=1,
        description="1-based page of the source document the metric was read on",
    )
    source_cell: TableCellRef | None = Field(
        None,
        description="The table cell the value was read from (table id, row, column)",
    )
    source_text: str | None = Field(
        None,
        description="The cell or sentence exactly as printed, for a reviewer to check",
    )

    @model_validator(mode="after")
    def _source_reference_is_consistent(self) -> "PerformanceMetric":
        """The new provenance fields must not contradict each other.

        Only the 0.23.0 fields take part, so a pre-0.23.0 metric (which has none
        of them) is never refused here.
        """
        cell = self.source_cell
        kind = self.source_kind
        if kind == MetricSourceKind.TABLE_CELL.value and cell is None:
            raise ValueError("source_kind 'table_cell' needs source_cell")
        if cell is not None:
            if kind is not None and kind != MetricSourceKind.TABLE_CELL.value:
                raise ValueError(
                    f"source_cell is set but source_kind is {kind!r}, not 'table_cell'"
                )
            if self.source_table is not None and self.source_table != cell.table_id:
                raise ValueError(
                    f"source_table {self.source_table!r} disagrees with "
                    f"source_cell.table_id {cell.table_id!r}"
                )
        return self
