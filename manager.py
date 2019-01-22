import json
from flask import json, Flask, request
from flask_basicauth import BasicAuth
from functions.db.mongo import *
from bson.json_util import dumps
from cachetools import cached, TTLCache
from retrying import retry


API_VERSION = "v2"


# get setting from envvar with failover from config/conf.json file if envvar not set
# using skip rather then None so passing a None type will still pass a None value rather then assuming there should be
# default value thus allowing to have No value set where needed (like in the case of registry user\pass)
def get_conf_setting(setting, settings_json, default_value="skip"):
    try:
        setting_value = os.getenv(setting.upper(), settings_json.get(setting, default_value))
        if setting_value == "true":
            return True
        elif setting_value == "false":
            return False
    except Exception as e:
        print >> sys.stderr, "missing " + setting + " config setting"
        print("missing " + setting + " config setting")
        os._exit(2)
    if setting_value == "skip":
        print >> sys.stderr, "missing " + setting + " config setting"
        print("missing " + setting + " config setting")
        os._exit(2)
    return setting_value


# takes an invalid request & figure out what params are missing on a request and returns a list of those, this function
# should only be called in cases where the "invalid_request" has been tried and found to be missing a param as it fails
# hard on failure like the rest of the code (which in this case also means no missing params)
def find_missing_params(invalid_request):
    try:
        required_params = ["docker_image"]
        missing_params = dict()
        missing_params["missing_parameters"] = list(set(required_params) - set(invalid_request))

    except Exception as e:
        print >> sys.stderr, "unable to find missing params yet the request is returning an error"
        os._exit(2)
    return missing_params


def return_sane_default_if_not_declared(needed_parameter, parameters_dict, sane_default):
    if needed_parameter in parameters_dict:
        returned_value = parameters_dict[needed_parameter]
    else:
        returned_value = sane_default
    return returned_value


# check for edge case of port being outside of the valid port range
def check_ports_valid_range(checked_ports):
    for checked_port in checked_ports:
        if isinstance(checked_port, int):
            if not 1 <= checked_port <= 65535:
                return "{\"starting_ports\": \"invalid port\"}", 400
        elif isinstance(checked_port, dict):
            for host_port, container_port in checked_port.iteritems():
                try:
                    if not 1 <= int(host_port) <= 65535 or not 1 <= int(container_port) <= 65535:
                        return "{\"starting_ports\": \"invalid port\"}", 400
                except ValueError:
                    return "{\"starting_ports\": \"can only be a list containing integers or dicts\"}", 403
        else:
            return "{\"starting_ports\": \"can only be a list containing integers or dicts\"}", 403
    return "all ports checked are in a valid 1-65535 range", 200


# read config file at startup
# load the login params from envvar or auth.json file if envvar is not set, if both are unset will load the default
# value if one exists for the param
if os.path.exists("config/conf.json"):
    print("reading config file")
    auth_file = json.load(open("config/conf.json"))
else:
    print("config file not found - skipping reading it and checking if needed params are given from envvars")
    auth_file = {}

print("reading config variables")
basic_auth_user = get_conf_setting("basic_auth_user", auth_file, None)
basic_auth_password = get_conf_setting("basic_auth_password", auth_file, None)
mongo_url = get_conf_setting("mongo_url", auth_file)
schema_name = get_conf_setting("schema_name", auth_file, "nebula")
basic_auth_enabled = int(get_conf_setting("basic_auth_enabled", auth_file, True))
cache_time = int(get_conf_setting("cache_time", auth_file, "10"))
cache_max_size = int(get_conf_setting("cache_max_size", auth_file, "1024"))
mongo_max_pool_size = int(get_conf_setting("mongo_max_pool_size", auth_file, "25"))

# login to db at startup
mongo_connection = MongoConnection(mongo_url, schema_name, max_pool_size=mongo_max_pool_size)
print("opened MongoDB connection")

# ensure mongo is indexed properly
mongo_connection.mongo_create_indexes("app_name", "device_group")

# get current list of apps at startup
nebula_apps = mongo_connection.mongo_list_apps()
print("got list of all mongo apps")

# open waiting connection
try:
    app = Flask(__name__)
    print("now waiting for connections")

    # basic auth for api
    # based on https://flask-basicauth.readthedocs.io/en/latest/
    app.config['BASIC_AUTH_USERNAME'] = basic_auth_user
    app.config['BASIC_AUTH_PASSWORD'] = basic_auth_password
    app.config['BASIC_AUTH_FORCE'] = basic_auth_enabled
    app.config['BASIC_AUTH_REALM'] = 'nebula'
    basic_auth = BasicAuth(app)
    print("basic auth configured")
