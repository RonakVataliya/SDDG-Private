import asyncio

import pytest
from fastapi import HTTPException

from app.diagram_generation import generate_plantuml
from app.schemas.diagrams import DiagramGenerationRequest, DiagramItem


ITEMS = [
    DiagramItem(id="A-001", category="actor", name="Customer", source_refs=["R-001"]),
    DiagramItem(id="E-001", category="entity", name="Order", source_refs=["R-001"]),
    DiagramItem(id="P-001", category="process", name="Place Order", source_refs=["R-001"]),
    DiagramItem(id="P-002", category="process", name="Confirm Order", source_refs=["R-002"]),
    DiagramItem(id="DS-001", category="data_store", name="Orders", source_refs=["R-001"]),
    DiagramItem(id="DF-001", category="data_flow", name="Order details", source_id="A-001", target_id="P-001"),
    DiagramItem(id="I-001", category="interaction", name="Place order", source_id="A-001", target_id="P-001"),
    DiagramItem(id="REL-001", category="relationship", name="stores", source_id="P-001", target_id="E-001", relation_type="dependency"),
]


@pytest.mark.parametrize("diagram_type", ["dfd", "class", "sequence", "activity", "component", "state"])
def test_each_sprint_two_diagram_has_plantuml(diagram_type):
    source = generate_plantuml(
        DiagramGenerationRequest(diagram_type=diagram_type, system_name="Shop", items=ITEMS)
    )

    assert source.startswith("@startuml")
    assert source.endswith("@enduml")


def test_sequence_requires_interactions():
    request = DiagramGenerationRequest(
        diagram_type="sequence",
        system_name="Shop",
        items=[item for item in ITEMS if item.category != "interaction"],
    )

    with pytest.raises(ValueError, match="no interactions"):
        generate_plantuml(request)


def test_diagram_endpoint_reports_incomplete_models():
    import app.routers.diagrams as diagrams_router

    with pytest.raises(HTTPException, match="no interactions") as error:
        asyncio.run(diagrams_router.generate(DiagramGenerationRequest(
            diagram_type="sequence", system_name="Shop", items=[]
        )))
    assert error.value.status_code == 422
