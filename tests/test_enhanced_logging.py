"""
Test script to verify enhanced logging functionality.

This script demonstrates and tests the enhanced logging capabilities including:
- Structured JSON logging
- Full stack trace capture
- Sensitive data redaction
- Request context extraction
"""

import sys
import os
import json
import logging
from io import StringIO

# Add libs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs', 'python'))

from common.enhanced_logging import (
    setup_enhanced_logging,
    get_enhanced_logger,
    redact_sensitive_data,
    format_exception_details,
    EnhancedJSONFormatter,
)


def test_sensitive_data_redaction():
    """Test that sensitive data is properly redacted."""
    print("\n=== Testing Sensitive Data Redaction ===")
    
    test_data = {
        "username": "john.doe",
        "password": "super_secret_123",
        "email": "john@example.com",
        "api_key": "sk_live_abc123xyz789",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "credit_card": "4532-1234-5678-9010",
        "normal_field": "this should not be redacted",
        "nested": {
            "secret": "nested_secret",
            "public": "public_data"
        }
    }
    
    redacted = redact_sensitive_data(test_data)
    
    print("Original data:")
    print(json.dumps(test_data, indent=2))
    print("\nRedacted data:")
    print(json.dumps(redacted, indent=2))
    
    # Verify redaction
    assert redacted["password"] == "[REDACTED]", "Password should be redacted"
    assert redacted["api_key"] == "[REDACTED]", "API key should be redacted"
    assert redacted["token"] == "[REDACTED]", "Token should be redacted"
    assert redacted["credit_card"] == "[REDACTED]", "Credit card should be redacted"
    assert redacted["username"] == "john.doe", "Username should not be redacted"
    assert redacted["normal_field"] == "this should not be redacted", "Normal field should not be redacted"
    assert redacted["nested"]["secret"] == "[REDACTED]", "Nested secret should be redacted"
    assert redacted["nested"]["public"] == "public_data", "Nested public field should not be redacted"
    
    print("\n✅ Sensitive data redaction test passed!")


def test_exception_formatting():
    """Test that exceptions are properly formatted with full stack traces."""
    print("\n=== Testing Exception Formatting ===")
    
    def level_3():
        """Third level function that raises an exception."""
        raise ValueError("This is a test error with sensitive data: password=secret123")
    
    def level_2():
        """Second level function."""
        level_3()
    
    def level_1():
        """First level function."""
        level_2()
    
    try:
        level_1()
    except Exception as exc:
        error_details = format_exception_details(exc, include_locals=False)
        
        print("Exception details:")
        print(json.dumps(error_details, indent=2, default=str))
        
        # Verify exception details
        assert error_details["type"] == "ValueError", "Exception type should be ValueError"
        assert "This is a test error" in error_details["message"], "Exception message should be present"
        assert "traceback" in error_details, "Traceback should be present"
        assert "stack_frames" in error_details, "Stack frames should be present"
        assert len(error_details["stack_frames"]) > 0, "Should have stack frames"
        
        # Verify stack frame structure
        frame = error_details["stack_frames"][0]
        assert "file" in frame, "Frame should have file"
        assert "function" in frame, "Frame should have function"
        assert "line_number" in frame, "Frame should have line number"
        
        print("\n✅ Exception formatting test passed!")


def test_json_formatter():
    """Test the EnhancedJSONFormatter."""
    print("\n=== Testing JSON Formatter ===")
    
    # Create a string buffer to capture log output
    log_buffer = StringIO()
    handler = logging.StreamHandler(log_buffer)
    
    # Create formatter
    formatter = EnhancedJSONFormatter(
        service_name="test-service",
        environment="test",
        include_locals=False,
    )
    handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]
    
    # Log a message
    logger.info("Test message", extra={"extra_data": {"user_id": "123", "action": "test"}})
    
    # Get log output
    log_output = log_buffer.getvalue()
    print("Log output:")
    print(log_output)
    
    # Parse JSON
    log_data = json.loads(log_output)
    
    # Verify structure
    assert log_data["service"] == "test-service", "Service name should be present"
    assert log_data["environment"] == "test", "Environment should be present"
    assert log_data["level"] == "INFO", "Log level should be INFO"
    assert log_data["message"] == "Test message", "Message should be present"
    assert "timestamp" in log_data, "Timestamp should be present"
    assert "extra" in log_data, "Extra data should be present"
    assert log_data["extra"]["user_id"] == "123", "User ID should be in extra data"
    
    print("\n✅ JSON formatter test passed!")


def test_error_logging():
    """Test logging of errors with full stack traces."""
    print("\n=== Testing Error Logging ===")
    
    # Create a string buffer to capture log output
    log_buffer = StringIO()
    handler = logging.StreamHandler(log_buffer)
    
    # Create formatter
    formatter = EnhancedJSONFormatter(
        service_name="test-service",
        environment="test",
        include_locals=False,
    )
    handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger("test_error_logger")
    logger.setLevel(logging.ERROR)
    logger.handlers = [handler]
    
    # Create and log an exception
    try:
        raise RuntimeError("Test error for logging")
    except Exception as exc:
        logger.error("An error occurred", exc_info=True)
    
    # Get log output
    log_output = log_buffer.getvalue()
    print("Error log output:")
    print(log_output)
    
    # Parse JSON
    log_data = json.loads(log_output)
    
    # Verify error details
    assert log_data["level"] == "ERROR", "Log level should be ERROR"
    assert "error" in log_data, "Error details should be present"
    assert log_data["error"]["type"] == "RuntimeError", "Error type should be RuntimeError"
    assert "Test error for logging" in log_data["error"]["message"], "Error message should be present"
    assert "traceback" in log_data["error"], "Traceback should be present"
    assert "stack_frames" in log_data["error"], "Stack frames should be present"
    assert log_data["requires_investigation"] == True, "Should require investigation"
    assert log_data["alert_priority"] == "high", "Should have high alert priority"
    
    print("\n✅ Error logging test passed!")


def test_setup_enhanced_logging():
    """Test the setup_enhanced_logging function."""
    print("\n=== Testing Enhanced Logging Setup ===")
    
    # Setup enhanced logging
    setup_enhanced_logging(
        service_name="test-service",
        environment="test",
        log_level="INFO",
        include_locals=False,
        json_logs=True,
    )
    
    # Get logger
    logger = get_enhanced_logger("test_setup")
    
    # Verify logger is configured
    assert logger is not None, "Logger should be created"
    assert logger.level <= logging.INFO, "Logger level should be INFO or lower"
    
    print("Logger configured successfully")
    print(f"Logger name: {logger.name}")
    print(f"Logger level: {logging.getLevelName(logger.level)}")
    print(f"Number of handlers: {len(logger.handlers)}")
    
    print("\n✅ Enhanced logging setup test passed!")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Enhanced Logging Test Suite")
    print("=" * 60)
    
    try:
        test_sensitive_data_redaction()
        test_exception_formatting()
        test_json_formatter()
        test_error_logging()
        test_setup_enhanced_logging()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

