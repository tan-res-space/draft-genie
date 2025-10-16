# DraftGenie Azure Deployment v1 - Architecture

## System Architecture

This document provides a visual overview of the idempotent deployment system architecture.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     deploy-azure_v1.py                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Main Entry Point                           │ │
│  │  - Parse CLI arguments                                        │ │
│  │  - Load configuration                                         │ │
│  │  - Initialize StateManager                                    │ │
│  │  - Create IdempotentDraftGenieDeployer                        │ │
│  │  - Execute deployment                                         │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              IdempotentDraftGenieDeployer                     │ │
│  │                                                               │ │
│  │  Extends: DraftGenieDeployer                                 │ │
│  │                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  @idempotent_step Decorator                             │ │ │
│  │  │  - Check if step completed                              │ │ │
│  │  │  - Compute dependency hash                              │ │ │
│  │  │  - Compare with stored hash                             │ │ │
│  │  │  - Skip if unchanged, execute if changed                │ │ │
│  │  │  - Update state on success/failure                      │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                                                               │ │
│  │  Wrapped Steps (14):                                         │ │
│  │  1. check_prerequisites                                      │ │
│  │  2. create_resource_group                                    │ │
│  │  3. create_monitoring                                        │ │
│  │  4. create_container_registry                                │ │
│  │  5. create_key_vault                                         │ │
│  │  6. create_databases                                         │ │
│  │  7. store_secrets                                            │ │
│  │  8. create_container_apps_env                                │ │
│  │  9. build_and_push_images                                    │ │
│  │  10. deploy_infrastructure_services                          │ │
│  │  11. deploy_application_services                             │ │
│  │  12. configure_environment_variables                         │ │
│  │  13. run_migrations                                          │ │
│  │  14. verify_deployment                                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    StateManager                               │ │
│  │                                                               │ │
│  │  - Load/Save state                                           │ │
│  │  - Track step completion                                     │ │
│  │  - Store dependency hashes                                   │ │
│  │  - Manage resource metadata                                  │ │
│  │                                                               │ │
│  │  Storage Backends:                                           │ │
│  │  ├─ Local File (default)                                     │ │
│  │  └─ Azure Blob Storage (configurable)                        │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## State Management Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      State Management Lifecycle                     │
└─────────────────────────────────────────────────────────────────────┘

1. INITIALIZATION
   ┌──────────────────┐
   │ Load State File  │
   │ (or create new)  │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Parse State JSON │
   └────────┬─────────┘
            │
            ▼

2. STEP EXECUTION
   ┌──────────────────────────────────────────────────────────────┐
   │ For each deployment step:                                    │
   │                                                              │
   │  ┌────────────────────────────────────────────────────────┐ │
   │  │ 1. Compute current dependency hash                     │ │
   │  │    - Hash all file dependencies                        │ │
   │  │    - Hash all config dependencies                      │ │
   │  │    - Combine into single SHA-256 hash                  │ │
   │  └────────────────────────────────────────────────────────┘ │
   │                          │                                   │
   │                          ▼                                   │
   │  ┌────────────────────────────────────────────────────────┐ │
   │  │ 2. Check execution conditions                          │ │
   │  │    - Is --force-all set? → Execute                     │ │
   │  │    - Is --force-step set? → Execute                    │ │
   │  │    - Is step completed? → Check hash                   │ │
   │  │    - Hash changed? → Execute                           │ │
   │  │    - Hash unchanged? → Skip                            │ │
   │  └────────────────────────────────────────────────────────┘ │
   │                          │                                   │
   │                          ▼                                   │
   │  ┌────────────────────────────────────────────────────────┐ │
   │  │ 3. Execute or Skip                                     │ │
   │  │                                                        │ │
   │  │  If Execute:                    If Skip:               │ │
   │  │  ├─ Run step function           └─ Log skip message    │ │
   │  │  ├─ Capture result                                     │ │
   │  │  └─ Update state                                       │ │
   │  └────────────────────────────────────────────────────────┘ │
   │                          │                                   │
   │                          ▼                                   │
   │  ┌────────────────────────────────────────────────────────┐ │
   │  │ 4. Update State                                        │ │
   │  │                                                        │ │
   │  │  If Success:                    If Failure:            │ │
   │  │  ├─ status = "completed"        ├─ status = "failed"   │ │
   │  │  ├─ Store dependency hash       ├─ Store error msg     │ │
   │  │  ├─ Store timestamp             ├─ Store timestamp     │ │
   │  │  └─ Save state file             └─ Save state file     │ │
   │  └────────────────────────────────────────────────────────┘ │
   └──────────────────────────────────────────────────────────────┘

