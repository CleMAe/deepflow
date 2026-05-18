"""
DeepFlow — Inter-module Protocol definitions.

Frozen at Day 1 10:00. All cross-module dependencies must reference
these Protocol interfaces, never concrete implementations.

This enables parallel development: each module uses a mock implementation
during dev, and swaps to the real one at integration time.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    runtime_checkable,
)


# ─── Enums ──────────────────────────────────────────────────────

class DatasetFormat(str, enum.Enum):
    CSV = "csv"
    JSON = "json"
    IMAGE = "image"
    OTHER = "other"


class DatasetStatus(str, enum.Enum):
    UPLOADING = "uploading"
    READY = "ready"
    CLEANING = "cleaning"
    CLEANED = "cleaned"
    ERROR = "error"


class TrainingStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ToolType(str, enum.Enum):
    MODEL_INFERENCE = "model_inference"
    API_CALL = "api_call"
    CUSTOM = "custom"


class WSMessageType(str, enum.Enum):
    METRICS = "metrics"
    LOG = "log"
    ALERT = "alert"
    STATUS_CHANGE = "status_change"
    PROGRESS = "progress"


class ChatRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class SSEEventType(str, enum.Enum):
    TOKEN = "token"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DONE = "done"
    ERROR = "error"


# ─── Data Transfer Objects ──────────────────────────────────────

@dataclass
class ColumnMeta:
    name: str
    dtype: str
    nullable: bool = True
    unique_count: int = 0
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class DatasetPreview:
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int


@dataclass
class CleaningResult:
    rows_before: int
    rows_after: int
    columns_affected: List[str]
    changes_summary: Dict[str, Any]
    dataset_id: str


@dataclass
class ColumnStat:
    name: str
    dtype: str
    missing_count: int = 0
    missing_pct: float = 0.0
    unique_count: int = 0
    numeric_stats: Optional[Dict[str, float]] = None
    top_values: Optional[List[Dict[str, Any]]] = None


@dataclass
class EDAReport:
    dataset_id: str
    num_rows: int
    num_columns: int
    num_missing: int
    duplicate_rows: int
    column_stats: List[ColumnStat]
    correlations: Optional[Dict[str, Dict[str, float]]] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None


@dataclass
class AugmentResult:
    original_count: int
    augmented_count: int
    new_dataset_id: str
    output_dataset_name: str


@dataclass
class SplitResult:
    train_dataset_id: str
    val_dataset_id: Optional[str]
    test_dataset_id: Optional[str]
    train_count: int
    val_count: int
    test_count: int


@dataclass
class ValidationResult:
    valid: bool
    errors: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class Checkpoint:
    epoch: int
    step: int
    path: str
    is_best: bool = False
    metrics: Dict[str, float] = field(default_factory=dict)
    file_size: int = 0
    created_at: Optional[str] = None


@dataclass
class TrainingMetrics:
    epoch: int
    step: int
    train_loss: float
    val_loss: Optional[float] = None
    accuracy: Optional[float] = None
    learning_rate: float = 0.001
    gpu_util: Optional[float] = None
    gpu_memory: Optional[float] = None
    cpu_util: Optional[float] = None
    memory_util: Optional[float] = None
    throughput: Optional[str] = None
    eta: Optional[str] = None


@dataclass
class WSMessage:
    type: WSMessageType
    data: Dict[str, Any]


@dataclass
class ChatMessage:
    id: str
    conversation_id: str
    role: ChatRole
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None


@dataclass
class SSEEvent:
    type: SSEEventType
    content: Optional[str] = None
    name: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    message_id: Optional[str] = None


@dataclass
class AgentToolConfig:
    tool_id: str
    name: str
    type: ToolType
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    bound_at: Optional[str] = None


@dataclass
class OnlineInferenceResult:
    prediction: Any
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    latency_ms: Optional[float] = None


# ─── Protocols ──────────────────────────────────────────────────

@runtime_checkable
class StorageProtocol(Protocol):
    """File system storage abstraction.

    P6 implements (RealFileStorage), P7/P8 consume.
    """

    def get_project_path(self, project_id: str) -> str:
        """Return root path for a project."""
        ...

    def get_dataset_path(self, project_id: str, dataset_id: str) -> str:
        """Return path for a dataset directory."""
        ...

    def get_raw_path(self, project_id: str, dataset_id: str) -> str:
        """Return path for raw uploaded files."""
        ...

    def get_cleaned_path(self, project_id: str, dataset_id: str) -> str:
        """Return path for cleaned data."""
        ...

    def get_model_path(self, project_id: str, model_id: str) -> str:
        """Return path for model directory."""
        ...

    def get_checkpoint_path(self, project_id: str, model_id: str) -> str:
        """Return path for model checkpoints."""
        ...

    def get_exported_path(self, project_id: str, model_id: str) -> str:
        """Return path for exported models (ONNX etc.)."""
        ...

    def get_experiment_path(self, project_id: str, experiment_id: str) -> str:
        """Return path for experiment logs."""
        ...

    def ensure_dir(self, path: str) -> str:
        """Create directory if not exists, return path."""
        ...

    def get_upload_temp_path(self) -> str:
        """Return path for temporary upload chunks."""
        ...

    def get_storage_usage(self, project_id: str) -> int:
        """Return total storage used in bytes for a project."""
        ...


@runtime_checkable
class DataParserProtocol(Protocol):
    """Data parsing and format detection.

    P7 implements, cleaning engine consumes.
    """

    def detect_format(self, file_path: str) -> DatasetFormat:
        """Detect dataset format from file content."""
        ...

    def parse(self, file_path: str, format: DatasetFormat) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Parse file into (columns, rows)."""
        ...

    def get_columns_meta(self, file_path: str, format: DatasetFormat) -> List[ColumnMeta]:
        """Extract column metadata (types, nullability, samples)."""
        ...

    def count_rows(self, file_path: str, format: DatasetFormat) -> int:
        """Count total rows without full load."""
        ...

    def validate_file(self, file_path: str, format: DatasetFormat) -> ValidationResult:
        """Validate file integrity and format correctness."""
        ...


