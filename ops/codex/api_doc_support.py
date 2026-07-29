from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(order=True)
class EndpointDoc:
    sort_key: tuple[str, str] = field(init=False, repr=False)
    method: str
    path: str
    handler: str
    response_model: str | None
    summary: str
    tags: list[str]
    query_params: list[str]
    path_params: list[str]
    body_params: list[str]

    def __post_init__(self) -> None:
        self.sort_key = (self.path, self.method)

    @property
    def signature(self) -> str:
        return f"{self.method} {self.path}"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_import_path(root: Path) -> None:
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _clean_annotation(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "__name__"):
        return value.__name__
    text = str(value)
    return text.replace("typing.", "")


def _string_constant(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_include_prefixes(main_path: Path) -> dict[str, str]:
    tree = ast.parse(main_path.read_text(encoding="utf-8"), filename=str(main_path))
    alias_to_module: dict[str, str] = {}
    prefix_by_module: dict[str, str] = {}

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.api.routes."):
            for imported in node.names:
                if imported.name == "router":
                    alias_to_module[imported.asname or imported.name] = node.module

    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute):
            continue
        if not (isinstance(call.func.value, ast.Name) and call.func.value.id == "app" and call.func.attr == "include_router"):
            continue
        if not call.args or not isinstance(call.args[0], ast.Name):
            continue
        alias = call.args[0].id
        module_name = alias_to_module.get(alias)
        if not module_name:
            continue
        prefix = ""
        for keyword in call.keywords:
            if keyword.arg == "prefix":
                prefix = _string_constant(keyword.value) or ""
        prefix_by_module[module_name] = prefix

    return prefix_by_module


def _extract_router_tags(tree: ast.Module) -> list[str]:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "router" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or node.value.func.id != "APIRouter":
            continue
        for keyword in node.value.keywords:
            if keyword.arg != "tags" or not isinstance(keyword.value, ast.List):
                continue
            tags = [_string_constant(item) for item in keyword.value.elts]
            return [tag for tag in tags if tag]
    return []


def _classify_param(default_node: ast.AST | None, name: str, route_path: str) -> str | None:
    if f"{{{name}}}" in route_path:
        return "path"
    if isinstance(default_node, ast.Call):
        func = default_node.func
        func_name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if func_name == "Query":
            return "query"
        if func_name == "Path":
            return "path"
        if func_name == "Depends":
            return None
    return "body" if default_node is not None else None


def _response_model_text(call: ast.Call) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == "response_model":
            try:
                return ast.unparse(keyword.value)
            except Exception:
                return None
    return None


def _load_router_file(module_name: str, file_path: Path, prefix: str) -> list[EndpointDoc]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    tags = _extract_router_tags(tree)
    endpoints: list[EndpointDoc] = []

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if not (isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "router"):
                continue
            method = decorator.func.attr.upper()
            route_path = _string_constant(decorator.args[0]) if decorator.args else None
            if not route_path:
                continue

            defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + list(node.args.defaults)
            query_params: list[str] = []
            path_params: list[str] = []
            body_params: list[str] = []
            for arg, default_node in zip(node.args.args, defaults):
                if arg.arg == "self":
                    continue
                bucket = _classify_param(default_node, arg.arg, route_path)
                if bucket == "query":
                    query_params.append(arg.arg)
                elif bucket == "path":
                    path_params.append(arg.arg)
                elif bucket == "body":
                    body_params.append(arg.arg)

            doc = ast.get_docstring(node) or ""
            summary = doc.splitlines()[0].strip() if doc else ""
            endpoints.append(
                EndpointDoc(
                    method=method,
                    path=f"{prefix}{route_path}",
                    handler=f"{module_name}.{node.name}",
                    response_model=_response_model_text(decorator),
                    summary=summary,
                    tags=tags,
                    query_params=query_params,
                    path_params=path_params,
                    body_params=[name for name in body_params if name != "db"],
                )
            )

    return endpoints


def _load_app_routes(main_path: Path) -> list[EndpointDoc]:
    tree = ast.parse(main_path.read_text(encoding="utf-8"), filename=str(main_path))
    endpoints: list[EndpointDoc] = []
    allowed_methods = {"get", "post", "put", "delete", "patch", "options", "head"}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if not (isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "app"):
                continue
            if decorator.func.attr not in allowed_methods:
                continue
            route_path = _string_constant(decorator.args[0]) if decorator.args else None
            if not route_path:
                continue
            endpoints.append(
                EndpointDoc(
                    method=decorator.func.attr.upper(),
                    path=route_path,
                    handler=f"app.main.{node.name}",
                    response_model=None,
                    summary=(ast.get_docstring(node) or "").splitlines()[0].strip() if ast.get_docstring(node) else "",
                    tags=[],
                    query_params=[],
                    path_params=[],
                    body_params=[],
                )
            )
    return endpoints


def load_fastapi_endpoints(root: Path | None = None) -> list[EndpointDoc]:
    root = root or project_root()
    main_path = root / "app" / "main.py"
    if not main_path.exists():
        return []

    prefix_by_module = _extract_include_prefixes(main_path)
    endpoints: list[EndpointDoc] = _load_app_routes(main_path)
    routes_dir = root / "app" / "api" / "routes"
    for route_file in sorted(routes_dir.glob("*.py")):
        if route_file.name == "__init__.py":
            continue
        module_name = f"app.api.routes.{route_file.stem}"
        prefix = prefix_by_module.get(module_name, "")
        endpoints.extend(_load_router_file(module_name, route_file, prefix))

    return sorted(endpoints)


def render_endpoint_markdown(endpoints: list[EndpointDoc]) -> str:
    lines = [
        "# API Endpoints",
        "",
        "Tai lieu nay duoc sinh tu code route FastAPI trong repo nay.",
        "Nguon su that la code; khi route doi, hay sinh lai file nay.",
        "",
        "| Method | Path | Handler | Response | Tags |",
        "| --- | --- | --- | --- | --- |",
    ]
    for endpoint in endpoints:
        tags = ", ".join(endpoint.tags) if endpoint.tags else "-"
        response_model = endpoint.response_model or "-"
        lines.append(
            f"| {endpoint.method} | `{endpoint.path}` | `{endpoint.handler}` | `{response_model}` | {tags} |"
        )

    lines.extend(["", "## Endpoint Details", ""])
    for endpoint in endpoints:
        lines.append(f"### `{endpoint.method} {endpoint.path}`")
        lines.append("")
        lines.append(f"- Handler: `{endpoint.handler}`")
        lines.append(f"- Response: `{endpoint.response_model or '-'}`")
        lines.append(f"- Tags: {', '.join(endpoint.tags) if endpoint.tags else '-'}")
        lines.append(f"- Query params: {', '.join(endpoint.query_params) if endpoint.query_params else '-'}")
        lines.append(f"- Path params: {', '.join(endpoint.path_params) if endpoint.path_params else '-'}")
        lines.append(f"- Body params: {', '.join(endpoint.body_params) if endpoint.body_params else '-'}")
        if endpoint.summary:
            lines.append(f"- Summary: {endpoint.summary}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
