from __future__ import annotations
import copy, re, uuid
from typing import Any
from components import COMPONENTS, default_properties, effective_ports

PROXY_TYPES = {
    "ContainerEventInput": ("work_in", "doInput"),
    "ContainerDataInput": ("data_in", "Value"),
    "ContainerEventOutput": ("event_out", "onResult"),
    "ContainerDataOutput": ("data_out", "Result"),
}

def build_interface(
    subgraph: dict[str, Any],
    previous: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build proxy interface without discarding the user's passport fields."""
    result=[]; used=set()
    old_by_proxy = {
        str(item.get("proxy_id")): item
        for item in (previous or [])
        if isinstance(item, dict)
    }
    for node in subgraph.get("nodes",[]):
        kind_default=PROXY_TYPES.get(str(node.get("type")))
        if not kind_default: continue
        kind,fallback=kind_default; pid=str(node.get("id")); props=node.get("properties",{})
        caption=str(props.get("name",fallback)); old=old_by_proxy.get(pid,{})
        preferred=str(old.get("port") or "")
        base=preferred or re.sub(r"\W+","_",caption).strip("_") or fallback
        port=base; number=2
        while port in used: port=f"{base}_{number}"; number+=1
        used.add(port)
        data_type=(
            str(old.get("data_type") or props.get("data_type") or "any")
            if kind in {"data_in","data_out"} else "any"
        )
        result.append({
            "port":port,
            "caption":caption,
            "kind":kind,
            "proxy_id":pid,
            "data_type":data_type,
            "data_type_source":str(
                old.get("data_type_source")
                or props.get("data_type_source")
                or ""
            ),
            "description":str(old.get("description") or ""),
        })
    return result

def pack_project(project: dict[str, Any], selected_ids: set[str]) -> tuple[dict[str, Any], str]:
    project=copy.deepcopy(project); by_id={str(n.get("id")):n for n in project.get("nodes",[])}
    selected=[by_id[i] for i in selected_ids if i in by_id]
    if not selected: raise ValueError("Не выбраны ноды для контейнера")
    min_x=min(float(n.get("x",0)) for n in selected); min_y=min(float(n.get("y",0)) for n in selected)
    # Helpers are drawing objects, not nodes.  Keep the ones covering the
    # selected area inside the new container instead of silently dropping
    # them.  The margin lets a frame surround the selected nodes even when
    # its top-left corner is slightly outside their bounding box.
    max_x=max(
        float(n.get("x", 0))
        + float(n.get("properties", {}).get("width", 120) or 120)
        for n in selected
    )
    max_y=max(
        float(n.get("y", 0))
        + float(n.get("properties", {}).get("height", 62) or 62)
        for n in selected
    )
    helper_margin = 70.0
    inner_helpers=[]; outer_helpers=[]
    for helper in project.get("helpers", []):
        if not isinstance(helper, dict):
            continue
        hx=float(helper.get("x", 0) or 0)
        hy=float(helper.get("y", 0) or 0)
        hw=float(helper.get("width", 220) or 220)
        hh=float(helper.get("height", 70) or 70)
        intersects = (
            hx < max_x + helper_margin
            and hx + hw > min_x - helper_margin
            and hy < max_y + helper_margin
            and hy + hh > min_y - helper_margin
        )
        target=inner_helpers if intersects else outer_helpers
        item=copy.deepcopy(helper)
        if intersects:
            item["x"]=round(hx-min_x+90, 1)
            item["y"]=round(hy-min_y+70, 1)
        target.append(item)
    inner_nodes=copy.deepcopy(selected)
    for n in inner_nodes: n["x"]=float(n.get("x",0))-min_x+90; n["y"]=float(n.get("y",0))-min_y+70
    inner_links=[]; outer_links=[]; proxies=[]; boundary=[]
    for link in project.get("connections",[]):
        a=link.get("from_node") in selected_ids; b=link.get("to_node") in selected_ids
        if a and b: inner_links.append(copy.deepcopy(link)); continue
        if not a and not b: outer_links.append(copy.deepcopy(link)); continue
        proxy_id="port_"+uuid.uuid4().hex[:8]
        if b:
            target=by_id[str(link.get("to_node"))]; port=next((p for p in effective_ports(target["type"],target.get("properties",{})) if p.name==link.get("to_port")),None)
            ptype="ContainerEventInput" if port and port.kind=="work_in" else "ContainerDataInput"; pport="onEvent" if ptype=="ContainerEventInput" else "Data"; caption=str(link.get("to_port")); data_type=str(port.data_type if port else "any")
            inner_links.append({"from_node":proxy_id,"from_port":pport,"to_node":link["to_node"],"to_port":link["to_port"]}); side="to"
        else:
            source=by_id[str(link.get("from_node"))]; port=next((p for p in effective_ports(source["type"],source.get("properties",{})) if p.name==link.get("from_port")),None)
            ptype="ContainerEventOutput" if port and port.kind=="event_out" else "ContainerDataOutput"; pport="doEvent" if ptype=="ContainerEventOutput" else "Data"; caption=str(link.get("from_port")); data_type=str(port.data_type if port else "any")
            inner_links.append({"from_node":link["from_node"],"from_port":link["from_port"],"to_node":proxy_id,"to_port":pport}); side="from"
        proxies.append({"id":proxy_id,"type":ptype,"x":0 if side=="to" else 560,"y":70+len(proxies)*70,"properties":{"name":caption,"data_type":data_type,"data_type_source":f"{source.get('type') if side=='from' else target.get('type')}.{link.get('from_port') if side=='from' else link.get('to_port')}"},"enabled_ports":[pport]})
        boundary.append((copy.deepcopy(link),proxy_id,side))
    subgraph={
        "format":1,
        "name":"Внутренняя схема",
        "nodes":inner_nodes+proxies,
        "connections":inner_links,
        "helpers":inner_helpers,
    }
    interface=build_interface(subgraph); port_by_proxy={i["proxy_id"]:i["port"] for i in interface}; cid=uuid.uuid4().hex[:10]
    for link,pid,side in boundary:
        if side=="to": link["to_node"]=cid; link["to_port"]=port_by_proxy[pid]
        else: link["from_node"]=cid; link["from_port"]=port_by_proxy[pid]
        outer_links.append(link)
    container={"id":cid,"type":"UserContainer","x":min_x,"y":min_y,"properties":{"name":f"Блок ({len(selected)} нод)","subgraph":subgraph,"interface":interface},"enabled_ports":[i["port"] for i in interface]}
    project["nodes"]=[n for n in project.get("nodes",[]) if n.get("id") not in selected_ids]+[container]
    project["connections"]=outer_links
    project["helpers"]=outer_helpers
    return project,cid
