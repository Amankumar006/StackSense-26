"""Official enums conforming to Section 3.1 and Section 4 of the problem statement."""

from enum import Enum


class ProjectType(str, Enum):
    CONTENT_SITE = "content_site"
    WEB_APP = "web_app"
    SAAS_B2B = "saas_b2b"
    ECOMMERCE = "ecommerce"
    MARKETPLACE = "marketplace"
    SOCIAL = "social"
    REALTIME_COLLAB = "realtime_collab"
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    DATA_ANALYTICS = "data_analytics"
    IOT = "iot"
    AI_ML_PRODUCT = "ai_ml_product"
    INTERNAL_TOOL = "internal_tool"
    GAMING = "gaming"
    API_PLATFORM = "api_platform"
    OTHER = "other"


class Platform(str, Enum):
    WEB = "web"
    ANDROID = "android"
    IOS = "ios"
    DESKTOP = "desktop"
    API_ONLY = "api_only"


class TrafficPattern(str, Enum):
    STEADY = "steady"
    SPIKY = "spiky"
    SEASONAL = "seasonal"


class WorkloadType(str, Enum):
    READ_HEAVY = "read_heavy"
    BALANCED = "balanced"
    WRITE_HEAVY = "write_heavy"


class TeamExperience(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    MIXED = "mixed"


class CloudPreference(str, Enum):
    ANY = "any"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    NONE = "none"


class DeploymentModel(str, Enum):
    MANAGED_CLOUD = "managed_cloud"
    SELF_HOSTED_CLOUD_VM = "self_hosted_cloud_vm"
    ON_PREMISE = "on_premise"
    AIR_GAPPED = "air_gapped"


class DataResidency(str, Enum):
    NONE = "none"
    INDIA = "india"
    EU = "eu"
    US = "us"
    OTHER = "other"


class AuthRequirement(str, Enum):
    NONE = "none"
    EMAIL_PASSWORD = "email_password"
    SOCIAL = "social"
    PHONE_OTP = "phone_otp"
    ENTERPRISE_SSO = "enterprise_sso"


class MLRequirement(str, Enum):
    NONE = "none"
    INFERENCE_API = "inference_api"
    LLM_RAG = "llm_rag"
    TRAINING = "training"


class ComplianceStandard(str, Enum):
    GDPR = "gdpr"
    DPDP = "dpdp"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    RBI_LOCALISATION = "rbi_localisation"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


class EngineStatus(str, Enum):
    OK = "ok"
    OK_WITH_WARNINGS = "ok_with_warnings"
    INFEASIBLE = "infeasible"
    INVALID_INPUT = "invalid_input"


class ArchitectureStyle(str, Enum):
    STATIC = "static"
    MONOLITH = "monolith"
    MODULAR_MONOLITH = "modular_monolith"
    SERVERLESS = "serverless"
    SERVICE_ORIENTED = "service_oriented"
    MICROSERVICES = "microservices"
    HYBRID = "hybrid"
    OTHER = "other"


class WarningSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SupportingLayer(str, Enum):
    CACHE = "cache"
    QUEUE = "queue"
    SEARCH = "search"
    AUTH = "auth"
    STORAGE = "storage"
    CDN = "cdn"
    REALTIME = "realtime"
    PAYMENTS = "payments"
    ML = "ml"
    CI_CD = "ci_cd"
    OBSERVABILITY = "observability"
    FORMS = "forms"
    OTHER = "other"
