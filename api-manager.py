import json, os, sys
from flask import json, Flask, request, Response, render_template, jsonify
from flask_basicauth import BasicAuth
from functions.db_functions import *
from functions.rabbit_functions import *
from bson.json_util import dumps, loads


# get setting from envvar with failover from conf.json file if envvar not set
def get_conf_setting(setting, settings_json):
    try:
        setting_value = os.getenv(setting.upper(), settings_json[setting])
        return setting_value
    except Exception as e:
        print >> sys.stderr, e
        print "missing " + setting + " config setting"
        exit(2)


# login to rabbit function
def rabbit_login(rabbit_login_user, rabbit_login_password, rabbit_login_host, rabbit_login_port, rabbit_login_vhost,
                 rabbit_login_heartbeat):
    rabbit_connection = rabbit_connect(rabbit_login_user, rabbit_login_password, rabbit_login_host, rabbit_login_port,
                                       rabbit_login_vhost, rabbit_login_heartbeat)
    rabbit_connection_channel = rabbit_create_channel(rabbit_connection)
    return rabbit_connection_channel


# read config file at startup
# load the login params from envvar or auth.json file if envvar is not set
print "reading conf.json file"
auth_file = json.load(open("conf.json"))
basic_auth_user = get_conf_setting("basic_auth_user", auth_file)
basic_auth_password = get_conf_setting("basic_auth_password", auth_file)
rabbit_host = get_conf_setting("rabbit_host", auth_file)
rabbit_vhost = get_conf_setting("rabbit_vhost", auth_file)
rabbit_port = int(get_conf_setting("rabbit_port", auth_file))
rabbit_user = get_conf_setting("rabbit_user", auth_file)
rabbit_password = get_conf_setting("rabbit_password", auth_file)
mongo_url = get_conf_setting("mongo_url", auth_file)
schema_name = get_conf_setting("schema_name", auth_file)
rabbit_heartbeat = int(get_conf_setting("rabbit_heartbeat", auth_file))


# login to db at startup
mongo_collection = mongo_connect(mongo_url, schema_name)
print "logged into mongo"

# login to rabbit at startup
rabbit_main_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                   rabbit_heartbeat)
print "logged into rabbit"

# get current list of apps at startup
nebula_apps = mongo_list_apps(mongo_collection)
print "got list of all mongo apps"

# ensure all apps has their rabbitmq exchanges created at startup
for nebula_app in nebula_apps:
    rabbit_create_exchange(rabbit_main_channel, nebula_app)
print "all apps has rabbitmq exchange created (if needed)"

# close rabbit connection
rabbit_close(rabbit_main_channel)

# open waiting connection
app = Flask(__name__)
print "now waiting for connections"

# basic auth for api
# based on https://flask-basicauth.readthedocs.io/en/latest/
app.config['BASIC_AUTH_USERNAME'] = basic_auth_user
app.config['BASIC_AUTH_PASSWORD'] = basic_auth_password
app.config['BASIC_AUTH_FORCE'] = True
app.config['BASIC_AUTH_REALM'] = 'nebula'
basic_auth = BasicAuth(app)
print "basic auth configured"


# api check page - return 200 and a massage just so we know API is reachable
@app.route('/api/status', methods=["GET"])
def check_page():
    return "{\"api_available\": \"True\"}", 200