except Exception as e:
    print("Flask connection configuration failure - dropping container")
    print >> sys.stderr, e
    os._exit(2)


# api check page - return 200 and a massage just so we know API is reachable
@app.route('/api/' + API_VERSION + '/status', methods=["GET"])
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=200, wait_exponential_max=500)
def check_page():
    return "{\"api_available\": true}", 200


# create a new app
@app.route('/api/' + API_VERSION + '/apps/<app_name>', methods=["POST"])
def create_app(app_name):
    # check app does't exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is True:
        return "{\"app_exists\": true}", 403
    else:
        # check the request is passed with all needed parameters
        try:
            app_json = request.json
        except:
            return json.dumps(find_missing_params({})), 400
        try:
            starting_ports = return_sane_default_if_not_declared("starting_ports", app_json, [])
            containers_per = return_sane_default_if_not_declared("containers_per", app_json, {"server": 1})
            env_vars = return_sane_default_if_not_declared("env_vars", app_json, [])
            docker_image = app_json["docker_image"]
            running = return_sane_default_if_not_declared("running", app_json, True)
            networks = return_sane_default_if_not_declared("networks", app_json, ["nebula", "bridge"])
            volumes = return_sane_default_if_not_declared("volumes", app_json, [])
            devices = return_sane_default_if_not_declared("devices", app_json, [])
            privileged = return_sane_default_if_not_declared("privileged", app_json, False)
            rolling_restart = return_sane_default_if_not_declared("rolling_restart", app_json, False)
        except:
            return json.dumps(find_missing_params(app_json)), 400
        # check edge case of port being outside of possible port ranges
        ports_check_return_message, port_check_return_code = check_ports_valid_range(starting_ports)
        if port_check_return_code >= 300:
            return ports_check_return_message, port_check_return_code
        # update the db
        app_json = mongo_connection.mongo_add_app(app_name, starting_ports, containers_per, env_vars, docker_image,
                                                  running, networks, volumes, devices, privileged, rolling_restart)
        return dumps(app_json), 200


# delete an app
@app.route('/api/' + API_VERSION + '/apps/<app_name>', methods=["DELETE"])
def delete_app(app_name):
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        return "{\"app_exists\": false}", 403
    # remove from db
    mongo_connection.mongo_remove_app(app_name)
    return "{}", 200


# restart an app
@app.route('/api/' + API_VERSION + '/apps/<app_name>/restart', methods=["POST"])
def restart_app(app_name):
    app_exists, app_json = mongo_connection.mongo_get_app(app_name)
    # check app exists first
    if app_exists is False:
        return "{\"app_exists\": \"False\"}", 403
    # check if app already running:
    if app_json["running"] is False:
        return "{\"running_before_restart\": false}", 403
    # post to db
    app_json = mongo_connection.mongo_increase_app_id(app_name)
    return dumps(app_json), 202


# stop an app
@app.route('/api/' + API_VERSION + '/apps/<app_name>/stop', methods=["POST"])
def stop_app(app_name):
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        return "{\"app_exists\": false}", 403
    # post to db
    app_json = mongo_connection.mongo_update_app_running_state(app_name, False)
    return dumps(app_json), 202


# start an app
@app.route('/api/' + API_VERSION + '/apps/<app_name>/start', methods=["POST"])
def start_app(app_name):
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        return "{\"app_exists\": false}", 403
    # post to db
    app_json = mongo_connection.mongo_update_app_running_state(app_name, True)
    return dumps(app_json), 202


