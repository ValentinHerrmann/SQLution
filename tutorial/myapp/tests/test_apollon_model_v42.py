"""
Regression tests for diagrams produced by the current Apollon editor
(model wire format 4.2.0).

The model below is what the editor stores for a small schema: class nodes
carry width/height/measured, edges carry handles and `data.points`. Diagrams
uploaded in the older Apollon v3 format are migrated by the editor and end up
with additional edge data fields (label, isManuallyLayouted, messages, empty
roles); those must not change the generated SQL either.
"""
import copy

from myapp.utils.json_to_sql import (
    ModelAnalyzer,
    SQLGenerator,
    convert_jsonmodel_to_sqlddl,
)


def _class_node(node_id, name, attributes, x, y):
    height = 40 + 30 * len(attributes)
    return {
        "id": node_id,
        "width": 160,
        "height": height,
        "type": "class",
        "position": {"x": x, "y": y},
        "data": {
            "name": name,
            "methods": [],
            "attributes": [
                {"id": f"{node_id}-attr-{i}", "name": attr}
                for i, attr in enumerate(attributes)
            ],
        },
        "measured": {"width": 160, "height": height},
    }


def editor_model_v42():
    return {
        "id": "vom4exm89zn",
        "version": "4.2.0",
        "title": "",
        "type": "ClassDiagram",
        "nodes": [
            _class_node("8f0c7c1e-1d2b", "Kunde", ["auto id", "String name"], 530, 175),
            _class_node("2b9e4a77-55aa", "Bestellung", ["auto id", "date datum"], 935, 175),
            _class_node("c41f0d3b-9e10", "Produkt", ["auto id", "float preis"], 935, 395),
        ],
        "edges": [
            {
                "id": "e5a1b2c3-0001",
                "source": "2b9e4a77-55aa",
                "target": "8f0c7c1e-1d2b",
                "type": "ClassUnidirectional",
                "sourceHandle": "left",
                "targetHandle": "right",
                "data": {
                    "sourceMultiplicity": "n",
                    "targetMultiplicity": "1",
                    "targetRole": "kunde_id",
                    "points": [{"x": 934, "y": 225}, {"x": 691, "y": 225}],
                },
            },
            {
                "id": "e5a1b2c3-0002",
                "source": "2b9e4a77-55aa",
                "target": "c41f0d3b-9e10",
                "type": "ClassBidirectional",
                "sourceHandle": "bottom",
                "targetHandle": "top",
                "data": {
                    "sourceMultiplicity": "n",
                    "targetMultiplicity": "m",
                    "sourceRole": "enthaelt",
                    "points": [],
                },
            },
        ],
        "assessments": {},
    }


class TestApollonModelV42:
    def test_tables_foreign_keys_and_junction_table(self):
        sql = convert_jsonmodel_to_sqlddl(editor_model_v42())

        assert 'CREATE TABLE "Kunde"' in sql
        assert 'CREATE TABLE "Bestellung"' in sql
        assert 'CREATE TABLE "Produkt"' in sql
        # n:m relationship becomes a junction table named after the role
        assert 'CREATE TABLE "enthaelt"' in sql
        assert 'REFERENCES "Kunde"("id")' in sql
        assert 'REFERENCES "Produkt"("id")' in sql
        assert 'REFERENCES "Bestellung"("id")' in sql
        assert '"kunde_id" INTEGER' in sql
        assert '"preis" REAL' in sql

    def test_referenced_tables_are_created_first(self):
        sql = convert_jsonmodel_to_sqlddl(editor_model_v42())

        assert sql.index('CREATE TABLE "Kunde"') < sql.index('CREATE TABLE "Bestellung"')
        assert sql.index('CREATE TABLE "Bestellung"') < sql.index('CREATE TABLE "enthaelt"')
        assert sql.index('CREATE TABLE "Produkt"') < sql.index('CREATE TABLE "enthaelt"')

    def test_editor_ids_are_renamed_to_readable_ids(self):
        analyzer = ModelAnalyzer(editor_model_v42())

        assert set(analyzer.class_elements) >= {"clz-kunde", "clz-bestellung", "clz-produkt"}

    def test_v3_migrated_edge_data_gives_same_sql(self):
        migrated = editor_model_v42()
        for edge in migrated["edges"]:
            edge["data"].update(
                {"label": "", "isManuallyLayouted": False, "messages": []}
            )
            edge["data"].setdefault("sourceRole", "")
            edge["data"].setdefault("targetRole", "")

        expected = SQLGenerator(ModelAnalyzer(editor_model_v42())).generate()
        assert SQLGenerator(ModelAnalyzer(copy.deepcopy(migrated))).generate() == expected
