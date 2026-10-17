"""Generate each Sprint 2 diagram directly from the confirmed shared model."""
import re

from app.schemas.diagrams import DiagramGenerationRequest, DiagramItem


def _alias(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]", "_", value)


def _quote(value: str) -> str:
    return value.replace('"', "'")


def _items(request: DiagramGenerationRequest, category: str) -> list[DiagramItem]:
    return [item for item in request.items if item.category == category]


def _require(items: list[DiagramItem], diagram_type: str, noun: str) -> None:
    if not items:
        raise ValueError(f"Cannot generate a {diagram_type} diagram: no {noun} were confirmed.")


def _relationships(items: list[DiagramItem], names: dict[str, str]) -> list[str]:
    arrows = {
        "association": "--",
        "aggregation": "o--",
        "composition": "*--",
        "inheritance": "<|--",
        "dependency": "..>",
        "realization": "..|>",
    }
    lines = []
    for item in items:
        if item.source_id in names and item.target_id in names:
            lines.append(f"{_alias(item.source_id)} {arrows.get(item.relation_type, '--')} {_alias(item.target_id)}")
    return lines


def generate_plantuml(request: DiagramGenerationRequest) -> str:
    actors = _items(request, "actor")
    entities = _items(request, "entity")
    processes = _items(request, "process")
    stores = _items(request, "data_store")
    flows = _items(request, "data_flow")
    interactions = _items(request, "interaction")
    relationships = _items(request, "relationship")
    lines = ["@startuml", f'title {_quote(request.system_name)} · {request.diagram_type.replace("_", " ").title()}']

    if request.diagram_type == "dfd":
        _require(processes, "Data Flow", "processes")
        _require(flows, "Data Flow", "data flows")
        for item in actors:
            lines.append(f'actor "{_quote(item.name)}" as {_alias(item.id)}')
        for item in processes:
            lines.append(f'rectangle "{_quote(item.name)}" as {_alias(item.id)}')
        for item in stores:
            lines.append(f'database "{_quote(item.name)}" as {_alias(item.id)}')
        names = {item.id: item.name for item in actors + processes + stores}
        for flow in flows:
            if flow.source_id in names and flow.target_id in names:
                lines.append(f'{_alias(flow.source_id)} --> {_alias(flow.target_id)} : {_quote(flow.name)}')
    elif request.diagram_type == "class":
        _require(entities, "Class", "entities")
        for item in entities:
            lines.append(f'class "{_quote(item.name)}" as {_alias(item.id)}')
        lines.extend(_relationships(relationships, {item.id: item.name for item in entities}))
    elif request.diagram_type == "sequence":
        _require(interactions, "Sequence", "interactions")
        participants = {item.id: item for item in actors + entities + processes}
        for item in participants.values():
            lines.append(f'participant "{_quote(item.name)}" as {_alias(item.id)}')
        for interaction in interactions:
            if interaction.source_id in participants and interaction.target_id in participants:
                lines.append(f'{_alias(interaction.source_id)} -> {_alias(interaction.target_id)} : {_quote(interaction.name)}')
    elif request.diagram_type == "activity":
        _require(processes, "Activity", "processes")
        lines.append("start")
        for process in processes:
            lines.append(f':{_quote(process.name)};')
        lines.append("stop")
    elif request.diagram_type == "component":
        components = processes + entities
        _require(components, "Component", "processes or entities")
        for item in components:
            lines.append(f'component "{_quote(item.name)}" as {_alias(item.id)}')
        lines.extend(_relationships(relationships, {item.id: item.name for item in components}))
    else:  # state
        _require(processes, "State", "processes")
        for process in processes:
            lines.append(f'state "{_quote(process.name)}" as {_alias(process.id)}')
        lines.append(f'[*] --> {_alias(processes[0].id)}')
        for current, following in zip(processes, processes[1:]):
            lines.append(f'{_alias(current.id)} --> {_alias(following.id)}')
        lines.append(f'{_alias(processes[-1].id)} --> [*]')

    lines.append("@enduml")
    return "\n".join(lines)
