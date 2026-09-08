import pytest
from fastapi.testclient import TestClient
from studio.app import app, OUTPUT_DIR
from unittest.mock import patch
import os

client = TestClient(app)

def test_check_status_path_traversal():
    """Test that path traversal attempts in prefix are sanitized or rejected for check_status."""
    
    # We mock glob.glob to see what it is called with.
    # If the vulnerability exists, glob will be called with a path containing traversal.
    
    prefix = "../../../secret_file"
    
    with patch("glob.glob") as mock_glob:
        mock_glob.return_value = [] # Return empty to just check the call arg
        
        response = client.get(f"/api/check_status?prefix={prefix}")
        
        assert response.status_code == 200 # Should probably still be 200 with {ready: false}
        assert response.json() == {"ready": False}

        # Check what glob was called with
        # If traversal is blocked, glob might NOT be called at all.
        if mock_glob.called:
            args, _ = mock_glob.call_args
            search_path = args[0]
            
            # We assertion FAILs if the path contains ".." or resolves outside OUTPUT_DIR
            assert ".." not in search_path
            # And specifically check it doesn't try to access the secret file
            # Note: In the failing test (current code), this assertion will fail.
            assert "/secret_file" not in search_path or search_path.startswith(os.path.join(OUTPUT_DIR, "secret_file"))
        else:
             # This is also a pass - we prevented the file access
             pass