3. COMPLETION
   ┌──────────────────┐
   │ Save Final State │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Generate Summary │
   └──────────────────┘
```

---

## Change Detection System

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Dependency Hash Computation                      │
└─────────────────────────────────────────────────────────────────────┘

Step: create_databases
├─ File Dependencies:
│  ├─ scripts/azure/azure_resources.py
│  │  └─ SHA-256: a1b2c3d4e5f6...
│  └─ (other files...)
│
├─ Config Dependencies:
│  ├─ postgresql.sku = "Standard_B1ms"
│  │  └─ SHA-256: f6g7h8i9j0k1...
│  ├─ postgresql.tier = "Burstable"
│  │  └─ SHA-256: l2m3n4o5p6q7...
│  ├─ redis.sku = "Basic"
│  │  └─ SHA-256: r8s9t0u1v2w3...
│  └─ (other config values...)
│
└─ Combined Hash:
   └─ SHA-256(sorted([file_hashes + config_hashes]))
      └─ Final: x4y5z6a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3

┌─────────────────────────────────────────────────────────────────────┐
│                      Change Detection Logic                         │
└─────────────────────────────────────────────────────────────────────┘

Current Hash:  x4y5z6a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3
Stored Hash:   x4y5z6a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3
                ↓
              MATCH → Skip step (dependencies unchanged)

Current Hash:  y5z6a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4
Stored Hash:   x4y5z6a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3
                ↓
              MISMATCH → Execute step (dependencies changed)
```

---

## State Storage Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    State Storage Backends                           │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐  ┌──────────────────────────────┐
│     Local File Storage           │  │   Azure Blob Storage         │
│         (Default)                │  │      (Configurable)          │
├──────────────────────────────────┤  ├──────────────────────────────┤
│                                  │  │                              │
│  File: .azure-deployment-        │  │  Account: <storage-account>  │
│        state-v1.json             │  │  Container: deployment-state │
│                                  │  │  Blob: azure-deployment-     │
│  Location: Project root          │  │        state.json            │
│                                  │  │                              │
│  Pros:                           │  │  Pros:                       │
│  ✓ Simple setup                  │  │  ✓ Centralized               │
│  ✓ Fast access                   │  │  ✓ Team accessible           │
│  ✓ Works offline                 │  │  ✓ Durable                   │
│  ✓ No cost                       │  │  ✓ Audit trail               │
│                                  │  │                              │
│  Cons:                           │  │  Cons:                       │
│  ✗ Not shared                    │  │  ✗ Requires storage account  │
│  ✗ Can be lost                   │  │  ✗ Network dependency        │
│                                  │  │  ✗ Additional cost           │
│                                  │  │                              │
│  Use Case:                       │  │  Use Case:                   │
│  • Local development             │  │  • Team environments         │
│  • Single-user deployments       │  │  • CI/CD pipelines           │
│  • Quick iterations              │  │  • Production deployments    │
└──────────────────────────────────┘  └──────────────────────────────┘
                │                                    │
                └────────────┬───────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  StateManager  │
                    │                │
                    │  Unified API   │
                    └────────────────┘