# POST update an app - requires all the params to be given in the request body or else will be reset to default values
@app.route('/api/' + API_VERSION + '/apps/<app_name>/update', methods=["POST"])
def update_app(app_name):
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        return "{\"app_exists\": false}", 403
    # check app got all needed parameters
    try:
        app_json = request.json
    except:
        return json.dumps(find_missing_params({})), 400
    try:
        starting_ports = return_sane_default_if_not_declared("starting_ports", app_json, [])
        containers_per = return_sane_default_if_not_declared("containers_per", app_json, {"server": 1})
        env_vars = return_sane_default_if_not_declared("env_vars", app_json, [])
        docker_image = app_json["docker_image"]
        running = return_sane_default_if_not_declared("running", app_json, True)
        networks = return_sane_default_if_not_declared("networks", app_json, ["nebula", "bridge"])
        volumes = return_sane_default_if_not_declared("volumes", app_json, [])
        devices = return_sane_default_if_not_declared("devices", app_json, [])
        privileged = return_sane_default_if_not_declared("privileged", app_json, False)
        rolling_restart = return_sane_default_if_not_declared("rolling_restart", app_json, False)
    except:
        return json.dumps(find_missing_params(app_json)), 400
    # check edge case of port being outside of possible port ranges
    ports_check_return_message, port_check_return_code = check_ports_valid_range(starting_ports)
    if port_check_return_code >= 300:
        return ports_check_return_message, port_check_return_code
    # update db
    app_json = mongo_connection.mongo_update_app(app_name, starting_ports, containers_per, env_vars, docker_image,
                                                 running, networks, volumes, devices, privileged, rolling_restart)
    return dumps(app_json), 202


# PUT update some fields of an app - params not given will be unchanged from their current value
@app.route('/api/' + API_VERSION + '/apps/<app_name>/update', methods=["PUT", "PATCH"])
def update_app_fields(app_name):
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        return "{\"app_exists\": false}", 403
    # check app got update parameters
    try:
        app_json = request.json
        if len(app_json) == 0:
            return "{\"missing_parameters\": true}", 400
    except:
        return "{\"missing_parameters\": true}", 400
    # check edge case of port being outside of possible port ranges in case trying to update port listing
    try:
        starting_ports = request.json["starting_ports"]
        ports_check_return_message, port_check_return_code = check_ports_valid_range(starting_ports)
        if port_check_return_code >= 300:
            return ports_check_return_message, port_check_return_code
    except:
        pass
    # update db
    app_json = mongo_connection.mongo_update_app_fields(app_name, request.json)
    return dumps(app_json), 202


# list apps
@app.route('/api/' + API_VERSION + '/apps', methods=["GET"])
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=200, wait_exponential_max=500)
def list_apps():
    nebula_apps_list = mongo_connection.mongo_list_apps()
    return "{\"apps\": " + dumps(nebula_apps_list) + " }", 200


# get app info
@app.route('/api/' + API_VERSION + '/apps/<app_name>', methods=["GET"])
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=200, wait_exponential_max=500)
def get_app(app_name):
    app_exists, app_json = mongo_connection.mongo_get_app(app_name)
    if app_exists is True:
        return dumps(app_json), 200
    elif app_exists is False:
        return "{\"app_exists\": false}", 403


# get device_group info
@app.route('/api/' + API_VERSION + '/device_groups/<device_group>/info', methods=["GET"])
@cached(cache=TTLCache(maxsize=cache_max_size, ttl=cache_time))
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=200, wait_exponential_max=500)
def get_device_group_info(device_group):
    device_group_exists, device_group_json = mongo_connection.mongo_get_device_group(device_group)
    if device_group_exists is False:
        return "{\"device_group_exists\": false}", 403
    device_group_config = {"apps": [], "apps_list": [], "prune_id": device_group_json["prune_id"],
                           "device_group_id": device_group_json["device_group_id"]}
    for device_app in device_group_json["apps"]:
        app_exists, app_json = mongo_connection.mongo_get_app(device_app)
        if app_exists is True:
            device_group_config["apps"].append(app_json)
            device_group_config["apps_list"].append(app_json["app_name"])
    return dumps(device_group_config), 200


# create device_group
@app.route('/api/' + API_VERSION + '/device_groups/<device_group>', methods=["POST"])
def create_device_group(device_group):
    # check app does't exists first
    device_group_exists = mongo_connection.mongo_check_device_group_exists(device_group)
    if device_group_exists is True:
        return "{\"device_group_exists\": true}", 403
    else:
        # check the request is passed with all needed parameters
        try:
            app_json = request.json
        except:
            return json.dumps({"missing_parameters": ["apps"]}), 400
        try:
            apps = request.json["apps"]
        except:
            return json.dumps({"missing_parameters": ["apps"]}), 400
        # check edge case where apps is not a list
        if type(apps) is not list:
            return "{\"apps_is_list\": false}", 400
        # check edge case where adding an app that does not exist
        for device_app in apps:
            app_exists, app_json = mongo_connection.mongo_get_app(device_app)
            if app_exists is False:
                return "{\"app_exists\": false}", 403
        # update the db
        app_json = mongo_connection.mongo_add_device_group(device_group, apps)
        return dumps(app_json), 200


