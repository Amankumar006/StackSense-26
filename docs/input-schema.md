# StackSense Input Specification

**Version:** 1.0.0 (Official Reconciled Contract)  
**Authority:** Synergy '26 StackSense Challenge Problem Statement (Section 3.1)

---

## 1. Overview & Processing Rules

The engine ingests structured project parameters in JSON format.
- **Mandatory fields** must be provided; their absence in an input file produces validation errors (`status: "invalid_input"`).
- **Optional fields** must be handled when absent by assigning a documented default value recorded in the output `assumptions[]` array.
- **Enums** are lower-case strings exactly as specified below.
- Extra parameters are allowed and contribute to Input Design & Research score when their architectural impact is justified, but the engine must operate correctly on files containing only the standard fields.

---

## 2. Mandatory Input Schema Dictionary

### 2.1 `project` (Project Metadata)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `project.name` | `string` | No | Free text (default: `"Unnamed Project"`) | Project identifier for presentation. |
| `project.type` | `enum` | **Yes** | `content_site`, `web_app`, `saas_b2b`, `ecommerce`, `marketplace`, `social`, `realtime_collab`, `fintech`, `healthtech`, `data_analytics`, `iot`, `ai_ml_product`, `internal_tool`, `gaming`, `api_platform`, `other` | Drives architectural archetype, stateful vs stateless design, and supporting layer defaults. |
| `project.description` | `string` | No | Free text | Free-text context. May be optionally parsed by LLM into structured fields when LLM is enabled. |
| `project.platforms` | `list[enum]` | **Yes** (non-empty) | `web`, `android`, `ios`, `desktop`, `api_only` | Directly constrains frontend technologies (e.g., cross-platform mobile like React Native/Flutter vs. web frameworks like Next.js/Astro). |

### 2.2 `scale` (Traffic & Data Scale)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `scale.users_at_launch` | `integer ≥ 0` | **Yes** | Non-negative integer | Initial scale baseline. |
| `scale.users_12_months` | `integer ≥ 0` | **Yes** | Non-negative integer | Projected 1-year growth; dictates autoscaling vs. single-node setup. |
| `scale.peak_concurrent_users`| `integer ≥ 0` | No | Non-negative integer (default: derived from launch users) | Peak concurrency; triggers connection pooling, cache layers, or distributed queues. |
| `scale.traffic_pattern` | `enum` | No | `steady`, `spiky`, `seasonal` (default: `steady`) | Serverless / container autoscaling versus fixed VM capacity. |
| `scale.workload` | `enum` | No | `read_heavy`, `balanced`, `write_heavy` (default: `balanced`) | Read replicas, CDN/edge caching, and database write optimization. |
| `scale.data_volume_gb_12_months` | `number ≥ 0` | No | Non-negative number (default: `10`) | Total storage footprint; affects database sizing and object storage requirements. |

### 2.3 `team` (Engineering Skills & Operations)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `team.size` | `integer ≥ 1` | **Yes** | Positive integer | Operational complexity budget. Tiny teams ($1-3$) penalize microservices or self-hosted Kubernetes. |
| `team.experience` | `enum` | **Yes** | `beginner`, `intermediate`, `senior`, `mixed` | Technology adoption friction; beginners favor batteries-included frameworks (Django, Rails, Supabase, Firebase). |
| `team.languages` | `list[string]` | **Yes** (may be empty) | Lower-case names, e.g. `python`, `typescript`, `javascript`, `java`, `csharp`, `php`, `go`, `kotlin`, `sql` | Language match bonus in candidate scoring; minimizes onboarding friction. |
| `team.has_devops` | `boolean` | No | `true`, `false` (default: `false`) | When `false`, strongly favors managed cloud PaaS/serverless over self-managed VMs or clusters. |

### 2.4 `budget` (Cost Boundaries)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `budget.monthly_infra_usd` | `number ≥ 0` | **Yes** | Number $\ge 0$ | Soft constraint ceiling. Stacks exceeding budget receive scoring penalties or trigger `ok_with_warnings` relaxation. \$0 budget enforces free-tier-only components. |

### 2.5 `timeline` (Delivery Velocity)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `timeline.mvp_weeks` | `integer ≥ 1` | **Yes** | Positive integer | Soft constraint. Short timelines ($<8$ weeks) heavily weight delivery speed, BaaS, and monoliths over decoupled services. |

