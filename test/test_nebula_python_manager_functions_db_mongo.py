from unittest import TestCase
from functions.db.mongo import *
from functions.hashing.hashing import *


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
        test_reply = mongo_connection_object.mongo_list_app_containers_per("unit_test_app")
        self.assertEqual(test_reply, {"server": 1})

        # check updating app number of containers per cpu works
        test_reply = mongo_connection_object.mongo_update_app_containers_per("unit_test_app", {"server": 2})
        self.assertEqual(test_reply["containers_per"], {"server": 2})

        # check getting app starting ports works
        test_reply = mongo_connection_object.mongo_list_app_starting_ports("unit_test_app")
        self.assertEqual(test_reply, [80])

        # check updating app starting ports works
        test_reply = mongo_connection_object.mongo_update_app_starting_ports("unit_test_app", {"81": "80"})
        self.assertEqual(test_reply["starting_ports"], {"81": "80"})

        # check increase app id works
        test_reply = mongo_connection_object.mongo_increase_app_id("unit_test_app")
        test_app_id = test_reply["app_id"]
        test_reply = mongo_connection_object.mongo_increase_app_id("unit_test_app")
        self.assertEqual(test_reply["app_id"], test_app_id + 1)

        # check getting app running state works
        test_reply = mongo_connection_object.mongo_list_app_running_state("unit_test_app")
        self.assertFalse(test_reply)

        # check updating app running state works
        test_reply = mongo_connection_object.mongo_update_app_running_state("unit_test_app", True)
        self.assertTrue(test_reply)

        # check getting list of apps works
        test_reply = mongo_connection_object.mongo_list_apps()
        self.assertEqual(test_reply, ["unit_test_app"])

        # check update test app works
        test_reply = mongo_connection_object.mongo_increase_app_id("unit_test_app")
        test_app_id = test_reply["app_id"]
        updated_app_conf = {
            "starting_ports": [80],
            "containers_per": {"server": 1},
            "env_vars": {"TEST": "test123"},
            "docker_image": "nginx",
            "running": True,
            "networks": ["nebula"],
            "volumes": [],
            "devices": [],
            "privileged": True,
            "rolling_restart": True
        }
        test_reply = mongo_connection_object.mongo_update_app("unit_test_app", updated_app_conf["starting_ports"],
                                                              updated_app_conf["containers_per"],
                                                              updated_app_conf["env_vars"],
                                                              updated_app_conf["docker_image"],
                                                              updated_app_conf["running"],
                                                              updated_app_conf["networks"],
                                                              updated_app_conf["volumes"],
                                                              updated_app_conf["devices"],
                                                              updated_app_conf["privileged"],
                                                              updated_app_conf["rolling_restart"])
        self.assertEqual(test_reply["app_id"], test_app_id + 1)
        self.assertEqual(test_reply["app_name"], "unit_test_app")
        self.assertEqual(test_reply["containers_per"], {"server": 1})
        self.assertEqual(test_reply["devices"], [])
        self.assertEqual(test_reply["docker_image"], "nginx")
        self.assertEqual(test_reply["env_vars"], {"TEST": "test123"})
        self.assertEqual(test_reply["networks"], ["nebula"])
        self.assertTrue(test_reply["privileged"])
        self.assertTrue(test_reply["rolling_restart"])
        self.assertTrue(test_reply["running"])
        self.assertEqual(test_reply["volumes"], [])

        # check delete test app works
        test_reply = mongo_connection_object.mongo_remove_app("unit_test_app")
        self.assertEqual(test_reply.deleted_count, 1)

    def test_mongo_device_group_flow(self):
        mongo_connection_object = mongo_connection()

        # ensure no test app is already created in the unit test DB
        mongo_connection_object.mongo_remove_device_group("unit_test_device_group")

        # check create device group works
        test_reply = mongo_connection_object.mongo_add_device_group("unit_test_device_group", [])
        self.assertEqual(test_reply["apps"], [])
        self.assertEqual(test_reply["device_group"], "unit_test_device_group")
        self.assertEqual(test_reply["device_group_id"], 1)
        self.assertEqual(test_reply["prune_id"], 1)

        # check list device group works
        device_group_exists, test_reply = mongo_connection_object.mongo_get_device_group("unit_test_device_group")
        self.assertTrue(device_group_exists)
        self.assertEqual(test_reply["apps"], [])
        self.assertEqual(test_reply["device_group"], "unit_test_device_group")
        self.assertEqual(test_reply["device_group_id"], 1)
        self.assertEqual(test_reply["prune_id"], 1)

        # check list device groups works
        test_reply = mongo_connection_object.mongo_list_device_groups()
        self.assertEqual(test_reply, ["unit_test_device_group"])

        # check update device group works
        test_reply = mongo_connection_object.mongo_update_device_group("unit_test_device_group", [])
        self.assertEqual(test_reply["device_group"], "unit_test_device_group")
        self.assertEqual(test_reply["device_group_id"], 2)
        self.assertEqual(test_reply["prune_id"], 1)

        # check device group exists works
        test_reply = mongo_connection_object.mongo_check_device_group_exists("unit_test_device_group")
        self.assertTrue(test_reply)

        # check increase prune id works
        test_reply = mongo_connection_object.mongo_increase_prune_id("unit_test_device_group")
        test_prune_id = test_reply["prune_id"]
        test_reply = mongo_connection_object.mongo_increase_prune_id("unit_test_device_group")
        self.assertEqual(test_reply["prune_id"], test_prune_id + 1)

        # check delete device group works
        test_reply = mongo_connection_object.mongo_remove_device_group("unit_test_device_group")
        self.assertEqual(test_reply.deleted_count, 1)

    def test_mongo_user_flow(self):
        mongo_connection_object = mongo_connection()

        # ensure no test user is already created in the unit test DB
        mongo_connection_object.mongo_delete_user("unit_test_user")

        # check create user works
        test_reply = mongo_connection_object.mongo_add_user("unit_test_user", "unit_test_pass", "unit_test_token")
        self.assertEqual(test_reply["user_name"], "unit_test_user")
        self.assertEqual("unit_test_pass", test_reply["password"])
        self.assertEqual("unit_test_token", test_reply["token"])

        # check list user works
        user_exists, test_reply = mongo_connection_object.mongo_get_user("unit_test_user")
        self.assertTrue(user_exists)
        self.assertEqual("unit_test_pass", test_reply["password"])
        self.assertEqual("unit_test_token", test_reply["token"])

        # check list user works
        test_reply = mongo_connection_object.mongo_list_users()
        self.assertEqual(test_reply, ["unit_test_user"])

        # check update user works
        test_reply = mongo_connection_object.mongo_update_user("unit_test_user", {"token": "new_unit_test_token"})
        self.assertEqual("new_unit_test_token", test_reply["token"])

        # check user exists works
        test_reply = mongo_connection_object.mongo_check_user_exists("unit_test_user")
        self.assertTrue(test_reply)

        # check delete user works
        test_reply = mongo_connection_object.mongo_delete_user("unit_test_user")
        self.assertEqual(test_reply.deleted_count, 1)

    def test_mongo_user_group_flow(self):
        mongo_connection_object = mongo_connection()

        # ensure no test user_group is already created in the unit test DB
        mongo_connection_object.mongo_delete_user_group("unit_test_user_group")
        mongo_connection_object.mongo_delete_user_group("unit_test_user_group_2")


        # check create user_group works
        test_reply = mongo_connection_object.mongo_add_user_group(user_group="unit_test_user_group",
                                                                  group_members=[
                                                                      "unit_test_member_1",
                                                                      "unit_test_member_2"
                                                                  ],
                                                                  pruning_allowed=False,
                                                                  apps={
                                                                      "unit_test_app_1": "rw",
                                                                      "unit_test_app_2": "ro"
                                                                  },
                                                                  device_groups={
                                                                      "unit_test_dg_1": "rw",
                                                                      "unit_test_dg_2": "ro"
                                                                  },
                                                                  admin=True)
        self.assertEqual(test_reply["user_group"], "unit_test_user_group")
        self.assertEqual(test_reply["group_members"], ["unit_test_member_1", "unit_test_member_2"])
        self.assertFalse(test_reply["pruning_allowed"])
        self.assertEqual(test_reply["apps"], {"unit_test_app_1": "rw", "unit_test_app_2": "ro"})
        self.assertEqual(test_reply["device_groups"], {"unit_test_dg_1": "rw", "unit_test_dg_2": "ro"})
        self.assertTrue(test_reply["admin"])

        # check list user_group works
        user_group_exists, test_reply = mongo_connection_object.mongo_get_user_group("unit_test_user_group")
        self.assertTrue(user_group_exists)
        self.assertEqual(test_reply["user_group"], "unit_test_user_group")
        self.assertEqual(test_reply["group_members"], ["unit_test_member_1", "unit_test_member_2"])
        self.assertFalse(test_reply["pruning_allowed"])
        self.assertEqual(test_reply["apps"], {"unit_test_app_1": "rw", "unit_test_app_2": "ro"})
        self.assertEqual(test_reply["device_groups"], {"unit_test_dg_1": "rw", "unit_test_dg_2": "ro"})
        self.assertTrue(test_reply["admin"])

        # check list user_group works
        test_reply = mongo_connection_object.mongo_list_user_groups()
        self.assertEqual(test_reply, ["unit_test_user_group"])

        # check update user_group works
        test_reply = mongo_connection_object.mongo_update_user_group("unit_test_user_group",
                                                                     {"pruning_allowed": True})
        self.assertTrue(test_reply["pruning_allowed"])

        # check mongo list user permissions work
        mongo_connection_object.mongo_add_user_group(user_group="unit_test_user_group_2",
                                                     group_members=[
                                                         "unit_test_member_1",
                                                         "unit_test_member_2"
                                                     ],
                                                     pruning_allowed=False,
                                                     apps={
                                                         "unit_test_app_3": "rw",
                                                         "unit_test_app_4": "ro"
                                                     },
                                                     device_groups={
                                                         "unit_test_dg_3": "rw",
                                                         "unit_test_dg_4": "ro"
                                                     },
                                                     admin=True)
        test_reply = mongo_connection_object.mongo_list_user_permissions("unit_test_member_1")
        self.assertTrue(test_reply["admin"])
        self.assertTrue(test_reply["pruning_allowed"])
        apps_result = {
            'unit_test_app_1': 'rw',
            'unit_test_app_2': 'ro',
            'unit_test_app_3': 'rw',
            'unit_test_app_4': 'ro'
        }
        device_groups_results = {
            'unit_test_dg_1': 'rw',
            'unit_test_dg_2': 'ro',
            'unit_test_dg_3': 'rw',
            'unit_test_dg_4': 'ro'
        }
        self.assertEqual(test_reply["apps"], apps_result)
        self.assertEqual(test_reply["device_groups"], device_groups_results)

        # check user_group exists works
        test_reply = mongo_connection_object.mongo_check_user_group_exists("unit_test_user_group")
        self.assertTrue(test_reply)

        # check delete user_group works
        test_reply = mongo_connection_object.mongo_delete_user_group("unit_test_user_group")
        self.assertEqual(test_reply.deleted_count, 1)
