import pytest
import os
import json
import sqlite3
import database
from scripts.story_manager import StoryManager

# Use a test database
TEST_DB_PATH = "data/test_story_studio_narration.db"
TEST_STORY_FILE = "data/stories/test_narration.story"

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", TEST_DB_PATH)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    database.init_db()
    
    # Setup test story file
    if not os.path.exists(os.path.dirname(TEST_STORY_FILE)):
        os.makedirs(os.path.dirname(TEST_STORY_FILE))
        
    test_data = [{"scene": 1, "description": "test", "prompt": "test"}]
    with open(TEST_STORY_FILE, "w") as f:
        json.dump(test_data, f)
        
    yield
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    if os.path.exists(TEST_STORY_FILE):
        os.remove(TEST_STORY_FILE)

def test_database_has_narration_columns():
    """Verify that the generated_images table has the new columns."""
    conn = database.get_db_connection()
    cursor = conn.execute("PRAGMA table_info(generated_images)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    
    assert "narration_text" in columns
    assert "audio_file" in columns

def test_story_manager_handles_narration():
    """Verify that StoryManager can save and load narration text."""
    manager = StoryManager(TEST_STORY_FILE)
    
    # Update narration
    manager.story_data[0]["narration_text"] = "This is a test narration."
    manager.save_story()
    
    # Reload and verify
    new_manager = StoryManager(TEST_STORY_FILE)
    assert new_manager.story_data[0]["narration_text"] == "This is a test narration."
