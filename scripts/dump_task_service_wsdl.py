#!/usr/bin/env python3
"""
One-off diagnostic: TaskService WSDL (Create / Read / Update / Delete) + Update trials.

Run from repo root with credentials in .env:

    pip install -e ".[dev]"
    python scripts/dump_task_service_wsdl.py

Optional live SOAP tests (Step 2 & XML post):

    python scripts/dump_task_service_wsdl.py --task-key "key://2/$Plan/17606"

    python scripts/dump_task_service_wsdl.py --task-key "key://2/$Plan/17606" --post-envelope

Paste the full terminal output when debugging Update / empty-dtos issues.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Allow `python scripts/...` without editable install
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lxml import etree  # noqa: E402

from planview_portfolios_mcp.config import settings  # noqa: E402
from planview_portfolios_mcp.oauth import get_oauth_token  # noqa: E402
from planview_portfolios_mcp.soap_client import get_soap_client  # noqa: E402

TASK_SERVICE_NAME = "TaskService"
TASK_SERVICE_PORT = "BasicHttpBinding_ITaskService3"
TASK_DTO2_QNAME = (
    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2"
)


def _binding_op_keys(binding: Any) -> list[Any]:
    all_ops = binding.all()
    if isinstance(all_ops, dict):
        return list(all_ops.keys())
    return list(all_ops)


def _find_op_key(binding: Any, local_name: str) -> Any | None:
    for key in _binding_op_keys(binding):
        tail = key.split("}")[-1] if isinstance(key, str) and "}" in key else str(key)
        if tail == local_name:
            return key
    return None


def _dump_operation(binding: Any, local_name: str) -> None:
    print(f"\n=== {local_name} ===")
    key = _find_op_key(binding, local_name)
    if key is None:
        print("  NOT FOUND (no matching operation key on this binding)")
        print(f"  Available keys: {_binding_op_keys(binding)}")
        return

    op = binding.get(key)
    print(f"  Zeep operation key: {key!r}")
    print(f"  soapAction: {getattr(op, 'soapaction', None)!r}")
    try:
        print(f"  str(): {op}")
    except Exception as e:
        print(f"  str() failed: {e}")

    if not op.input or not op.input.body:
        print("  (no input body)")
        return

    body = op.input.body
    typ = getattr(body, "type", None)
    print(f"  Input body element: {body!r}")
    print(f"  Input body type: {typ}")
    print(f"  Input body type name: {getattr(typ, 'name', None)!r}")

    elements = getattr(typ, "elements", None) if typ is not None else None
    if elements:
        for elem_name, elem in elements:
            ename = getattr(elem, "attr_name", None) or elem_name
            etyp = getattr(elem, "type", None)
            print(f"  Element: {ename!r} (raw {elem_name!r})")
            print(f"    Type: {etyp}")
            print(f"    Type name: {getattr(etyp, 'name', None)!r}")
            print(f"    Is optional: {getattr(elem, 'is_optional', 'n/a')}")
            print(
                "    Min/Max occurs: "
                f"{getattr(elem, 'min_occurs', 'n/a')}/{getattr(elem, 'max_occurs', 'n/a')}"
            )

    parts = getattr(body, "parts", None)
    if isinstance(parts, Mapping):
        for part_name, part in parts.items():
            print(f"  Part: {part_name} -> {part}")


def _serialize_envelope(client: Any, service: Any, op_local: str, args: tuple, kwargs: dict) -> bytes:
    key = _find_op_key(service._binding, op_local)
    if key is None:
        raise SystemExit(f"No operation {op_local!r} on binding")
    envelope, _headers = service._binding._create(key, args, kwargs, client=client)
    return etree.tostring(envelope, pretty_print=True)


async def _step2_and_xml(
    client: Any,
    service: Any,
    task_key: str | None,
    post_envelope: bool,
) -> None:
    if not task_key:
        print("\n=== Step 2 / XML: skipped (pass --task-key to run live Update + envelope) ===")
        return

    task_payload = {"Key": task_key, "Description": "dump_task_service_wsdl.py probe"}

    update_fn = getattr(service, "Update")

    print("\n=== Step 2: Live Update() variants (sync zeep calls) ===")
    trials: list[tuple[str, tuple, dict]] = [
        ("kwargs dtos= list, options not passed", (), {"dtos": [task_payload]}),
        ("kwargs dtos=, options={}", (), {"dtos": [task_payload], "options": {}}),
        ("kwargs dtos=, options=None", (), {"dtos": [task_payload], "options": None}),
        ("positional ([payload], {})", ([task_payload], {}), {}),
        ("positional ([payload],) one-arg", ([task_payload],), {}),
    ]
    for label, args, kw in trials:
        try:
            result = update_fn(*args, **kw)
            print(f"  OK {label}: {type(result).__name__} {result!r}"[:500])
        except Exception as e:
            print(f"  FAIL {label}: {type(e).__name__}: {e}")

    print("\n=== Serialized envelopes (zeep create_message) ===")
    for op_name in ("Create", "Update"):
        try:
            # Create needs FatherKey + Description; only serialize shape for comparison
            if op_name == "Create":
                sample = {
                    **task_payload,
                    "FatherKey": "key://2/$Plan/3817",
                    "Description": "serialize sample",
                }
                del sample["Key"]
                blob = _serialize_envelope(client, service, op_name, (), {"dtos": [sample]})
            else:
                blob = _serialize_envelope(client, service, op_name, (), {"dtos": [task_payload]})
            print(f"\n--- {op_name} envelope (first 4000 bytes) ---\n{blob[:4000].decode('utf-8', errors='replace')}")
        except Exception as e:
            print(f"  {op_name} serialize failed: {type(e).__name__}: {e}")

    if not post_envelope:
        print("\n=== Step 3 POST: skipped (pass --post-envelope to POST serialized Update XML) ===")
        return

    print("\n=== Step 3: POST serialized Update envelope via httpx ===")
    key = _find_op_key(service._binding, "Update")
    envelope, http_headers = service._binding._create(
        key, (), {"dtos": [task_payload]}, client=client
    )
    xml_bytes = etree.tostring(envelope, xml_declaration=True, encoding="utf-8")
    addr = service._binding_options.get("address")
    if not addr:
        print("  No service address on binding_options; cannot POST")
        return
    token = await get_oauth_token()
    import httpx

    hdrs = {
        "Content-Type": "text/xml; charset=utf-8",
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": settings.planview_tenant_id,
    }
    if isinstance(http_headers, dict):
        hdrs.update({k: v for k, v in http_headers.items() if k and v is not None})
    async with httpx.AsyncClient(timeout=settings.soap_timeout) as http:
        r = await http.post(addr, content=xml_bytes, headers=hdrs)
        print(f"  POST {addr}")
        print(f"  Status: {r.status_code}")
        print(f"  Body (first 2000 chars): {r.text[:2000]}")


async def _amain(task_key: str | None, post_envelope: bool) -> None:
    print("planview_api_url:", settings.planview_api_url)
    print("soap_service_path:", settings.soap_service_path)
    print("tenant_id set:", bool(settings.planview_tenant_id))
    print("oauth client id set:", bool(settings.planview_client_id))

    async with get_soap_client() as client:
        try:
            service = client.bind(TASK_SERVICE_NAME, port_name=TASK_SERVICE_PORT)
        except (AttributeError, ValueError, KeyError, TypeError):
            service = client.service

        binding = service._binding
        print("\n=== All binding operation keys ===")
        print(_binding_op_keys(binding))

        for op_name in ("Create", "Read", "Update", "Delete"):
            _dump_operation(binding, op_name)

        print("\n=== Service endpoint ===")
        print(service._binding_options)

        factory = client.get_type(TASK_DTO2_QNAME)
        print(f"\n=== TaskDto2 factory ===\n  {factory}")

        await _step2_and_xml(client, service, task_key, post_envelope)


def main() -> None:
    p = argparse.ArgumentParser(description="Dump TaskService WSDL metadata via zeep")
    p.add_argument("--task-key", help="Real task key URI for Step 2 / Step 3 trials")
    p.add_argument(
        "--post-envelope",
        action="store_true",
        help="POST zeep-serialized Update envelope with httpx (needs --task-key)",
    )
    args = p.parse_args()
    asyncio.run(_amain(args.task_key, args.post_envelope))


if __name__ == "__main__":
    main()
