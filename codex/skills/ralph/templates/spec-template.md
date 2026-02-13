# Feature: [Name]

## Purpose

[Brief description of what this feature does and why it exists]

## Function Signatures

```python
def function_name(param: ParamType) -> ReturnType:
    """
    Brief description.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ErrorType: When this error occurs
    """
    pass
```

## Requirements

- [Specific library versions, e.g., "transformers>=4.30.0"]
- [Environment requirements, e.g., "CUDA 11.8+", "GPU with 16GB VRAM"]
- [Any other constraints]

## Implementation Notes

- [Key patterns to follow]
- [Gotchas to avoid]
- [Performance considerations]

## Test Infrastructure

### Smoke Test (Tier 2)
[How to verify the code loads without crashing — e.g., curl a health endpoint, import the module, run --version]

### Integration Test (Tier 3)
[How to verify the feature works end-to-end — e.g., process real data, call the full API pipeline]

### Prerequisites
- [Services that must be running — e.g., "Local Supabase stack", "Redis on localhost:6379"]
- [Test data that must exist — e.g., "Job ID abc123 with 50 segments in local DB"]
- [Secrets/keys that must be configured — e.g., "GEMINI_API_KEY in .env.local"]

## Reference Code

```python
# Working code from tested notebook/implementation
# This is CRITICAL - Ralph uses this to guide generation

# Example:
def working_example():
    """This code has been tested and works."""
    result = actual_implementation()
    return result
```

## Expected Behavior

**Input:**
```python
example_input = {"key": "value"}
```

**Output:**
```python
expected_output = {"result": "expected"}
```

## Test Cases

```python
def test_basic_functionality():
    """Test the basic happy path."""
    result = function_name(valid_input)
    assert result == expected_output

def test_edge_case():
    """Test important edge case."""
    result = function_name(edge_input)
    assert result == edge_expected
```