```

---

## Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Deployment Execution Flow                        │
└─────────────────────────────────────────────────────────────────────┘

START
  │
  ├─ Parse CLI Arguments
  │   ├─ --config
  │   ├─ --force-step
  │   ├─ --force-all
  │   ├─ --reset-state
  │   └─ (other options)
  │
  ├─ Load Configuration
  │   └─ config.yaml
  │
  ├─ Initialize StateManager
  │   ├─ Determine storage backend
  │   └─ Load existing state (if any)
  │
  ├─ Handle --reset-state
  │   └─ If set: Clear state and exit
  │
  ├─ Create IdempotentDraftGenieDeployer
  │   ├─ Pass StateManager
  │   ├─ Pass force_steps dict
  │   └─ Pass force_all flag
  │
  ├─ Execute deploy()
  │   │
  │   ├─ Step 1: check_prerequisites
  │   │   └─ @idempotent_step wrapper
  │   │       ├─ Check state
  │   │       ├─ Compute hash
  │   │       ├─ Execute or skip
  │   │       └─ Update state
  │   │
  │   ├─ Step 2: create_resource_group
  │   │   └─ @idempotent_step wrapper
  │   │       └─ (same logic)
  │   │
  │   ├─ Step 3-13: (other steps)
  │   │   └─ @idempotent_step wrapper
  │   │       └─ (same logic)
  │   │
  │   └─ Step 14: verify_deployment
  │       └─ @idempotent_step wrapper
  │           └─ (same logic)
  │
  ├─ Generate Deployment Summary
  │
  └─ EXIT
      ├─ Exit Code 0: Success
      ├─ Exit Code 1: Failure
      └─ Exit Code 130: User interrupt
```

---

## Class Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Class Hierarchy                             │
└─────────────────────────────────────────────────────────────────────┘

DraftGenieDeployer (from deployer.py)
  │
  │  Original deployment orchestrator
  │  - 14 deployment step methods
  │  - Basic state management
  │  - Azure resource creation
  │
  └─── IdempotentDraftGenieDeployer (from deploy-azure_v1.py)
        │
        │  Extended with idempotency
        │  - Wraps all 14 steps with @idempotent_step
        │  - Adds StateManager integration
        │  - Adds force execution support
        │  - Overrides _save_deployment_state()
        │
        └─── Methods:
              ├─ __init__(config, logger, dry_run, state_manager, force_steps, force_all)
              ├─ _save_deployment_state() [overridden]
              ├─ @idempotent_step _step_check_prerequisites()
              ├─ @idempotent_step _step_create_resource_group()
              ├─ @idempotent_step _step_create_monitoring()
              ├─ @idempotent_step _step_create_container_registry()
              ├─ @idempotent_step _step_create_key_vault()
              ├─ @idempotent_step _step_create_databases()
              ├─ @idempotent_step _step_store_secrets()
              ├─ @idempotent_step _step_create_container_apps_env()
              ├─ @idempotent_step _step_build_and_push_images()
              ├─ @idempotent_step _step_deploy_infrastructure_services()
              ├─ @idempotent_step _step_deploy_application_services()
              ├─ @idempotent_step _step_configure_environment_variables()
              ├─ @idempotent_step _step_run_migrations()
              └─ @idempotent_step _step_verify_deployment()

StateManager (from deploy-azure_v1.py)
  │
  │  State persistence and management
  │  - Load/save state
  │  - Track step completion
  │  - Store dependency hashes
  │  - Manage resource metadata
  │
  └─── Methods:
        ├─ __init__(config, logger)
        ├─ _determine_storage_type()
        ├─ _load_state()
        ├─ _load_state_from_file()
        ├─ _load_state_from_blob() [TODO]
        ├─ _save_state_to_file()
        ├─ _save_state_to_blob() [TODO]
        ├─ _create_empty_state()
        ├─ save()
        ├─ reset()
        ├─ is_step_completed(step_name)
        ├─ mark_step_completed(step_name, hash, metadata)
        ├─ mark_step_failed(step_name, error)
        ├─ get_step_hash(step_name)
        ├─ store_resource(type, data)
        └─ get_resource(type)
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Flow                                  │
└─────────────────────────────────────────────────────────────────────┘

config.yaml
    │
    ├─→ Configuration Values
    │       │
    │       ├─→ Deployment Settings
    │       ├─→ Resource Names
    │       ├─→ SKUs and Sizes
    │       └─→ Secrets
    │
    └─→ Dependency Hash Computation
            │
            └─→ Combined with File Hashes
                    │
                    └─→ Stored in State File

Dockerfiles, Python Modules
    │
    └─→ File Hash Computation
            │
            └─→ Combined with Config Hashes
                    │
                    └─→ Stored in State File

State File (.azure-deployment-state-v1.json)
    │
    ├─→ Step Status (completed/failed)
    ├─→ Dependency Hashes
    ├─→ Timestamps
    ├─→ Error Messages
    └─→ Resource Metadata
            │
            └─→ Used for Idempotency Decisions
```

---

**Architecture Version:** 1.0  
**Last Updated:** January 15, 2024  
**Status:** Current