# list device_group
@app.route('/api/' + API_VERSION + '/device_groups/<device_group>', methods=["GET"])
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=200, wait_exponential_max=500)
def get_device_group(device_group):
    device_group_exists, device_group_json = mongo_connection.mongo_get_device_group(device_group)
    if device_group_exists is True:
        return dumps(device_group_json), 200
    elif device_group_exists is False:
        return "{\"device_group_exists\": false}", 403


# POST update device_group - requires a full list of apps to be given in the request body
@app.route('/api/' + API_VERSION + '/device_groups/<device_group>/update', methods=["POST"])
def update_device_group(device_group):
    # check device_group exists first
    device_group_exists = mongo_connection.mongo_check_device_group_exists(device_group)
    if device_group_exists is False:
        return "{\"app_exists\": false}", 403
    # check app got all needed parameters
    try:
        app_json = request.json
    except:
        return json.dumps({"missing_parameters": ["apps"]}), 400
    try:
        apps = request.json["apps"]
    except:
        return json.dumps({"missing_parameters": ["apps"]}), 400
        # check edge case where apps is not a list
    if type(apps) is not list:
        return "{\"apps_is_list\": false}", 400
    # check edge case where adding an app that does not exist
    for device_app in apps:
        app_exists, app_json = mongo_connection.mongo_get_app(device_app)
        if app_exists is False:
            return "{\"app_exists\": false}", 403
    # update db
    app_json = mongo_connection.mongo_update_device_group(device_group, apps)
    return dumps(app_json), 202


# delete device_group
@app.route('/api/' + API_VERSION + '/device_groups/<device_group>', methods=["DELETE"])
def delete_device_group(device_group):
    # check app exists first
    device_group_exists = mongo_connection.mongo_check_device_group_exists(device_group)
    if device_group_exists is False:
        return "{\"device_group_exists\": false}", 403
    # remove from db
    mongo_connection.mongo_remove_device_group(device_group)
    return "{}", 200


# list device_groups
@app.route('/api/' + API_VERSION + '/device_groups', methods=["GET"])
@retry(stop_max_attempt_number=3, wait_exponential_multiplier=200, wait_exponential_max=500)
def list_device_groups():
    nebula_device_groups_list = mongo_connection.mongo_list_device_groups()
    return "{\"device_groups\": " + dumps(nebula_device_groups_list) + " }", 200


# prune unused images on all devices running said device_group
@app.route('/api/' + API_VERSION + '/device_groups/<device_group>/prune', methods=["POST"])
def prune_device_group_images(device_group):
    # check device_group exists first
    device_group_exists = mongo_connection.mongo_check_device_group_exists(device_group)
    if device_group_exists is False:
        return "{\"app_exists\": false}", 403
    # update db
    app_json = mongo_connection.mongo_increase_prune_id(device_group)
    return dumps(app_json), 202


# prune unused images on all devices
@app.route('/api/' + API_VERSION + '/prune', methods=["POST"])
def prune_images_on_all_device_groups():
    # get a list of all device_groups
    device_groups = mongo_connection.mongo_list_device_groups()
    all_device_groups_prune_id = {"prune_ids": {}}
    # loop over all device groups
    for device_group in device_groups:
        # check device_group exists first
        device_group_exists = mongo_connection.mongo_check_device_group_exists(device_group)
        if device_group_exists is False:
            return "{\"app_exists\": false}", 403
        # update db
        app_json = mongo_connection.mongo_increase_prune_id(device_group)
        all_device_groups_prune_id["prune_ids"][device_group] = app_json["prune_id"]
    return dumps(all_device_groups_prune_id), 202


# set json header - the API is JSON only so the header is set on all requests
@app.after_request
def apply_caching(response):
    response.headers["Content-Type"] = "application/json"
    return response


# used for when running with the 'ENV' envvar set to dev to open a new thread with flask builtin web server
def run_dev(dev_host='0.0.0.0', dev_port=5000, dev_threaded=True):
    try:
        app.run(host=dev_host, port=dev_port, threaded=dev_threaded)
    except Exception as e:
        print("Flask connection failure - dropping container")
        print >> sys.stderr, e
        os._exit(2)


# will usually run in gunicorn but for debugging set the "ENV" envvar to "dev" to run from flask built in web server
# opens in a new thread, DO NOT SET AS 'dev' FOR PRODUCTION USE!!!
if os.getenv("ENV", "prod") == "dev":
    try:
        run_dev()
    except Exception as e:
        print("Flask connection failure - dropping container")
        print >> sys.stderr, e
        os._exit(2)
