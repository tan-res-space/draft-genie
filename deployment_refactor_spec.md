# Technical Specification: Azure Deployment Refactor for Resource Locations

This document outlines the design for refactoring the Azure deployment scripts to support resource-specific locations.

## 1. Configuration Changes (`scripts/azure/config.yaml`)

### 1.1. Problem

The current configuration uses a single, global `location` field under the `azure` key. This is inflexible and causes deployment failures when a selected region does not support all resource types (e.g., PostgreSQL Flexible Servers in 'southindia').

### 1.2. Proposed Solution

I will introduce a new top-level `locations` block. This block will contain a `default` location and an optional `resources` map to specify locations for individual resource types. The existing `azure.location` will be deprecated and eventually removed.

### 1.3. "Before" and "After" Examples

**Before (`config.yaml`):**

```yaml
azure:
  subscription_id: d102000b-c949-411d-ac5d-9ee7154eb524
  resource_group: draftgenie-rg
  location: southindia
  project_name: draftgenie-backend
# ... other resources
postgresql:
  server_name: dg-backend-postgres
  # ... other postgresql settings
```

**After (`config.yaml`):**

```yaml
azure:
  subscription_id: d102000b-c949-411d-ac5d-9ee7154eb524
  resource_group: draftgenie-rg
  project_name: draftgenie-backend
  # The 'location' field is deprecated and will be ignored if 'locations' is present.

locations:
  default: southindia
  resources:
    postgresql: westus3 # A region that supports PostgreSQL Flexible Servers

# ... other resources
postgresql:
  server_name: dg-backend-postgres
  # ... other postgresql settings
```

This new structure is more scalable and allows for fine-grained control over resource placement.

## 2. Python Script Logic Changes

### 2.1. `scripts/azure/azure_resources.py`

The `AzureResourceManager` class will be updated to handle the new location configuration.

#### 2.1.1. `__init__` method:

The constructor will be modified to:
1.  Read the new `locations` block from the configuration.
2.  Store the default location and the resource-specific locations.
3.  Issue a warning if the deprecated `azure.location` is used alongside the new `locations` block.

#### 2.1.2. New `_get_location_for_resource` method:

A new private method will be added to resolve the location for a given resource type.

```python
def _get_location_for_resource(self, resource_type: str) -> str:
    """
    Get the location for a specific resource type.
    Falls back to the default location if no specific location is defined.
    """
    return self.config.get('locations', {}).get('resources', {}).get(resource_type, self.config.get('locations', {}).get('default'))
```

#### 2.1.3. Resource Creation Methods:

Each `create_*` method (e.g., `create_postgresql_server`, `create_container_registry`) will be updated to call `_get_location_for_resource` to determine the correct location for the resource being created.

**Example (`create_postgresql_server`):**

```python
# ... inside create_postgresql_server method
location = self._get_location_for_resource('postgresql')

cmd = [
    'postgres', 'flexible-server', 'create',
    # ... other arguments
    '--location', location,
    # ... other arguments
]
# ...
```

### 2.2. `scripts/deploy-azure.py`

The `validate_config` function will be updated to validate the new `locations` structure.

#### 2.2.1. `validate_config` function:

This function will be modified to:
1.  Check for the presence of the `locations.default` field.
2.  If `locations.default` is missing, the validation should fail.
3.  If both `azure.location` and `locations` are present, a warning should be logged, and `locations` should be preferred.