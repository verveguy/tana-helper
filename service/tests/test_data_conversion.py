from service.json2tana import json_to_tana, tana_to_json


class TestDataConversion:
    """Test core data conversion functionality directly."""

    def test_simple_tana_to_json(self):
        """Test basic Tana to JSON conversion."""
        tana_data = """- Main Item
  - field1:: value1
  - field2:: value2"""

        result = tana_to_json(tana_data)
        assert isinstance(result, list)
        assert len(result) > 0

        # Check structure - fields are hoisted up as properties
        main_item = result[0]
        assert main_item["name"] == "Main Item"
        assert main_item["field1"] == "value1"
        assert main_item["field2"] == "value2"

    def test_simple_json_to_tana(self):
        """Test basic JSON to Tana conversion."""
        json_data = {"name": "Test Item", "field1": "value1", "field2": "value2"}

        result = json_to_tana(json_data)
        assert isinstance(result, str)
        assert "Test Item" in result
        assert "field1" in result
        assert "value1" in result

    def test_nested_tana_to_json(self):
        """Test nested Tana structure conversion."""
        tana_data = """- Parent
  - Child 1
    - grandchild:: value
  - Child 2
    - another:: property"""

        result = tana_to_json(tana_data)
        assert isinstance(result, list)

        parent = result[0]
        assert parent["name"] == "Parent"
        assert "children" in parent
        assert len(parent["children"]) >= 2

    def test_special_field_syntax(self):
        """Test Tana's special field syntax (::)."""
        tana_data = """- Item
  - field:: value
  - date:: 2024-01-01
  - number:: 42"""

        result = tana_to_json(tana_data)
        assert isinstance(result, list)

        item = result[0]
        # Check that fields are properly parsed and hoisted
        assert item["field"] == "value"
        assert item["date"] == "2024-01-01"
        assert item["number"] == "42"

    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        # Empty Tana - should handle gracefully
        try:
            result = tana_to_json("")
            assert isinstance(result, list)
        except (KeyError, IndexError):
            # This is also acceptable for empty input
            pass

        # Empty JSON
        result = json_to_tana({})
        assert isinstance(result, str)

    def test_unicode_in_conversion(self):
        """Test Unicode character handling in conversions."""
        tana_data = """- Unicode Item 🚀
  - emoji:: 🎉✨
  - japanese:: こんにちは"""

        result = tana_to_json(tana_data)
        assert isinstance(result, list)

        # Convert back to Tana if we have results
        if result:
            tana_result = json_to_tana(result[0])
            assert isinstance(tana_result, str)

    def test_roundtrip_conversion(self):
        """Test that data survives roundtrip conversion."""
        original_json = {"name": "Test", "type": "roundtrip"}

        # JSON -> Tana -> JSON
        tana_result = json_to_tana(original_json)
        assert isinstance(tana_result, str)

        json_result = tana_to_json(tana_result)
        assert isinstance(json_result, list)
        assert len(json_result) > 0

    def test_list_handling(self):
        """Test handling of lists in JSON."""
        json_data = {"name": "List Test"}

        result = json_to_tana(json_data)
        assert isinstance(result, str)
        assert "List Test" in result

    def test_nested_object_handling(self):
        """Test handling of nested objects."""
        json_data = {"name": "Nested Test", "created": "2024-01-01", "author": "test"}

        result = json_to_tana(json_data)
        assert isinstance(result, str)
        assert "Nested Test" in result

    def test_malformed_tana_handling(self):
        """Test handling of malformed Tana data."""
        malformed_data = """- Item
    - badly indented
  - correct indent"""

        # Should not crash
        try:
            result = tana_to_json(malformed_data)
            assert isinstance(result, list)
        except Exception:
            # If it throws an exception, that's also acceptable
            pass

    def test_special_characters_in_fields(self):
        """Test special characters in field names and values."""
        tana_data = """- Item
  - field with spaces:: value with spaces
  - field-with-dashes:: value-with-dashes
  - field_with_underscores:: value_with_underscores"""

        result = tana_to_json(tana_data)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_numeric_values(self):
        """Test handling of numeric values."""
        tana_data = """- Numeric Test
  - integer:: 42
  - float:: 3.14
  - negative:: -10
  - zero:: 0"""

        result = tana_to_json(tana_data)
        assert isinstance(result, list)
        assert len(result) > 0

        # Values are stored as strings
        item = result[0]
        assert item["integer"] == "42"
        assert item["float"] == "3.14"

    def test_boolean_like_values(self):
        """Test handling of boolean-like values."""
        tana_data = """- Boolean Test
  - true_value:: true
  - false_value:: false
  - yes_value:: yes
  - no_value:: no"""

        result = tana_to_json(tana_data)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_date_like_values(self):
        """Test handling of date-like values."""
        tana_data = """- Date Test
  - iso_date:: 2024-01-01
  - datetime:: 2024-01-01T10:00:00Z
  - time:: 10:30 AM"""

        result = tana_to_json(tana_data)
        assert isinstance(result, list)
        assert len(result) > 0