# create a new app
@app.route('/api/apps/<app_name>', methods=["POST"])
def create_app(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    # check app does't exists first
    app_exists = mongo_check_app_exists(mongo_collection, app_name)
    if app_exists is True:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"True\"}", 403
    else:
        # check the request is passed with all needed parameters
        try:
            app_json = request.json
            starting_ports = request.json["starting_ports"]
            containers_per = request.json["containers_per"]
            env_vars = request.json["env_vars"]
            docker_image = request.json["docker_image"]
            running = request.json["running"]
            networks = request.json["networks"]
            volumes = request.json["volumes"]
            devices = request.json["devices"]
            privileged = request.json["privileged"]
        except:
            rabbit_close(rabbit_channel)
            return "{\"missing_parameters\": \"True\"}", 400
        # check corner case of port being outside of possible port ranges
        for starting_port in starting_ports:
            if isinstance(starting_port, int):
                if not 1 <= starting_port <= 65535:
                    return "{\"starting_ports\": \"invalid port\"}", 400
            elif isinstance(starting_port, dict):
                for host_port, container_port in starting_port.iteritems():
                    if not 1 <= int(host_port) <= 65535 or not 1 <= int(container_port) <= 65535:
                        return "{\"starting_ports\": \"invalid port\"}", 400
            else:
                rabbit_close(rabbit_channel)
                return "{\"starting_ports\": \"can only be a list containing intgers or dicts\"}", 403
        # update the db
        mongo_add_app(mongo_collection, app_name, starting_ports, containers_per, env_vars, docker_image, running,
                      networks, volumes,devices, privileged)
        # create the rabbitmq exchange
        rabbit_create_exchange(rabbit_channel, app_name + "_fanout")
        # post the new app to rabbitmq if app is set to start running
        if running is True:
            rabbit_send(rabbit_channel, app_name + "_fanout", dumps(app_json))
        rabbit_close(rabbit_channel)
        return jsonify(**app_json), 202


# delete an app
@app.route('/api/apps/<app_name>', methods=["DELETE"])
def delete_app(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_check_app_exists(mongo_collection, app_name)
    if app_exists is False:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"False\"}", 403
    # remove from db
    mongo_remove_app(mongo_collection, app_name)
    # post to rabbit to stop all app containers
    rabbit_send(rabbit_channel, app_name + "_fanout", "{}")
    # remove rabbit exchange
    rabbit_delete_exchange(rabbit_channel, app_name + "_fanout")
    rabbit_close(rabbit_channel)
    return "{}", 202


# restart an app
@app.route('/api/apps/<app_name>/restart', methods=["POST"])
def restart_app(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    app_exists, app_json = mongo_get_app(mongo_collection, app_name)
    # check app exists first
    if app_exists is False:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"False\"}", 403
    # check if app already running:
    if app_json["running"] is False:
        rabbit_close(rabbit_channel)
        return "{\"running_before_restart\": \"False\"}", 403
    # post to rabbit to restart app
    app_json["command"] = "restart"
    rabbit_send(rabbit_channel, app_name + "_fanout", dumps(app_json))
    rabbit_close(rabbit_channel)
    return dumps(app_json), 202


# rolling restart an app
@app.route('/api/apps/<app_name>/roll', methods=["POST"])
def roll_app(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    app_exists, app_json = mongo_get_app(mongo_collection, app_name)
    # check app exists first
    if app_exists is False:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"False\"}", 403
    # check if app already running:
    if app_json["running"] is False:
        rabbit_close(rabbit_channel)
        return "{\"running_before_restart\": \"False\"}", 403
    # post to rabbit to restart app
    app_json["command"] = "roll"
    rabbit_send(rabbit_channel, app_name + "_fanout", dumps(app_json))
    rabbit_close(rabbit_channel)
    return dumps(app_json), 202


# stop an app
@app.route('/api/apps/<app_name>/stop', methods=["POST"])
def stop_app(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_check_app_exists(mongo_collection, app_name)
    if app_exists is False:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"False\"}", 403
    # post to db
    app_json = mongo_update_app_running_state(mongo_collection, app_name, False)
    # post to rabbit to stop app
    app_json["command"] = "stop"
    rabbit_send(rabbit_channel, app_name + "_fanout", dumps(app_json))
    rabbit_close(rabbit_channel)
    return dumps(app_json), 202


# start an app
@app.route('/api/apps/<app_name>/start', methods=["POST"])
def start_app(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_check_app_exists(mongo_collection, app_name)
    if app_exists is False:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"False\"}", 403
    # post to db
    app_json = mongo_update_app_running_state(mongo_collection, app_name, True)
    # post to rabbit to stop app
    app_json["command"] = "start"
    rabbit_send(rabbit_channel, app_name + "_fanout", dumps(app_json))
    rabbit_close(rabbit_channel)
    return dumps(app_json), 202


# POST update an app
@app.route('/api/apps/<app_name>/update', methods=["POST"])
def update_app(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_check_app_exists(mongo_collection, app_name)
    if app_exists is False:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"False\"}", 403
    # check app got all needed parameters
    try:
        starting_ports = request.json["starting_ports"]
        containers_per = request.json["containers_per"]
        env_vars = request.json["env_vars"]
        docker_image = request.json["docker_image"]
        running = request.json["running"]
        networks = request.json["networks"]
        volumes = request.json["volumes"]
        devices = request.json["devices"]
        privileged = request.json["privileged"]
    except:
        rabbit_close(rabbit_channel)
        return "{\"missing_parameters\": \"True\"}", 400
    # check corner case of port being outside of possible port ranges
    for starting_port in starting_ports:
        if isinstance(starting_port, int):
            if not 1 <= starting_port <= 65535:
                return "{\"starting_ports\": \"invalid port\"}", 400
        elif isinstance(starting_port, dict):
            for host_port, container_port in starting_port.iteritems():
                if not 1 <= int(host_port) <= 65535 or not 1 <= int(container_port) <= 65535:
                    return "{\"starting_ports\": \"invalid port\"}", 400
        else:
            rabbit_close(rabbit_channel)
            return "{\"starting_ports\": \"can only be a list containing intgers or dicts\"}", 403
    # update db
    app_json = mongo_update_app(mongo_collection, app_name, starting_ports, containers_per, env_vars, docker_image,
                                running, networks, volumes, devices, privileged)
    # post to rabbit to update app
    app_json["command"] = "update"
    rabbit_send(rabbit_channel, app_name + "_fanout", dumps(app_json))
    rabbit_close(rabbit_channel)
    return dumps(app_json), 202


# PUT update some fields of an app
@app.route('/api/apps/<app_name>/update', methods=["PUT", "PATCH"])
def update_app_fields(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_check_app_exists(mongo_collection, app_name)
    if app_exists is False:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"False\"}", 403
    # check app got update parameters
    try:
        app_json = request.json
        if len(app_json) == 0:
            rabbit_close(rabbit_channel)
            return "{\"missing_parameters\": \"True\"}", 400
    except:
        rabbit_close(rabbit_channel)
        return "{\"missing_parameters\": \"True\"}", 400
    # check corner case of port being outside of possible port ranges in case trying to update port listing
    try:
        starting_ports = request.json["starting_ports"]
        for starting_port in starting_ports:
            if isinstance(starting_port, int):
                if not 1 <= starting_port <= 65535:
                    return "{\"starting_ports\": \"invalid port\"}", 400
            elif isinstance(starting_port, dict):
                for host_port, container_port in starting_port.iteritems():
                    if not 1 <= int(host_port) <= 65535 or not 1 <= int(container_port) <= 65535:
                        return "{\"starting_ports\": \"invalid port\"}", 400
            else:
                rabbit_close(rabbit_channel)
                return "{\"starting_ports\": \"can only be a list containing intgers or dicts\"}", 403
    except:
        pass
    # update db
    app_json = mongo_update_app_fields(mongo_collection, app_name, request.json)
    # post to rabbit to update app
    app_json["command"] = "update"
    rabbit_send(rabbit_channel, app_name + "_fanout", dumps(app_json))
    rabbit_close(rabbit_channel)
    return dumps(app_json), 202


# new version released
@app.route('/api/apps/<app_name>/release', methods=["POST"])
def release_app(app_name):
    rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                  rabbit_heartbeat)
    app_exists, app_json = mongo_get_app(mongo_collection, app_name)
    # check app exists first
    if app_exists is False:
        rabbit_close(rabbit_channel)
        return "{\"app_exists\": \"False\"}", 403
    # post to rabbit to restart app
    app_json["command"] = "release"
    rabbit_send(rabbit_channel, app_name + "_fanout", dumps(app_json))
    rabbit_close(rabbit_channel)
    return dumps(app_json), 202


# list apps
@app.route('/api/apps', methods=["GET"])
def list_apps():
    nebula_apps_list = mongo_list_apps(mongo_collection)
    return "{\"apps\": " + dumps(nebula_apps_list) + " }", 200


# get app info
@app.route('/api/apps/<app_name>', methods=["GET"])
def get_app(app_name):
    app_exists, app_json = mongo_get_app(mongo_collection, app_name)
    if app_exists is True:
        return dumps(app_json), 200
    elif app_exists is False:
        return "{\"app_exists\": \"False\"}", 403


# set json header
@app.after_request
def apply_caching(response):
    response.headers["Content-Type"] = "application/json"
    return response


# will usually run in gunicorn but for debugging set ENV envvar to dev to run from flask built in web server
if os.getenv("ENV", "prod") == "dev":
    app.run(host='0.0.0.0', port=5000, threaded=True)
