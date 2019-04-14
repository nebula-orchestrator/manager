from unittest import TestCase
from manager import *


class BaseTests(TestCase):

    def test_get_conf_setting_from_json_config(self):
        settings_json = {"test_json_key": "test_json_value"}
        test_value = get_conf_setting("test_json_key", settings_json, default_value="skip")
        self.assertEqual(test_value, "test_json_value")

    def test_get_conf_setting_true(self):
        settings_json = {"test_json_key": "true"}
        test_value = get_conf_setting("test_json_key", settings_json, default_value="skip")
        self.assertTrue(test_value)

    def test_get_conf_setting_false(self):
        settings_json = {"test_json_key": "false"}
        test_value = get_conf_setting("test_json_key", settings_json, default_value="skip")
        self.assertFalse(test_value)

    def test_get_conf_setting_from_default_value(self):
        settings_json = {"test_json_key": "test_json_value"}
        test_value = get_conf_setting("default_value_key_check", settings_json, default_value="default_value_value")
        self.assertEqual(test_value, "default_value_value")

    def test_get_conf_setting_from_envar(self):
        settings_json = {"test_json_key": "test_json_value"}
        test_value = get_conf_setting("default_value_key_check", settings_json, default_value="default_value_value")
        self.assertEqual(test_value, "default_value_value")

    def test_find_missing_params(self):
        test_reply = find_missing_params({}, ["docker_image"])
        self.assertEqual(test_reply, {"missing_parameters": ["docker_image"]})

    def test_return_sane_default_if_not_declared_param_declared(self):
        test_reply = return_sane_default_if_not_declared("test_param", {"test_param": "test_value"}, "param_default")
        self.assertEqual(test_reply, "test_value")

    def test_return_sane_default_if_not_declared_param_not_declared_default_exists(self):
        test_reply = return_sane_default_if_not_declared("test_param", {}, "param_default")
        self.assertEqual(test_reply, "param_default")

    def test_check_ports_valid_range_port_in_range(self):
        test_reply, text_reply_code = check_ports_valid_range([80, 81])
        self.assertEqual(text_reply_code, 200)

    def test_check_ports_valid_range_port_not_in_range(self):
        test_reply, text_reply_code = check_ports_valid_range([80, 643681, 81])
        self.assertEqual(text_reply_code, 400)
