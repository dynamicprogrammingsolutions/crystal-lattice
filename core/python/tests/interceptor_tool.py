from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class InterceptorCalculator:
    name: str = "interceptor_calculator"
    version: str = "1.0.0"
    priority: int = 50

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_interception_ui_schema(self, state: Dict[str, Any]) -> Dict[str, Any]:
        add_confirmation: Dict[str, Any] = {
            "ui_type": "tool_interceptor_prompt",
            "title": "Allow adding the numbers?",
            "message": "The model wants to sum two numbers (a={a}, b={b}). Pick an action below.",
            "buttons": [
                {"id": "allow", "label": "Allow", "default": True},
                {"id": "deny", "label": "Deny"},
                {"id": "deny_stop", "label": "Deny and stop"},
                {"id": "transform", "label": "Transform"},
            ],
        }
        web_access: Dict[str, Any] = {
            "ui_type": "tool_interceptor_prompt",
            "title": "Do you want to access this link?",
            "message": "{url}",
            "buttons": [
                {"id": "accept", "label": "Accept", "default": True},
                {"id": "reject", "label": "Reject"},
            ],
        }
        cfg_raw = state.get("config")
        root: Dict[str, Any] = cfg_raw if isinstance(cfg_raw, dict) else {}
        icfg = root.get("interceptor_calculator")
        if isinstance(icfg, dict):
            prompts = icfg.get("tool_call_prompts")
            if isinstance(prompts, dict):
                o = prompts.get("add")
                if isinstance(o, dict):
                    if isinstance(o.get("title"), str) and o["title"]:
                        add_confirmation = {**add_confirmation, "title": o["title"]}
                    if isinstance(o.get("message"), str) and o["message"]:
                        add_confirmation = {**add_confirmation, "message": o["message"]}
        return {"schemas": {"add_confirmation": add_confirmation, "web_access": web_access}}

    def materialize_interception_prompt(
        self,
        state: Dict[str, Any],
        *,
        schema_id: str,
        schema_params: Dict[str, Any],
        tool_call_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        raw = self.get_interception_ui_schema(state)
        schemas = raw.get("schemas") if isinstance(raw, dict) else None
        if not isinstance(schemas, dict):
            return None
        entry = schemas.get(schema_id)
        if not isinstance(entry, dict):
            return None
        params = dict(schema_params or {})

        def fmt(template: str) -> str:
            try:
                m = {str(k): ("" if params[k] is None else params[k]) for k in params}

                class _Keep(dict):
                    __slots__ = ()

                    def __missing__(self, key: str) -> str:
                        return "{" + key + "}"

                return template.format_map(_Keep(m))
            except Exception:
                return template

        title_t = entry.get("title")
        msg_t = entry.get("message")
        title = fmt(str(title_t)) if isinstance(title_t, str) else ""
        message = fmt(str(msg_t)) if isinstance(msg_t, str) else ""

        buttons: List[Dict[str, Any]] = []
        bl = entry.get("buttons")
        if isinstance(bl, list):
            for b in bl:
                if not isinstance(b, dict):
                    continue
                bid = b.get("id")
                if not isinstance(bid, str) or not bid:
                    continue
                nb: Dict[str, Any] = {"id": bid}
                lab = b.get("label")
                if isinstance(lab, str):
                    nb["label"] = lab
                if b.get("default") is True:
                    nb["default"] = True
                for key in ("style", "icon", "order", "metadata"):
                    if key in b:
                        nb[key] = b[key]
                buttons.append(nb)
        if not buttons:
            return None

        pid = entry.get("id")
        if isinstance(pid, str) and pid:
            prompt_id = fmt(pid)
        else:
            suf = tool_call_id if isinstance(tool_call_id, str) and tool_call_id else "tool"
            prompt_id = f"{schema_id}_{suf}"

        out: Dict[str, Any] = {
            "id": prompt_id,
            "title": title,
            "message": message,
            "buttons": buttons,
            "schema_id": schema_id,
        }
        if params:
            out["schema_params"] = params
        ut = entry.get("ui_type")
        if isinstance(ut, str) and ut:
            out["ui_type"] = ut
        sv = entry.get("schema_version")
        if isinstance(sv, (int, str)):
            out["schema_version"] = sv
        ex = entry.get("extras")
        if isinstance(ex, dict):
            out["extras"] = ex
        return out

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        **_: Any,
    ) -> Dict[str, Any]:
        if tool_name != "add":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        return {"success": True, "result": (arguments.get("a") or 0) + (arguments.get("b") or 0)}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"

    def intercept_tool_call(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        tool_name = payload.get("tool_name")
        tool_name_str = str(tool_name) if isinstance(tool_name, str) else ""
        args = payload.get("arguments")
        url = args.get("url") if isinstance(args, dict) else None

        is_web_access = (
            ("web" in tool_name_str and ("fetch" in tool_name_str or "search" in tool_name_str))
            or isinstance(url, str)
        )

        if is_web_access:
            answer = context.get("answer") if isinstance(context.get("answer"), dict) else None
            if answer is None:
                display_url = str(url) if isinstance(url, str) else "External web access requested."
                return {
                    "kind": "prompt",
                    "schema_id": "web_access",
                    "schema_params": {"url": display_url},
                }
            if answer.get("button_id") == "reject":
                return {
                    "kind": "respond",
                    "tool_result": {"success": False, "error": "Rejected web access"},
                    "continue_loop": True,
                }
            return {"kind": "continue"}

        if tool_name != "add":
            return {"kind": "continue"}
        answer = context.get("answer") if isinstance(context.get("answer"), dict) else None
        if answer is None:
            raw_args = payload.get("arguments")
            a_b: Dict[str, Any] = raw_args if isinstance(raw_args, dict) else {}
            return {
                "kind": "prompt",
                "schema_id": "add_confirmation",
                "schema_params": {"a": a_b.get("a", ""), "b": a_b.get("b", "")},
            }
        button_id = answer.get("button_id")
        if button_id == "deny":
            return {
                "kind": "respond",
                "tool_result": {"success": False, "error": "Denied by interceptor"},
                "continue_loop": True,
            }
        if button_id == "deny_stop":
            return {
                "kind": "respond",
                "tool_result": {"success": False, "error": "Denied and stopped"},
                "continue_loop": False,
            }
        if button_id == "transform":
            raw = payload.get("raw_call")
            if isinstance(raw, dict):
                call = dict(raw)
                args_json = json.dumps({"a": 2, "b": 8}, separators=(",", ":"))
                if call.get("type") == "function_call":
                    call["arguments"] = args_json
                else:
                    fn = dict(call.get("function") or {})
                    fn["arguments"] = args_json
                    call["function"] = fn
                return {"kind": "continue", "tool_call": call}
        return {"kind": "continue"}

    def intercept_tool_result(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        result = payload.get("tool_result")
        if not isinstance(result, dict):
            return {"kind": "continue"}
        value = result.get("result")
        if isinstance(value, (int, float)) and value > 8:
            return {
                "kind": "continue",
                "tool_result": {"success": True, "result": 8},
            }
        return {"kind": "continue"}
