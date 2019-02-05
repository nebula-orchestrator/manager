import os
from unittest import TestCase
from functions.db.mongo import *


def mongo_connection():
    mongo_url = os.getenv("MONGO_URL", "mongodb://nebula:nebula@127.0.0.1:27017/nebula?authSource=admin")
    connection = MongoConnection(mongo_url)
    return connection


def create_temp_app(mongo_connection_object, app):
    app_conf = {
        "starting_ports": [80],
        "containers_per": {"server": 1},
        "env_vars": {"TEST": "test123"},
        "docker_image": "nginx"
    }
    reply = mongo_connection_object.mongo_add_app(app, app_conf["starting_ports"],  app_conf["containers_per"],
                                                  app_conf["env_vars"], app_conf["docker_image"])
    return reply


class MongoTests(TestCase):

    def test_mongo_app_flow(self):
        mongo_connection_object = mongo_connection()

        # ensure no test app is already created in the unit test DB
        mongo_connection_object.mongo_remove_app("unit_test_app")

        # check create test app works
        test_reply = create_temp_app(mongo_connection_object, "unit_test_app")
        self.assertEqual(test_reply["app_id"], 1)
        self.assertEqual(test_reply["app_name"], "unit_test_app")
        self.assertEqual(test_reply["containers_per"], {"server": 1})
        self.assertEqual(test_reply["devices"], [])
        self.assertEqual(test_reply["docker_image"], "nginx")
        self.assertEqual(test_reply["env_vars"], {"TEST": "test123"})
        self.assertEqual(test_reply["networks"], "nebula")
        self.assertFalse(test_reply["privileged"])
        self.assertFalse(test_reply["rolling_restart"])
        self.assertTrue(test_reply["running"])
        self.assertEqual(test_reply["volumes"], [])

        # check getting test app data works
        app_exists, test_reply = mongo_connection_object.mongo_get_app("unit_test_app")
        self.assertTrue(app_exists)
        self.assertEqual(test_reply["app_id"], 1)
        self.assertEqual(test_reply["app_name"], "unit_test_app")
        self.assertEqual(test_reply["containers_per"], {"server": 1})
        self.assertEqual(test_reply["devices"], [])
        self.assertEqual(test_reply["docker_image"], "nginx")
        self.assertEqual(test_reply["env_vars"], {"TEST": "test123"})
        self.assertEqual(test_reply["networks"], "nebula")
        self.assertFalse(test_reply["privileged"])
        self.assertFalse(test_reply["rolling_restart"])
        self.assertTrue(test_reply["running"])
        self.assertEqual(test_reply["volumes"], [])

        # check getting test app data non existing app
        app_exists, test_reply = mongo_connection_object.mongo_get_app("unit_test_app_that_doesnt_exist")
        self.assertFalse(app_exists)

        # check if app exists works
        test_reply = mongo_connection_object.mongo_check_app_exists("unit_test_app")
        self.assertTrue(test_reply)
        test_reply = mongo_connection_object.mongo_check_app_exists("unit_test_app_that_doesnt_exist")
        self.assertFalse(test_reply)

        # check getting app envvars works
        test_reply = mongo_connection_object.mongo_list_app_envvars("unit_test_app")
        self.assertEqual(test_reply, {"TEST": "test123"})

        # check updating app envvars works
        test_reply = mongo_connection_object.mongo_update_app_envars("unit_test_app", {"NEW_TEST": "new_test123"})
        self.assertEqual(test_reply["env_vars"], {"NEW_TEST": "new_test123"})

        # check updating app somefield works
        test_reply = mongo_connection_object.mongo_update_app_fields("unit_test_app", {
            "env_vars":
                {"TESTING": "testing123"},
            "running": False
        })
        self.assertEqual(test_reply["env_vars"], {"TESTING": "testing123"})
        self.assertFalse(test_reply["running"])

        # check getting app number of containers per cpu works

        # check updating app number of containers per cpu works

        # check getting app starting ports works

        # check updating app starting ports works

        # check increase app id works

        # check getting app running state works

        # check updating app running state works

        # check getting list of apps works

        # check update test app works

        # check delete test app works

    def test_mongo_device_group_flow(self):
        mongo_connection_object = mongo_connection()
        self.assertEqual("", "")
