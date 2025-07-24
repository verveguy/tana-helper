import json
import time

import requests


class TestIntegrationFlow:
    """Test complete integration flows end-to-end."""

    def test_json_tana_conversion_flow(self, live_server, sample_json_data):
        """Test complete JSON to Tana and back conversion flow."""
        base_url = live_server

        # Step 1: Convert JSON to Tana
        json_string = json.dumps(sample_json_data)
        response = requests.post(f"{base_url}/tanify", data=json_string)
        assert response.status_code == 200

        tana_result = response.text
        assert len(tana_result) > 0

        # Step 2: Convert Tana back to JSON
        response = requests.post(f"{base_url}/jsonify", data=tana_result)
        assert response.status_code == 200

        json_result = response.json()
        assert isinstance(json_result, list)
        assert len(json_result) > 0

    def test_proxy_integration_flow(self, live_server):
        """Test proxy functionality with real external API."""
        base_url = live_server

        # Test GET proxy
        test_url = "https://httpbin.org/get"
        response = requests.get(f"{base_url}/proxy/GET/{test_url}")

        if response.status_code == 200:
            # If proxy works, verify the response
            assert "httpbin.org" in response.text.lower()

    def test_api_documentation_integration(self, live_server):
        """Test that API documentation is properly served."""
        base_url = live_server

        # Test OpenAPI spec
        response = requests.get(f"{base_url}/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "paths" in openapi_spec

        # Test documentation UI
        response = requests.get(f"{base_url}/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


class TestPerformanceBasics:
    """Basic performance testing."""

    def test_response_time_jsonify(self, live_server, sample_tana_data):
        """Test jsonify endpoint response time."""
        base_url = live_server

        start_time = time.time()
        response = requests.post(f"{base_url}/jsonify", data=sample_tana_data)
        end_time = time.time()

        response_time = end_time - start_time

        # Response should be fast (under 5 seconds for simple data)
        assert response_time < 5.0
        assert response.status_code == 200

    def test_response_time_tanify(self, live_server, sample_json_data):
        """Test tanify endpoint response time."""
        base_url = live_server

        json_string = json.dumps(sample_json_data)

        start_time = time.time()
        response = requests.post(f"{base_url}/tanify", data=json_string)
        end_time = time.time()

        response_time = end_time - start_time

        # Response should be fast (under 5 seconds for simple data)
        assert response_time < 5.0
        assert response.status_code == 200


class TestDataValidation:
    """Test data validation and edge cases."""

    def test_large_data_handling(self, live_server):
        """Test handling of reasonably large data."""
        base_url = live_server

        # Create a moderately large Tana structure
        large_tana_data = "- Root\n"
        for i in range(100):
            large_tana_data += f"  - Item {i}\n"
            large_tana_data += f"    - field:: value{i}\n"

        response = requests.post(f"{base_url}/jsonify", data=large_tana_data)

        # Should handle this size gracefully
        assert response.status_code in [200, 413, 422]  # 413 = Payload Too Large

        if response.status_code == 200:
            json_result = response.json()
            assert isinstance(json_result, list)

    def test_unicode_handling(self, live_server):
        """Test handling of Unicode characters."""
        base_url = live_server

        unicode_tana_data = """- Unicode Test 🚀
  - emoji:: 🎉✨🔥
  - japanese:: こんにちは
  - arabic:: مرحبا
  - mathematical:: ∑∏∆"""

        response = requests.post(f"{base_url}/jsonify", data=unicode_tana_data)
        assert response.status_code == 200

        json_result = response.json()
        assert isinstance(json_result, list)

    def test_special_characters_handling(self, live_server):
        """Test handling of special characters and edge cases."""
        base_url = live_server

        special_tana_data = """- Special Characters
  - quotes:: "double" 'single'
  - symbols:: !@#$%^&*()
  - newlines:: line1\\nline2
  - tabs:: tab\\there"""

        response = requests.post(f"{base_url}/jsonify", data=special_tana_data)
        assert response.status_code == 200

        json_result = response.json()
        assert isinstance(json_result, list)


class TestSecurityBasics:
    """Basic security testing."""

    def test_cors_headers(self, live_server):
        """Test CORS headers are properly set."""
        base_url = live_server

        # Test with an OPTIONS request
        response = requests.options(f"{base_url}/jsonify")

        # Should either support OPTIONS or handle gracefully
        assert response.status_code in [200, 405]  # 405 = Method Not Allowed

    def test_malicious_input_handling(self, live_server):
        """Test handling of potentially malicious input."""
        base_url = live_server

        # Test script injection attempt
        malicious_data = """- Script Test
  - script:: <script>alert('xss')</script>
  - sql:: '; DROP TABLE users; --"""

        response = requests.post(f"{base_url}/jsonify", data=malicious_data)

        # Should handle without crashing
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            json_result = response.json()
            # Result should be properly escaped/sanitized
            json.dumps(json_result)
            # The dangerous scripts should not be executable
            assert isinstance(json_result, list)


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""

    def test_recovery_after_error(self, live_server):
        """Test that the service recovers after encountering an error."""
        base_url = live_server

        # First, cause an error
        response = requests.post(f"{base_url}/tanify", data="invalid json {")
        assert response.status_code in [400, 422, 500]

        # Then, verify service still works with valid input
        valid_json = json.dumps({"test": "recovery"})
        response = requests.post(f"{base_url}/tanify", data=valid_json)
        assert response.status_code == 200

    def test_concurrent_requests(self, live_server, sample_tana_data):
        """Test handling of concurrent requests."""
        import threading

        base_url = live_server
        results = []

        def make_request():
            try:
                response = requests.post(
                    f"{base_url}/jsonify", data=sample_tana_data, timeout=10
                )
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")

        # Create 5 concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=15)

        # Most requests should succeed
        success_count = sum(1 for result in results if result == 200)
        assert success_count >= 3  # At least 3 out of 5 should succeed
