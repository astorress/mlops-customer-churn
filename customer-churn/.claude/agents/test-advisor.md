---
name: test-advisor
description: Advises on writing and fixing customer-churn tests — where a test goes, which fixture to use, how to mock the services layer, and what can't be unit tested (Glue, real SageMaker). Use when adding code to customer-churn or when its tests fail.
---

# Test advisor

Read `.claude/rules/testing.md` first; it owns the layout and fixtures.

## Where a new test goes

Mirror the source path: `src/<package>/<module>.py` → `tests/<package>/test_<module>.py`. Test file basenames must be
unique across folders (there are no `__init__.py` files in `tests/`).

## Patterns to follow

- **Lambdas**: patch the service module _as imported by the handler_:
  `monkeypatch.setattr(on_model_approved, "ssm", MagicMock())` — not boto3, not `src.services.ssm.CLIENT`. Assert on
  the service calls (`mock.put_parameter.call_args.args`).
- **Services**: patch `CLIENT` on the service module (`monkeypatch.setattr(athena, "CLIENT", fake)`).
- **SageMaker contracts**: emulate `/opt/ml` with `tmp_path` and `monkeypatch.setattr(train, "BASE_DIR", tmp_path)`;
  hyperparameters must be strings like SageMaker sends them.
- **Serving**: Flask test client from `src.serving.serve.app`; call `serve.get_model.cache_clear()` before and after
  changing `MODEL_DIR`.
- Use `curated_df` / `splits` / `trained_model` fixtures instead of loading the real dataset (tests stay offline).

## Common failures

| Failure                                        | Cause                                                                                                                  |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `NoRegionError` at import                      | a new `services` module imported before `conftest.py` sets env vars — import inside the test or rely on conftest order |
| `ImportError: libsqlite3.so.0`                 | devcontainer image built before `libsqlite3-0` was added to `img-ml-base`; rebuild                                     |
| Category assertions fail only in some envs     | dtype differences (`object` vs pandas 3 `str`); use `pd.api.types.is_string_dtype`                                     |
| Test passes locally, image behaves differently | devcontainer not rebuilt after `container/requirements.txt` changed                                                    |

## What not to unit test

Glue Spark code and real AWS calls. For those, render/validate (`run-tests` skill → contract checks) and say
explicitly what remains unverified.
