# Zero-Trust Configuration & Environment Architecture

## 1. Architectural Role of `config.py` in Enterprise AI

In production healthcare and telephony architectures (AI-102/103), the configuration layer is not simply a key-value dictionary. It acts as the **first line of security, validation, and zero-trust policy enforcement**.

```
              ┌────────────────────────────────────────────────────────┐
              │                     Source of Truth                    │
              │  Local: .env file  │  Production: Azure App Service    │
              └─────────────────────────┬──────────────────────────────┘
                                        │
                                        ▼
             ┌──────────────────────────────────────────────────────────┐
             │       src/core/config.py (Pydantic BaseSettings)         │
             │  - Strict Type Coercion (int, bool, str, Optional)       │
             │  - Case-Insensitive Mapping (AZURE_SPEECH_KEY -> attr)   │
             │  - Default Fallbacks & Fail-Fast Validation              │
             └──────────────────────────┬───────────────────────────────┘
                                        │
             ┌──────────────────────────┴───────────────────────────────┐
             ▼                                                          ▼
[Local Dev Mode: USE_MANAGED_IDENTITY=False]      [Production Mode: USE_MANAGED_IDENTITY=True]
 Downstream modules use raw API Keys               Downstream modules instantiate:
 from .env for rapid offline testing.               DefaultAzureCredential() via Entra ID /
                                                    Managed Identity (Zero persistent secrets).
```

---

## 2. Pydantic Settings Mechanics vs. `os.environ`

Using raw `os.environ.get("...")` or `os.getenv("...")` introduces severe architectural vulnerabilities:
1. **Silent Failures:** If `APP_PORT` is missing, `os.environ.get("APP_PORT")` returns `None` or requires repetitive inline defaults. If it returns a string `"8000"`, passing it to a server expecting an `int` crashes at runtime.
2. **Scattered Reads:** Calling `os.environ` inside arbitrary functions makes dependencies invisible and impossible to mock during unit tests.
3. **Pydantic V2 Performance:** `pydantic-settings` validates environment variables once during process bootstrap using high-performance Rust core (`pydantic-core`). It produces a immutable, strongly-typed singleton (`settings`).

---

## 3. Failure Modes & Edge Cases

| Failure Mode | Raw `os.environ` Behavior | Pydantic `Settings` Behavior |
| :--- | :--- | :--- |
| **Missing Port / Int Mismatch** | Raises `TypeError` down in socket code | Coerces `"8000"` to integer `8000` or fails during startup |
| **Boolean Formatting** | `"False"` evaluated as truthy string in Python (`bool("False") == True`) | Correctly evaluates `"false"`, `"0"`, `"off"`, `"no"` to `False` |
| **Credential Leakage** | Plaintext keys passed indiscriminately | Masked or bypassed via `use_managed_identity` flag |
| **Cross-Platform Case Sensitivity** | Linux is case-sensitive; Windows is not | `case_sensitive=False` normalizes all platforms |
