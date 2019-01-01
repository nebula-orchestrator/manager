import sys, os
from pymongo import MongoClient, ReturnDocument, ASCENDING


class MongoConnection:

    # connect to db
    def __init__(self, mongo_connection_string, schema_name="nebula"):
        try:
            self.client = MongoClient(mongo_connection_string)
            self.db = self.client[schema_name]
            self.collection = self.db["nebula"]
        except Exception as e:
            print("error connection to mongodb")
            print >> sys.stderr, e
            os._exit(2)

    # create index
    def mongo_create_index(self, index_name):
        try:
            self.collection.create_index([(index_name, ASCENDING)], background=True, name=index_name + "_index",
                                         unique=True, sparse=True)
        except Exception as e:
            print("error creating mongodb index")
            print >> sys.stderr, e
            os._exit(2)

    # get all app data
    def mongo_get_app(self, app_name):
        result = self.collection.find_one({"app_name": app_name})
        if result is None:
            app_exists = False
        else:
            app_exists = True
        return app_exists, result

    # check if app exists
    def mongo_check_app_exists(self, app_name):
        result, ignored = self.mongo_get_app(app_name)
        return result

    # update all app data
    def mongo_update_app(self, app_name, starting_ports, containers_per, env_vars, docker_image, running,
                         networks, volumes, devices, privileged):
        result = self.collection.find_one_and_update({'app_name': app_name},
                                                     {'$inc': {'app_id': 1},
                                                     '$set': {'starting_ports': starting_ports,
                                                              'containers_per': containers_per,
                                                              'env_vars': env_vars,
                                                              'docker_image': docker_image,
                                                              'running': running,
                                                              'networks': networks,
                                                              "volumes": volumes,
                                                              "devices": devices,
                                                              "privileged": privileged
                                                              }
                                                      },
                                                     upsert=True,
                                                     return_document=ReturnDocument.AFTER)
        return result

    # get latest envvars of app
    def mongo_list_app_envvars(self, app_name):
        result = self.collection.find_one({"app_name": app_name})
        return result["env_vars"]

    # update envvars of an app
    def mongo_update_app_envars(self, app_name, env_vars):
        result = self.collection.find_one_and_update({'app_name': app_name},
                                                     {'$inc': {'app_id': 1},
                                                     '$set': {'env_vars': env_vars}},
                                                     return_document=ReturnDocument.AFTER)
        return result

    # update some fields of an app
    def mongo_update_app_fields(self, app_name, update_fields_dict):
        result = self.collection.find_one_and_update({'app_name': app_name},
                                                     {'$inc': {'app_id': 1},
                                                     '$set': update_fields_dict},
                                                     return_document=ReturnDocument.AFTER)
        return result

    # get number of containers per cpu of app
    def mongo_list_app_containers_per(self, app_name):
        result = self.collection.find_one({"app_name": app_name})
        return result["containers_per"]

    # update number of containers per cpu of app
    def mongo_update_app_containers_per(self, app_name, containers_per):
        result = self.collection.find_one_and_update({'app_name': app_name},
                                                     {'$inc': {'app_id': 1},
                                                     '$set': {'containers_per': containers_per}},
                                                     return_document=ReturnDocument.AFTER)
        return result

    # get list of apps
    def mongo_list_apps(self):
        apps_list = []
        for app in self.collection.find({"app_name": {"$exists": "true"}}):
            apps_list.append(app["app_name"])
        return apps_list

    # add app
    def mongo_add_app(self, app_name, starting_ports, containers_per, env_vars, docker_image, running=True,
                      networks="nebula", volumes=None, devices=None, privileged=False):
        # creating the list inside the function to avoid mutable value list in the function default value
        if volumes is None:
            volumes = []
        if devices is None:
            devices = []
        app_doc = {
            "app_id": 1,
            "app_name": app_name,
            "starting_ports": starting_ports,
            "containers_per": containers_per,
            "env_vars": env_vars,
            "docker_image": docker_image,
            "running": running,
            "networks": networks,
            "volumes": volumes,
            "devices": devices,
            "privileged": privileged
        }
        insert_id = self.collection.insert_one(app_doc).inserted_id
        result = self.mongo_get_app(app_name)
        return result

    # remove app
    def mongo_remove_app(self, app_name):
        result = self.collection.delete_one({"app_name": app_name})
        return result

    # get app starting ports
    def mongo_list_app_starting_ports(self, app_name):
        result = self.collection.find_one({"app_name": app_name})
        return result["starting_ports"]

    # update app starting ports
    def mongo_update_app_starting_ports(self, app_name, starting_ports):
        result = self.collection.find_one_and_update({'app_name': app_name},
                                                     {'$inc': {'app_id': 1},
                                                     '$set': {'starting_ports': starting_ports}},
                                                     return_document=ReturnDocument.AFTER)
        return result

    # increase app_id - used to restart the app
    def mongo_increase_app_id(self, app_name):
            result = self.collection.find_one_and_update({'app_name': app_name},
                                                         {'$inc': {'app_id': 1}},
                                                         return_document=ReturnDocument.AFTER)
            return result

    # get app running\stopped state
    def mongo_list_app_running_state(self, app_name):
        result = self.collection.find_one({"app_name": app_name})
        return result["running"]

    # update app running\stopped state
    def mongo_update_app_running_state(self, app_name, running):
        result = self.collection.find_one_and_update({'app_name': app_name},
                                                     {'$inc': {'app_id': 1},
                                                     '$set': {'running': running}},
                                                     return_document=ReturnDocument.AFTER)
        return result
