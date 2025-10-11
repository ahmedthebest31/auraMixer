import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# We must import the script we are testing. Since it's not a module, we load it carefully.
# This is a common pattern for testing standalone scripts.
import auramixer

class TestAuramixer(unittest.TestCase):

    def test_get_resource_path_normal_mode(self):
        """Tests get_resource_path when running as a standard Python script."""
        # In normal mode, it should resolve to an absolute path based on the current directory.
        relative = os.path.join('assets', 'icon.png')
        expected_path = os.path.abspath(relative)
        self.assertEqual(auramixer.get_resource_path(relative), expected_path)

    @patch('auramixer.sys')
    def test_get_resource_path_frozen_mode(self, mock_sys):
        """Tests get_resource_path when running as a PyInstaller executable."""
        # Mock the sys._MEIPASS attribute that PyInstaller sets.
        mock_sys._MEIPASS = '/tmp/_MEI12345'
        relative = 'assets/icon.png'
        expected_path = os.path.join(mock_sys._MEIPASS, relative)
        self.assertEqual(auramixer.get_resource_path(relative), expected_path)

    @patch('os.makedirs')
    def test_setup_asset_paths_portable_mode(self, mock_makedirs):
        """Tests asset path setup in portable mode."""
        # In portable mode, paths should be relative to the current directory.
        paths, needs_notification = auramixer.setup_asset_paths(is_portable=True)

        # Check that the base path is the current directory.
        self.assertEqual(paths['base'], os.path.abspath('.'))
        self.assertFalse(needs_notification) # Should not notify if creating in-place.

        # Check that it tried to create the correct directories.
        expected_calls = [
            call(os.path.abspath('./backgrounds'), exist_ok=True),
            call(os.path.abspath('./effects'), exist_ok=True),
            call(os.path.abspath('./music'), exist_ok=True),
        ]
        mock_makedirs.assert_has_calls(expected_calls, any_order=True)

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False) # Assume the Auramixer dir doesn't exist yet
    @patch('os.path.expanduser', return_value='/home/user')
    def test_setup_asset_paths_non_portable_mode_first_run(self, mock_expanduser, mock_exists, mock_makedirs):
        """Tests asset path setup in non-portable mode for a first-time run."""
        # In non-portable mode, paths should be in the user's Documents folder.
        paths, needs_notification = auramixer.setup_asset_paths(is_portable=False)

        documents_path = os.path.join('/home/user', 'Documents', 'Auramixer')
        self.assertEqual(paths['base'], documents_path)
        self.assertTrue(needs_notification) # Should notify on first run.

        # Check that it tried to create the correct directories.
        expected_calls = [
            call(os.path.join(documents_path, 'backgrounds'), exist_ok=True),
            call(os.path.join(documents_path, 'effects'), exist_ok=True),
            call(os.path.join(documents_path, 'music'), exist_ok=True),
        ]
        mock_makedirs.assert_has_calls(expected_calls, any_order=True)

    @patch('auramixer.pygame.image.load')
    @patch('auramixer.pygame.mixer.Sound')
    @patch('os.listdir')
    def test_load_all_assets_all_missing(self, mock_listdir, mock_sound, mock_image_load):
        """Tests that load_all_assets correctly identifies all missing asset types."""
        # Pretend all asset directories are empty.
        mock_listdir.return_value = []

        asset_paths = {
            'backgrounds': '/fake/backgrounds',
            'effects': '/fake/effects',
            'music': '/fake/music'
        }

        assets, is_fatal, missing = auramixer.load_all_assets(asset_paths)

        # Assert that the asset lists are empty.
        self.assertEqual(assets['backgrounds'], [])
        self.assertEqual(assets['effects'], [])
        self.assertEqual(assets['music'], [])

        # Assert that it correctly reports a fatal error and lists all missing types.
        self.assertTrue(is_fatal)
        self.assertIn('backgrounds', missing)
        self.assertIn('effects', missing)
        self.assertIn('music', missing)

    @patch('auramixer.pygame.image.load', MagicMock())
    @patch('auramixer.pygame.mixer.Sound', MagicMock())
    @patch('os.listdir')
    def test_load_all_assets_some_present(self, mock_listdir):
        """Tests that load_all_assets correctly identifies partially missing assets."""
        # Mock the file system to return some files for music, but none for others.
        def listdir_side_effect(path):
            if 'music' in path:
                return ['track1.mp3', 'track2.ogg']
            return []
        mock_listdir.side_effect = listdir_side_effect

        asset_paths = {
            'backgrounds': '/fake/backgrounds',
            'effects': '/fake/effects',
            'music': '/fake/music'
        }

        assets, is_fatal, missing = auramixer.load_all_assets(asset_paths)

        # Assert that only the music list is populated.
        self.assertEqual(len(assets['music']), 2)
        self.assertEqual(len(assets['backgrounds']), 0)
        self.assertEqual(len(assets['effects']), 0)

        # A fatal error should still be true because effects are missing.
        self.assertTrue(is_fatal)
        self.assertIn('backgrounds', missing)
        self.assertIn('effects', missing)
        self.assertNotIn('music', missing)

if __name__ == '__main__':
    # This allows the test to be run from the command line.
    unittest.main()
