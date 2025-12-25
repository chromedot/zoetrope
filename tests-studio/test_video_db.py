import unittest
import database
import os
import sqlite3

# Use a test database
TEST_DB_PATH = "data/test_story_studio_video.db"

class TestVideoDatabase(unittest.TestCase):
    def setUp(self):
        # Set the DB_PATH in database module
        database.DB_PATH = TEST_DB_PATH
        
        # Initialize the test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        database.init_db()

    def tearDown(self):
        # Cleanup
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_video_record_lifecycle(self):
        """Test creating, updating, and deleting video records."""
        story_name = "test_video_story"
        transition = "fade"
        duration = 1.5
        
        # Create
        video_id = database.create_video_record(story_name, transition, duration)
        self.assertIsNotNone(video_id)
        
        # Verify initial state
        videos = database.get_all_videos()
        self.assertEqual(len(videos), 0) # Should be 0 because status is 'pending'
        
        # Update to completed
        filename = "test_video.mp4"
        database.update_video_record(video_id, filename, status='completed')
        
        # Verify completed state
        videos = database.get_all_videos()
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]['story_name'], story_name)
        self.assertEqual(videos[0]['filename'], filename)
        
        # Delete
        database.delete_video_record(video_id)
        videos = database.get_all_videos()
        self.assertEqual(len(videos), 0)

if __name__ == "__main__":
    unittest.main()