@runtime_checkable
class CleaningProtocol(Protocol):
    """Data cleaning operations.

    P7 implements, API layer consumes.
    """

    def handle_missing(
        self,
        dataset_id: str,
        strategy: str,
        columns: Optional[List[str]] = None,
        fill_value: Optional[Any] = None,
        create_new_version: bool = True,
    ) -> CleaningResult:
        ...

    def detect_outliers(
        self,
        dataset_id: str,
        columns: List[str],
        method: str,
        threshold: Optional[float] = None,
        action: str = "drop",
    ) -> CleaningResult:
        ...

    def deduplicate(
        self,
        dataset_id: str,
        columns: Optional[List[str]] = None,
        keep: str = "first",
    ) -> CleaningResult:
        ...

    def encode(
        self,
        dataset_id: str,
        columns: List[str],
        method: str,
    ) -> CleaningResult:
        ...

    def type_convert(
        self,
        dataset_id: str,
        conversions: List[Dict[str, Any]],
    ) -> CleaningResult:
        ...


@runtime_checkable
class EDAServiceProtocol(Protocol):
    """Exploratory data analysis service.

    P7 implements, API layer consumes.
    """

    def run_eda(
        self,
        dataset_id: str,
        columns: Optional[List[str]] = None,
        include_visualizations: bool = True,
    ) -> EDAReport:
        ...

    def get_report(self, dataset_id: str) -> Optional[EDAReport]:
        ...


@runtime_checkable
class AugmentationProtocol(Protocol):
    """CV data augmentation service.

    P7 implements, API layer consumes.
    """

    def augment(
        self,
        dataset_id: str,
        transforms: List[Dict[str, Any]],
        num_augmented: int = 1,
        output_name: Optional[str] = None,
    ) -> AugmentResult:
        ...

    def preview_transform(
        self,
        image_path: str,
        transforms: List[Dict[str, Any]],
    ) -> str:
        """Return path to a preview image with transforms applied."""
        ...


