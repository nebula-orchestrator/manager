from pymongo import MongoClient, ReturnDocument


# connect to db
def mongo_connect(mongo_connection_string, schema_name="nebula"):
    try:
        client = MongoClient(mongo_connection_string)
        db = client[schema_name]
        collection = db["nebula"]
    except:
        print "error connection to mongodb"
        exit(2)
    return collection


# get all app data
def mongo_get_app(collection, app_name):
    result = collection.find_one({"app_name": app_name})
    if result is None:
        app_exists = False
    else:
        app_exists = True
    return app_exists, result


# check if app exists
def mongo_check_app_exists(collection, app_name):
    result, ignored = mongo_get_app(collection, app_name)
    return result


# update all app data
def mongo_update_app(collection, app_name, starting_ports, containers_per, env_vars, docker_image, running,
                     network_mode):
    app_doc = {
        "app_name": app_name,
        "starting_ports": starting_ports,
        "containers_per": containers_per,
        "env_vars": env_vars,
        "docker_image": docker_image,
        "running": running,
        "network_mode": network_mode
    }
    result = collection.find_one_and_update({'app_name': app_name},
                                            {'$set': {'starting_ports': starting_ports,
                                                      'containers_per': containers_per,
                                                      'env_vars': env_vars,
                                                      'docker_image': docker_image,
                                                      'running': running,
                                                      'network_mode': network_mode}},
                                            upsert=True,
                                            return_document=ReturnDocument.AFTER)
    return result


# get latest envvars of app
def mongo_list_app_envvars(collection, app_name):
    result = collection.find_one({"app_name": app_name})
    return result["env_vars"]


# update envvars of an app
def mongo_update_app_envars(collection, app_name, env_vars):
    result = collection.find_one_and_update({'app_name': app_name},
                                            {'$set': {'env_vars': env_vars}},
                                            return_document=ReturnDocument.AFTER)
    return result


# update some fields of an app
def mongo_update_app_fields(collection, app_name, update_fields_dict):
    result = collection.find_one_and_update({'app_name': app_name},
                                            {'$set': update_fields_dict},
                                            return_document=ReturnDocument.AFTER)
    return result


# get number of containers per cpu of app
def mongo_list_app_containers_per(collection, app_name):
    result = collection.find_one({"app_name": app_name})
    return result["containers_per"]


# update number of containers per cpu of app
def mongo_update_app_containers_per(collection, app_name, containers_per):
    result = collection.find_one_and_update({'app_name': app_name},
                                            {'$set': {'containers_per': containers_per}},
                                            return_document=ReturnDocument.AFTER)
    return result


# get list of apps
def mongo_list_apps(collection):
    apps_list = []
    for app in collection.find():
        apps_list.append(app["app_name"])
    return apps_list


# add app
def mongo_add_app(collection, app_name, starting_ports, containers_per, env_vars, docker_image, running=True,
                  network_mode="bridge"):
    app_doc = {
        "app_name": app_name,
        "starting_ports": starting_ports,
        "containers_per": containers_per,
        "env_vars": env_vars,
        "docker_image": docker_image,
        "running": running,
        "network_mode": network_mode
    }
    result = collection.insert_one(app_doc).inserted_id
    return result


# remove app
def mongo_remove_app(collection, app_name):
    result = collection.delete_one({"app_name": app_name})
    return result


# get app starting ports
def mongo_list_app_starting_ports(collection, app_name):
    result = collection.find_one({"app_name": app_name})
    return result["starting_ports"]


# update app starting ports
def mongo_update_app_starting_ports(collection, app_name, starting_ports):
    result = collection.find_one_and_update({'app_name': app_name},
                                            {'$set': {'starting_ports': starting_ports}},
                                            return_document=ReturnDocument.AFTER)
    return result


# get app running\stopped state
def mongo_list_app_running_state(collection, app_name):
    result = collection.find_one({"app_name": app_name})
    return result["running"]


# update app running\stopped state
def mongo_update_app_running_state(collection, app_name, running):
    result = collection.find_one_and_update({'app_name': app_name},
                                            {'$set': {'running': running}},
                                            return_document=ReturnDocument.AFTER)
    return result