### 2.6 `infrastructure` (Deployment & Residency Invariants)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `infrastructure.cloud_preference` | `enum` | No | `any`, `aws`, `gcp`, `azure`, `none` (default: `any`) | **Hard constraint** when explicit (`aws`, `gcp`, `azure`). Hosting and managed services must belong to the chosen provider. |
| `infrastructure.deployment_model` | `enum` | No | `managed_cloud`, `self_hosted_cloud_vm`, `on_premise`, `air_gapped` (default: `managed_cloud`) | **Hard constraint**. `on_premise` and `air_gapped` strictly exclude SaaS/PaaS and external CDN dependencies. |
| `infrastructure.data_residency` | `enum` | No | `none`, `india`, `eu`, `us`, `other` (default: `none`) | **Hard constraint**. Selected cloud regions and database providers must offer in-region physical data storage. |
| `infrastructure.existing_systems` | `list[string]` | No | List of strings (default: `[]`) | Legacy systems that the recommended stack must integrate with (e.g. Entra ID, on-prem SQL Server). |

### 2.7 `requirements` (Functional & Architecture Triggers)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `requirements.realtime` | `boolean` | No | `true`, `false` (default: `false`) | Triggers WebSocket / SSE supporting layer or managed real-time service (Supabase realtime, Pusher, Redis Pub/Sub). |
| `requirements.offline_support` | `boolean` | No | `true`, `false` (default: `false`) | Enforces local client storage (SQLite, WatermelonDB, Realm) with conflict-resolution sync architecture. |
| `requirements.full_text_search` | `boolean` | No | `true`, `false` (default: `false`) | Evaluates PostgreSQL tsvector vs dedicated search engine (Meilisearch, Elasticsearch, Algolia). |
| `requirements.file_media_storage`| `boolean` | No | `true`, `false` (default: `false`) | Triggers object storage layer (S3, Cloudflare R2, Google Cloud Storage). |
| `requirements.payments` | `boolean` | No | `true`, `false` (default: `false`) | Triggers payments gateway integration layer (Razorpay, Stripe, UPI). |
| `requirements.auth` | `enum` | No | `none`, `email_password`, `social`, `phone_otp`, `enterprise_sso` (default: `none`) | Constrains auth service selection (Firebase Auth, Supabase Auth, Keycloak, Auth0, Entra ID). |
| `requirements.multi_tenant` | `boolean` | No | `true`, `false` (default: `false`) | Influences database schema strategy (schema-per-tenant, row-level security). |
| `requirements.ml_features` | `enum` | No | `none`, `inference_api`, `llm_rag`, `training` (default: `none`) | Triggers ML supporting services, vector search indexing, or dedicated GPU/model endpoints. |
| `requirements.seo_critical` | `boolean` | No | `true`, `false` (default: `false`) | Mandates SSR / SSG frontend rendering (Astro, Next.js); eliminates pure client-rendered SPAs. |
| `requirements.availability` | `enum` | No | `"99"`, `"99.9"`, `"99.95"`, `"99.99"` (default: `"99.9"`) | High availability triggers multi-AZ managed instances, automated failover, and redundancy. |
| `requirements.p95_latency_ms` | `integer > 0` or `null` | No | Integer $> 0$ or `null` (default: `null`) | Sub-100ms latency triggers in-memory caching (Redis) and edge CDN deployment. |

### 2.8 `compliance` (Regulatory Invariants)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `compliance` | `list[enum]` | No | Items: `gdpr`, `dpdp`, `hipaa`, `pci_dss`, `rbi_localisation`, `soc2`, `iso27001` (default: `[]`) | **Hard constraint**. Enforces compliance certifications, tokenization, audit logging, and data localization. |

### 2.9 `priorities` (Optimization Weights)
| Field Path | Type | Required | Allowed Values / Default | Meaning / Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| `priorities.cost` | `integer 1-5` | No | `1` to `5` (default: `3`) | Multiplier for monthly cost efficiency in scoring. |
| `priorities.time_to_market` | `integer 1-5` | No | `1` to `5` (default: `3`) | Multiplier for rapid prototyping and developer ergonomics. |
| `priorities.scalability` | `integer 1-5` | No | `1` to `5` (default: `3`) | Multiplier for horizontal scaling and throughput capacity. |
| `priorities.performance` | `integer 1-5` | No | `1` to `5` (default: `3`) | Multiplier for low response latency and resource efficiency. |
| `priorities.maintainability`| `integer 1-5` | No | `1` to `5` (default: `3`) | Multiplier for clean architecture, typing, and long-term tech debt. |
| `priorities.security` | `integer 1-5` | No | `1` to `5` (default: `3`) | Multiplier for hardened defaults, isolation, and access control. |
