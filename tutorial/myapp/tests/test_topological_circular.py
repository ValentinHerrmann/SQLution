"""
Test for topological sorting with circular dependencies.
"""
import pytest
from myapp.utils import json_to_sql as j2s_mod


class TestTopologicalCircular:
    """Test topological sorting handles circular dependencies and all tables."""

    def test_circular_dependency_all_tables_included(self):
        """Test that all tables are included even with circular dependencies."""
        data = {
            "id": "test-circular",
            "version": "4.0.0",
            "nodes": [
                {
                    "id": "clz-nutzer",
                    "type": "class",
                    "data": {
                        "name": "Nutzer",
                        "attributes": [
                            {"id": "att-nutzer-id", "name": "auto NutzerID"}
                        ],
                        "methods": []
                    }
                },
                {
                    "id": "clz-produkt",
                    "type": "class",
                    "data": {
                        "name": "Produkt",
                        "attributes": [
                            {"id": "att-produkt-id", "name": "auto ProduktID"}
                        ],
                        "methods": []
                    }
                },
                {
                    "id": "clz-anbieter",
                    "type": "class",
                    "data": {
                        "name": "Anbieter",
                        "methods": [],
                        "attributes": [
                            {"id": "att-anbieter-id", "name": "auto AnbieterID"}
                        ]
                    }
                },
                {
                    "id": "clz-werbung",
                    "type": "class",
                    "data": {
                        "name": "Werbung",
                        "methods": [],
                        "attributes": [
                            {"id": "att-werbung-id", "name": "auto WerbeID"}
                        ]
                    }
                },
                {
                    "id": "clz-lieferung",
                    "type": "class",
                    "data": {
                        "name": "Lieferung",
                        "methods": [],
                        "attributes": [
                            {"id": "att-lieferung-id", "name": "auto LieferID"}
                        ]
                    }
                }
            ],
            "edges": [
                {
                    "id": "rel-1",
                    "source": "clz-anbieter",
                    "target": "clz-produkt",
                    "type": "ClassUnidirectional",
                    "data": {
                        "sourceRole": "Bietet_an",
                        "targetRole": "",
                        "sourceMultiplicity": "n",
                        "targetMultiplicity": "1"
                    }
                },
                {
                    "id": "rel-2",
                    "source": "clz-produkt",
                    "target": "clz-lieferung",
                    "type": "ClassUnidirectional",
                    "data": {
                        "sourceRole": "wird_geliefert_in",
                        "targetRole": "",
                        "sourceMultiplicity": "n",
                        "targetMultiplicity": "1"
                    }
                },
                {
                    "id": "rel-3",
                    "source": "clz-werbung",
                    "target": "clz-anbieter",
                    "type": "ClassUnidirectional",
                    "data": {
                        "sourceRole": "schaltet",
                        "targetRole": "",
                        "sourceMultiplicity": "n",
                        "targetMultiplicity": "1"
                    }
                },
                {
                    "id": "rel-4",
                    "source": "clz-produkt",
                    "target": "clz-werbung",
                    "type": "ClassUnidirectional",
                    "data": {
                        "sourceRole": "bewirbt",
                        "targetRole": "",
                        "sourceMultiplicity": "n",
                        "targetMultiplicity": "1"
                    }
                },
                {
                    "id": "rel-5",
                    "source": "clz-nutzer",
                    "target": "clz-lieferung",
                    "type": "ClassUnidirectional",
                    "data": {
                        "sourceRole": "beauftragt",
                        "targetRole": "",
                        "sourceMultiplicity": "n",
                        "targetMultiplicity": "1"
                    }
                }
            ]
        }

        analyzer = j2s_mod.ModelAnalyzer(data)
        generator = j2s_mod.SQLGenerator(analyzer)
        
        # All 5 classes should be present in analyzer
        assert len(analyzer.class_elements) == 5
        
        # Generate SQL
        sorted_ids = generator._topological_sort()
        
        # All 5 tables must be included in the output
        assert len(sorted_ids) == 5, f"Expected 5 tables, got {len(sorted_ids)}: {sorted_ids}"
        
        # Verify all expected class IDs are present
        expected_ids = {'clz-nutzer', 'clz-produkt', 'clz-anbieter', 'clz-werbung', 'clz-lieferung'}
        actual_ids = set(sorted_ids)
        assert actual_ids == expected_ids, f"Missing tables: {expected_ids - actual_ids}"
        
        # Generate full SQL
        sql = generator.generate()
        
        # Verify all table names appear in the SQL
        assert 'CREATE TABLE "Nutzer"' in sql
        assert 'CREATE TABLE "Produkt"' in sql
        assert 'CREATE TABLE "Anbieter"' in sql
        assert 'CREATE TABLE "Werbung"' in sql
        assert 'CREATE TABLE "Lieferung"' in sql
        
    def test_no_circular_dependency_correct_order(self):
        """Test that tables without circular dependencies are ordered correctly."""
        data = {
            "nodes": [
                {
                    "id": "clz-a",
                    "type": "class",
                    "data": {
                        "name": "A",
                        "attributes": [{"id": "att-a-id", "name": "auto id"}],
                        "methods": []
                    }
                },
                {
                    "id": "clz-b",
                    "type": "class",
                    "data": {
                        "name": "B",
                        "attributes": [{"id": "att-b-id", "name": "auto id"}],
                        "methods": []
                    }
                },
                {
                    "id": "clz-c",
                    "type": "class",
                    "data": {
                        "name": "C",
                        "attributes": [{"id": "att-c-id", "name": "auto id"}],
                        "methods": []
                    }
                }
            ],
            "edges": [
                {
                    "id": "rel-1",
                    "source": "clz-b",
                    "target": "clz-a",
                    "type": "ClassUnidirectional",
                    "data": {
                        "sourceRole": "ref_a",
                        "sourceMultiplicity": "n",
                        "targetMultiplicity": "1"
                    }
                },
                {
                    "id": "rel-2",
                    "source": "clz-c",
                    "target": "clz-b",
                    "type": "ClassUnidirectional",
                    "data": {
                        "sourceRole": "ref_b",
                        "sourceMultiplicity": "n",
                        "targetMultiplicity": "1"
                    }
                }
            ]
        }

        analyzer = j2s_mod.ModelAnalyzer(data)
        generator = j2s_mod.SQLGenerator(analyzer)
        sorted_ids = generator._topological_sort()
        
        # All tables should be present
        assert len(sorted_ids) == 3
        
        # A should come before B, and B should come before C
        idx_a = sorted_ids.index('clz-a')
        idx_b = sorted_ids.index('clz-b')
        idx_c = sorted_ids.index('clz-c')
        
        assert idx_a < idx_b, "A should come before B"
        assert idx_b < idx_c, "B should come before C"

    def test_isolated_tables_included(self):
        """Test that tables with no relationships are still included."""
        data = {
            "nodes": [
                {
                    "id": "clz-isolated1",
                    "type": "class",
                    "data": {
                        "name": "Isolated1",
                        "attributes": [{"id": "att-1", "name": "auto id"}],
                        "methods": []
                    }
                },
                {
                    "id": "clz-isolated2",
                    "type": "class",
                    "data": {
                        "name": "Isolated2",
                        "attributes": [{"id": "att-2", "name": "auto id"}],
                        "methods": []
                    }
                },
                {
                    "id": "clz-related1",
                    "type": "class",
                    "data": {
                        "name": "Related1",
                        "attributes": [{"id": "att-3", "name": "auto id"}],
                        "methods": []
                    }
                },
                {
                    "id": "clz-related2",
                    "type": "class",
                    "data": {
                        "name": "Related2",
                        "attributes": [{"id": "att-4", "name": "auto id"}],
                        "methods": []
                    }
                }
            ],
            "edges": [
                {
                    "id": "rel-1",
                    "source": "clz-related2",
                    "target": "clz-related1",
                    "type": "ClassUnidirectional",
                    "data": {
                        "sourceRole": "ref",
                        "sourceMultiplicity": "n",
                        "targetMultiplicity": "1"
                    }
                }
            ]
        }

        analyzer = j2s_mod.ModelAnalyzer(data)
        generator = j2s_mod.SQLGenerator(analyzer)
        sorted_ids = generator._topological_sort()
        
        # All 4 tables must be present
        assert len(sorted_ids) == 4
        
        expected_ids = {'clz-isolated1', 'clz-isolated2', 'clz-related1', 'clz-related2'}
        actual_ids = set(sorted_ids)
        assert actual_ids == expected_ids
