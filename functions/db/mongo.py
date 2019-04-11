import sys, os
from pymongo import MongoClient, ReturnDocument, ASCENDING
from bson.objectid import ObjectId


class MongoConnection:

    # connect to db
    def __init__(self, mongo_connection_string, schema_name="nebula", max_pool_size=100):
        try:
            self.client = MongoClient(mongo_connection_string, maxPoolSize=max_pool_size)
            self.db = self.client[schema_name]
            self.collection = {"apps": self.db["nebula_apps"], "device_groups": self.db["nebula_device_groups"],
                               "reports": self.db["nebula_reports"], "users": self.db["nebula_users"],
                               "user_groups": self.db["nebula_user_groups"], "cron_jobs": self.db["nebula_cron_jobs"]}
        except Exception as e:
            print("error connection to mongodb")
            print(e, file=sys.stderr)
            os._exit(2)

    # create indexes
    def mongo_create_index(self, collection_name, collection_index):
        try:
            self.collection[collection_name].create_index([(collection_index, ASCENDING)], background=True,
                                                          name=collection_index + "_index", unique=True, sparse=True)
        except Exception as e:
            print("error creating mongodb indexes")
            print(e, file=sys.stderr)
            os._exit(2)

    # get all app data
    def mongo_get_app(self, app_name):
        result = self.collection["apps"].find_one({"app_name": app_name}, {'_id': False})
        if result is None:
            app_exists = False
        else:
            app_exists = True
        return app_exists, result

    # check if app exists
    def mongo_check_app_exists(self, app_name):
        result, ignored = self.mongo_get_app(app_name)
        return result

    # check if device_group exists
    def mongo_check_device_group_exists(self, device_group):
        result, ignored = self.mongo_get_device_group(device_group)
        return result

    # update all app data
    def mongo_update_app(self, app_name, starting_ports, containers_per, env_vars, docker_image, running,
                         networks, volumes, devices, privileged, rolling_restart):
        result = self.collection["apps"].find_one_and_update({'app_name': app_name},
                                                             {'$inc': {'app_id': 1},
                                                              '$set': {'starting_ports': starting_ports,
                                                                       'containers_per': containers_per,
                                                                       'env_vars': env_vars,
                                                                       'docker_image': docker_image,
                                                                       'running': running,
                                                                       'networks': networks,
                                                                       "volumes": volumes,
                                                                       "devices": devices,
                                                                       "privileged": privileged,
                                                                       "rolling_restart": rolling_restart
                                                                       }
                                                              },
                                                             upsert=True,
                                                             return_document=ReturnDocument.AFTER)
        return result

    # get latest envvars of app
    def mongo_list_app_envvars(self, app_name):
        result = self.collection["apps"].find_one({"app_name": app_name}, {'_id': False})
        return result["env_vars"]

    # update envvars of an app
    def mongo_update_app_envars(self, app_name, env_vars):
        result = self.collection["apps"].find_one_and_update({'app_name': app_name},
                                                             {'$inc': {'app_id': 1},
                                                              '$set': {'env_vars': env_vars}},
                                                             return_document=ReturnDocument.AFTER)
        return result

    # update some fields of an app
    def mongo_update_app_fields(self, app_name, update_fields_dict):
        result = self.collection["apps"].find_one_and_update({'app_name': app_name},
                                                             {'$inc': {'app_id': 1},
                                                              '$set': update_fields_dict},
                                                             return_document=ReturnDocument.AFTER)
        return result

    # get number of containers per cpu of app
    def mongo_list_app_containers_per(self, app_name):
        result = self.collection["apps"].find_one({"app_name": app_name}, {'_id': False})
        return result["containers_per"]

    # update number of containers per cpu of app
    def mongo_update_app_containers_per(self, app_name, containers_per):
        result = self.collection["apps"].find_one_and_update({'app_name': app_name},
                                                             {'$inc': {'app_id': 1},
                                                              '$set': {'containers_per': containers_per}},
                                                             return_document=ReturnDocument.AFTER)
        return result

    # get list of apps
    def mongo_list_apps(self):
        apps_list = []
        for app in self.collection["apps"].find({"app_name": {"$exists": "true"}}, {'_id': False}):
            apps_list.append(app["app_name"])
        return apps_list

    # add app
    def mongo_add_app(self, app_name, starting_ports, containers_per, env_vars, docker_image, running=True,
                      networks="nebula", volumes=None, devices=None, privileged=False, rolling_restart=False):
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
            "privileged": privileged,
            "rolling_restart": rolling_restart
        }
        insert_id = self.collection["apps"].insert_one(app_doc).inserted_id
        ignored_app_existence_status, result = self.mongo_get_app(app_name)
        return result

    # remove app
    def mongo_remove_app(self, app_name):
        result = self.collection["apps"].delete_one({"app_name": app_name})
        return result

    # get app starting ports
    def mongo_list_app_starting_ports(self, app_name):
        result = self.collection["apps"].find_one({"app_name": app_name}, {'_id': False})
        return result["starting_ports"]

    # update app starting ports
    def mongo_update_app_starting_ports(self, app_name, starting_ports):
        result = self.collection["apps"].find_one_and_update({'app_name': app_name},
                                                             {'$inc': {'app_id': 1},
                                                              '$set': {'starting_ports': starting_ports}},
                                                             return_document=ReturnDocument.AFTER)
        return result

    # increase app_id - used to restart the app
    def mongo_increase_app_id(self, app_name):
        result = self.collection["apps"].find_one_and_update({'app_name': app_name},
                                                             {'$inc': {'app_id': 1}},
                                                             return_document=ReturnDocument.AFTER)
        return result

    # get app running\stopped state
    def mongo_list_app_running_state(self, app_name):
        result = self.collection["apps"].find_one({"app_name": app_name}, {'_id': False})
        return result["running"]

    # update app running\stopped state
    def mongo_update_app_running_state(self, app_name, running):
        result = self.collection["apps"].find_one_and_update({'app_name': app_name},
                                                             {'$inc': {'app_id': 1},
                                                              '$set': {'running': running}},
                                                             return_document=ReturnDocument.AFTER)
        return result

    # add device_group
    def mongo_add_device_group(self, device_group, apps, cron_jobs):
        app_doc = {
            "device_group_id": 1,
            "device_group": device_group,
            "apps": apps,
            "prune_id": 1,
            "cron_jobs": cron_jobs
        }
        insert_id = self.collection["device_groups"].insert_one(app_doc).inserted_id
        ignored_device_group_existence_status, result = self.mongo_get_device_group(device_group)
        return result

    # increase prune_id - used to prune unused images of devices that are part of a device group
    def mongo_increase_prune_id(self, device_group):
        result = self.collection["device_groups"].find_one_and_update({'device_group': device_group},
                                                                      {'$inc': {'prune_id': 1}},
                                                                      return_document=ReturnDocument.AFTER)
        return result

    # list device_group
    def mongo_get_device_group(self, device_group):
        result = self.collection["device_groups"].find_one({"device_group": device_group}, {'_id': False})
        if result is None:
            device_group_exists = False
        else:
            device_group_exists = True
        return device_group_exists, result

    # update device_group
    def mongo_update_device_group(self, device_group, update_fields_dict):
        result = self.collection["device_groups"].find_one_and_update({'device_group': device_group},
                                                                      {'$inc': {'device_group_id': 1},
                                                                       '$set': update_fields_dict},
                                                                      return_document=ReturnDocument.AFTER)
        return result

    # delete device_group
    def mongo_remove_device_group(self, device_group):
        result = self.collection["device_groups"].delete_one({"device_group": device_group})
        return result

    # list all device groups
    def mongo_list_device_groups(self):
        device_groups = []
        for device_group in self.collection["device_groups"].find({"device_group": {"$exists": "true"}},
                                                                  {'_id': False}):
            device_groups.append(device_group["device_group"])
        return device_groups

    # get the reports of the user that match it's requested filtering in a paginated fashion starting with the last_id
    # of the previous user request (or none if it's the first request)
    def mango_list_paginated_filtered_reports(self, page_size=10, last_id=None, filters=None):
        if filters is None:
            filters = {}

        # if this isn't the first request start after the last _id of the previous request the user received
        if last_id is not None:
            filters['_id'] = {'$gt': ObjectId(last_id)}

        # if there aren't any filters return a page of all reports
        if filters == {}:
            cursor = self.collection["reports"].find().limit(page_size).sort('_id', ASCENDING)
        # if there are filters return a filtered page of the reports
        else:
            cursor = self.collection["reports"].find(filters).limit(page_size).sort('_id', ASCENDING)

        # Get the data
        data = [x for x in cursor]

        if not data:
            # No documents left
            return None, None

        # Since documents are ordered with _id, last document will have max id.
        last_id = data[-1]['_id']

        # Return data and last_id
        return data, last_id

    # list all users
    def mongo_list_users(self):
        users_list = []
        for user in self.collection["users"].find({"user_name": {"$exists": "true"}}, {'_id': False}):
            users_list.append(user["user_name"])
        return users_list

    # check if user exists
    def mongo_check_user_exists(self, user_name):
        result, ignored = self.mongo_get_user(user_name)
        return result

    # check if user exists
    def mongo_check_user_group_exists(self, user_group):
        result, ignored = self.mongo_get_user_group(user_group)
        return result

    # get user info - the password and\or token are returned hashed for security reasons
    def mongo_get_user(self, user_name):
        result = self.collection["users"].find_one({"user_name": user_name}, {'_id': False})
        if result is None:
            user_exists = False
        else:
            user_exists = True
        return user_exists, result

    # delete a user
    def mongo_delete_user(self, user_name):
        result = self.collection["users"].delete_one({"user_name": user_name})
        return result

    # create a user - make sure to hash the password & token before using this function as it does not hash anything on
    # it's own
    def mongo_add_user(self, user_name, password, token):
        user_doc = {
            "user_name": user_name,
            "password": password,
            "token": token
        }
        insert_id = self.collection["users"].insert_one(user_doc).inserted_id
        ignored_device_group_existence_status, result = self.mongo_get_user(user_name)
        return result

    # update a user - make sure to hash the password & token before using this function as it does not hash anything on
    # it's own
    def mongo_update_user(self, user_name, update_fields_dict):
        result = self.collection["users"].find_one_and_update({'user_name': user_name},
                                                              {'$set': update_fields_dict},
                                                              return_document=ReturnDocument.AFTER)
        return result

    # create a user_group
    def mongo_add_user_group(self, user_group, group_members, pruning_allowed, apps, device_groups, admin, cron_jobs):
        user_group_doc = {
            "user_group": user_group,
            "group_members": group_members,
            "pruning_allowed": pruning_allowed,
            "apps": apps,
            "device_groups": device_groups,
            "admin": admin,
            "cron_jobs": cron_jobs
        }
        insert_id = self.collection["user_groups"].insert_one(user_group_doc).inserted_id
        ignored_device_group_existence_status, result = self.mongo_get_user_group(user_group)
        return result

    # update a user_group
    def mongo_update_user_group(self, user_group, update_fields_dict):
        result = self.collection["user_groups"].find_one_and_update({'user_group': user_group},
                                                                    {'$set': update_fields_dict},
                                                                    return_document=ReturnDocument.AFTER)
        return result

    # delete a user_group
    def mongo_delete_user_group(self, user_group):
        result = self.collection["user_groups"].delete_one({"user_group": user_group})
        return result

    # list all user_groups
    def mongo_list_user_groups(self):
        user_groups_list = []
        for user_group in self.collection["user_groups"].find({"user_group": {"$exists": "true"}}, {'_id': False}):
            user_groups_list.append(user_group["user_group"])
        return user_groups_list

    # get user_group info
    def mongo_get_user_group(self, user_group):
        result = self.collection["user_groups"].find_one({"user_group": user_group}, {'_id': False})
        if result is None:
            user_group_exists = False
        else:
            user_group_exists = True
        return user_group_exists, result

    # return a aggregated view of all groups that a user is a member of
    def mongo_list_user_permissions(self, user_name):
        user_permissions = {"apps": {}, "device_groups": {}, "admin": False, "pruning_allowed": False, "cron_jobs": {}}
        find_query = {"$and": [{"user_group": {"$exists": "true"}}, {"group_members": user_name}]}
        for user_group in self.collection["user_groups"].find(find_query, {'_id': False}):
            if user_group["admin"] is True:
                user_permissions["admin"] = True
            if user_group["pruning_allowed"] is True:
                user_permissions["pruning_allowed"] = True
            user_permissions["apps"] = {**user_permissions["apps"], **user_group["apps"]}
            user_permissions["device_groups"] = {**user_permissions["device_groups"], **user_group["device_groups"]}
            user_permissions["cron_jobs"] = {**user_permissions["cron_jobs"], **user_group["cron_jobs"]}
        return user_permissions

    # add cron_job
    def mongo_add_cron_job(self, cron_job_name, schedule, env_vars, docker_image, running, networks, volumes, devices,
                           privileged):
        cron_job_doc = {
            "cron_job_id": 1,
            "cron_job_name": cron_job_name,
            "schedule": schedule,
            "env_vars": env_vars,
            "docker_image": docker_image,
            'running': running,
            'networks': networks,
            "volumes": volumes,
            "devices": devices,
            "privileged": privileged
        }
        insert_id = self.collection["cron_jobs"].insert_one(cron_job_doc).inserted_id
        ignored_cron_job_existence_status, result = self.mongo_get_cron_job(cron_job_name)
        return result

    # list all cron jobs
    def mongo_list_cron_jobs(self):
        cron_jobs = []
        for cron_job in self.collection["cron_jobs"].find({"cron_job": {"$exists": "true"}},
                                                          {'_id': False}):
            cron_jobs.append(cron_job["cron_job"])
        return cron_jobs

    # get all cron job data
    def mongo_get_cron_job(self, cron_job_name):
        result = self.collection["cron_jobs"].find_one({"cron_job": cron_job_name}, {'_id': False})
        if result is None:
            cron_job_exists = False
        else:
            cron_job_exists = True
        return cron_job_exists, result

    # update some fields of an cron_job
    def mongo_update_cron_job_fields(self, cron_job_name, update_fields_dict):
        result = self.collection["cron_jobs"].find_one_and_update({'cron_job': cron_job_name},
                                                                  {'$inc': {'app_id': 1},
                                                                   '$set': update_fields_dict},
                                                                  return_document=ReturnDocument.AFTER)
        return result

    # delete a cron_job
    def mongo_delete_cron_job(self, cron_job):
        result = self.collection["cron_jobs"].delete_one({"cron_job": cron_job})
        return result

    # check if cron_job exists
    def mongo_check_cron_job_exists(self, cron_job):
        result, ignored = self.mongo_get_cron_job(cron_job)
        return result