@runtime_checkable
class DatasetSplitProtocol(Protocol):
    """Dataset splitting service.

    P7 implements, API layer consumes.
    """

    def split(
        self,
        dataset_id: str,
        train_ratio: float,
        val_ratio: Optional[float] = None,
        test_ratio: Optional[float] = None,
        stratify_column: Optional[str] = None,
        random_seed: int = 42,
    ) -> SplitResult:
        ...


@runtime_checkable
class ModelRegistryProtocol(Protocol):
    """Pre-built model library registry.

    P8 implements, P1 (Agent) and API layer consume.
    """

    def list_models(
        self,
        task_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        ...

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        ...

    def get_default_hyperparams(self, arch_type: str) -> Dict[str, Any]:
        ...

    def validate_config(self, arch_type: str, params_cfg: Dict[str, Any]) -> ValidationResult:
        ...


@runtime_checkable
class TrainingEngineProtocol(Protocol):
    """Training engine interface.

    P8 implements, API layer consumes.
    The engine runs as a subprocess, isolated from the API process.
    """

    def start_training(self, job_id: str) -> None:
        """Launch training as subprocess."""
        ...

    def pause_training(self, job_id: str) -> None:
        ...

    def resume_training(self, job_id: str) -> None:
        ...

    def stop_training(self, job_id: str) -> None:
        ...

    def get_status(self, job_id: str) -> TrainingStatus:
        ...

    def get_checkpoints(self, job_id: str) -> List[Checkpoint]:
        ...

    def get_logs(self, job_id: str, tail: int = 200) -> List[str]:
        ...

    def subscribe(self, job_id: str) -> AsyncIterator[WSMessage]:
        """Subscribe to training events (WebSocket feed source)."""
        ...


@runtime_checkable
class InferenceEngineProtocol(Protocol):
    """Inference engine interface.

    P7/P8 implements, P1 (Agent tool wrapper) and API layer consume.
    """

    def evaluate(
        self,
        model_id: str,
        dataset_id: str,
        checkpoint_path: Optional[str] = None,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        ...

    def batch_inference(
        self,
        model_id: str,
        dataset_id: str,
        checkpoint_path: Optional[str] = None,
    ) -> str:
        """Start batch inference, return task_id."""
        ...

    def get_inference_result(self, task_id: str) -> Dict[str, Any]:
        ...

    def online_inference(
        self,
        model_id: str,
        input_data: Any,
        checkpoint_path: Optional[str] = None,
    ) -> OnlineInferenceResult:
        ...

    def export_onnx(
        self,
        model_id: str,
        checkpoint_path: Optional[str] = None,
        opset_version: int = 17,
        dynamic_batch: bool = True,
    ) -> str:
        """Start ONNX export, return output path."""
        ...


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """LLM provider interface (OpenAI-compatible via LiteLLM).

    P1 implements, Agent chat engine consumes.
    MockLLM returns preset replies when real LLM API is unavailable.
    """

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[SSEEvent]:
        """Stream chat completion via SSE events."""
        ...

    def get_available_models(self) -> List[str]:
        ...


@runtime_checkable
class ToolWrapperProtocol(Protocol):
    """FastAPI tool wrapping interface.

    P1 implements. Wraps trained models as callable tool endpoints
    that agents can invoke during conversations.
    """

    def wrap_model(self, model_id: str, model_name: str, config: Dict[str, Any]) -> str:
        """Wrap a trained model as a FastAPI endpoint. Return endpoint URL."""
        ...

    def unwrap_model(self, model_id: str) -> None:
        """Remove a model's tool endpoint."""
        ...

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke a bound tool with given arguments."""
        ...

    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Return OpenAI function-calling-compatible schema for a tool."""
        ...

    def list_active_tools(self) -> List[Dict[str, Any]]:
        ...


@runtime_checkable
class AuthProtocol(Protocol):
    """Authentication service.

    P6 implements, all modules consume.
    """

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT, return user payload or None."""
        ...

    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get full user info from token."""
        ...

    def create_token(self, user_id: str, username: str, role: str) -> Tuple[str, str]:
        """Create (access_token, refresh_token) pair."""
        ...

    def refresh_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh token pair. Return None if invalid."""
        ...
