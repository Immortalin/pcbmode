import unittest
from unittest.mock import patch

import os
import pkg_resources

import pcbmode.config
from pcbmode.config import Config

class TestConfig(unittest.TestCase):
    """Test config dictionary"""

    def setUp(self):
        self.top_level_keys = 'cfg brd stl pth msg stk rte tmp'.split()

    def test_config_dict_entries(self):
        expected_keys = 'cfg brd stl pth msg stk'.split()
        for key in expected_keys:
            with self.subTest(key=key):
                self.assertTrue(hasattr(pcbmode.config, key), 'config should contain {} dict'.format(key))

    def test_config_class_properties(self):
        c = Config()
        for prop in self.top_level_keys:
            attr_dict = getattr(c, prop, None)
            self.assertIsNotNone(attr_dict, 'Config class should have {} property'.format(prop))

    def test_config_properties_are_same_as_globals(self):
        c = Config()
        c.tmp['test'] = 'data'
        self.assertEqual(pcbmode.config.tmp.get('test'), 'data', 'object attribute and global should be same dict')

    def test_config_init_with_clean(self):
        c1 = Config()
        c1.tmp['test'] = 'data'
        c2 = Config()
        self.assertEqual(c2.tmp['test'], 'data', 'config object should reuse config by default')
        c3 = Config(clean=True)
        with self.assertRaises(KeyError, msg='config object should not reuse config if clean is set'):
            val = c3.tmp['test']
        c4 = Config(clean=True, defaults={'tmp':{'fish': 'salmon'}})
        self.assertEqual(c4.tmp['fish'], 'salmon', 'config object should clean with defaults if supplied')
        c5 = Config()
        self.assertEqual(c5.tmp['fish'], 'salmon', 'config object should retain defaults from earlier instance')

    def test_config_get_with_no_top_level_key(self):
        c = Config()
        with self.assertRaises(KeyError, msg='should raise KeyError when no top-level key supplied to get()'):
            c.get()

    def test_config_get_with_nonexistent_top_level_key(self):
        c = Config()
        with self.assertRaises(KeyError, msg='should raise KeyError when nonexistent top-level key supplied to get()'):
            c.get('no_such_key')

    def test_config_get_with_top_level_only(self):
        c = Config()
        for top in self.top_level_keys:
            dict_from_attr = getattr(c, top)
            dict_from_get = c.get(top)
            self.assertIs(dict_from_get, dict_from_attr, 'top-level get should return same object as attribute')

    def test_config_get_with_two_levels(self):
        c = Config()
        for top in self.top_level_keys:
            dict_from_attr = getattr(c, top)
            dict_from_attr['example_key'] = '{}_value'.format(top)
            value = c.get(top, 'example_key')
            self.assertEqual(value, '{}_value'.format(top), 'should get expected value from two-level config get()')

    def test_config_get_with_three_levels(self):
        c = Config()
        for top in self.top_level_keys:
            dict_from_attr = getattr(c, top)
            dict_from_attr['second'] = { 'third': 'value_for_{}'.format(top) }
            self.assertEqual(c.get(top, 'second', 'third'), 'value_for_{}'.format(top), 'should get expected value from three-level config get()')
            self.assertEqual(c.get(top, 'second', 'nonexistent'), None, 'should get None from nonexistent dict item')

    def test_config_get_with_array(self):
        c = Config()
        for top in self.top_level_keys:
            dict_from_attr = getattr(c, top)
            dict_from_attr['food'] = [ { 'fruit': 'apple' }, { 'fruit': 'banana' } ]
            self.assertEqual(c.get(top, 'food', 0, 'fruit'), 'apple', 'should get expected value from first item in array')
            self.assertEqual(c.get(top, 'food', 1, 'fruit'), 'banana', 'should get expected value from second item in array')
            self.assertEqual(c.get(top, 'food', 2, 'fruit'), None, 'should get None from nonexistent array item')

    def test_load_defaults(self):
        c = Config()
        c.load_defaults()
        self.assertEqual(c.get('cfg', 'refdef-index', 'common', 'AT'), 'Attenuator', 'should read global config file')

    def test_global_config_path(self):
        c = Config()
        self.assertEqual(c.global_config_path, pkg_resources.resource_filename('pcbmode', pcbmode.config.DEFAULT_CONFIG_FILENAME), 'should get correct global config path')

    @patch('pcbmode.config.Config._default_config_filename', 'no_such_file.json')
    def test_global_config_path_with_custom_filename(self):
        c = Config()
        self.assertEqual(c.global_config_path, pkg_resources.resource_filename('pcbmode', 'no_such_file.json'), 'should get correct global config path with custom filename')

    @patch('pcbmode.utils.messages.error')
    @patch('pcbmode.config.Config._default_config_filename', 'no_such_file.json')
    def test_load_defaults_with_missing_global_file(self, e):
        c = Config()
        c.load_defaults()
        e.assert_called_once()
        self.assertRegex(e.call_args[0][0], r"Couldn't open PCBmodE's configuration file no_such_file\.json")

    def test_path_in_location_without_base_dir(self):
        c = Config(clean=True)
        self.assertIsNone(c.get('cfg', 'base-dir'), 'base-dir should not be set')
        with self.assertRaisesRegex(Exception, r"cannot determine paths until base-dir has been set"):
            c.path_in_location('build', 'test.svg')

    def test_path_in_location_with_unknown_location(self):
        c = Config(clean=True)
        c.cfg['base-dir'] = os.getcwd()
        self.assertIsNotNone(c.get('cfg', 'base-dir'), 'base-dir should be set')
        with self.assertRaisesRegex(Exception, r'cannot determine path for unknown location'):
            c.path_in_location('build', 'test.svg')

    def test_path_in_location_with_known_location(self):
        c = Config(clean=True)
        c.cfg['base-dir'] = 'some_base_dir'
        c.cfg['locations'] = { 'build' : 'some_build_directory' }
        self.assertEqual(c.get('cfg', 'base-dir'), 'some_base_dir', 'base-dir should be set')
        self.assertEqual(c.get('cfg', 'locations', 'build'), 'some_build_directory', 'locations.build should be set')
        path = c.path_in_location('build', 'test.svg')
        self.assertEqual(path, os.path.join('some_base_dir', 'some_build_directory', 'test.svg'), 'should get expected file path')

    def test_path_in_location_with_known_location_absolute(self):
        c = Config(clean=True)
        c.cfg['base-dir'] = 'some_base_dir'
        c.cfg['locations'] = { 'build': 'some_build_directory' }
        self.assertEqual(c.get('cfg', 'base-dir'), 'some_base_dir', 'base-dir should be set')
        self.assertEqual(c.get('cfg', 'locations', 'build'), 'some_build_directory', 'locations.build should be set')
        path = c.path_in_location('build', 'test.svg', absolute=True)
        self.assertEqual(path, os.path.join(os.getcwd(), 'some_base_dir', 'some_build_directory', 'test.svg'), 'should get expected file path')

    def test_longer_path_in_location_with_known_location(self):
        c = Config(clean=True)
        c.cfg['base-dir'] = 'some_base_dir'
        c.cfg['locations'] = { 'build' : 'some_build_directory' }
        self.assertEqual(c.get('cfg', 'base-dir'), 'some_base_dir', 'base-dir should be set')
        self.assertEqual(c.get('cfg', 'locations', 'build'), 'some_build_directory', 'locations.build should be set')
        path = c.path_in_location('build', 'some_intermediate_dir', 'another_intermediate_dir', 'test.svg')
        self.assertEqual(path, os.path.join('some_base_dir', 'some_build_directory', 'some_intermediate_dir', 'another_intermediate_dir', 'test.svg'), 'should get expected file path')

    def test_longer_path_in_location_with_known_location_absolute(self):
        c = Config(clean=True)
        c.cfg['base-dir'] = 'some_base_dir'
        c.cfg['locations'] = { 'build': 'some_build_directory' }
        self.assertEqual(c.get('cfg', 'base-dir'), 'some_base_dir', 'base-dir should be set')
        self.assertEqual(c.get('cfg', 'locations', 'build'), 'some_build_directory', 'locations.build should be set')
        path = c.path_in_location('build', 'some_intermediate_dir', 'another_intermediate_dir', 'test.svg', absolute=True)
        self.assertEqual(path, os.path.join(os.getcwd(), 'some_base_dir', 'some_build_directory', 'some_intermediate_dir', 'another_intermediate_dir', 'test.svg'), 'should get expected file path')