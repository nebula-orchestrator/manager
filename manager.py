import json
from flask import json, Flask, request, jsonify
from flask_basicauth import BasicAuth
from functions.db.mongo import *
from functions.message_queue.rabbit import *
from bson.json_util import dumps
from threading import Thread


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
        required_params = ["starting_ports", "containers_per", "env_vars", "docker_image", "running", "networks",
                           "volumes", "devices", "privileged"]
        missing_params = dict()
        missing_params["missing_parameters"] = list(set(required_params) - set(invalid_request))

    except Exception as e:
        print >> sys.stderr, "unable to find missing params yet the request is returning an error"
        os._exit(2)
    return missing_params


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
                    return "{\"starting_ports\": \"can only be a list containing intgers or dicts\"}", 403
        else:
            return "{\"starting_ports\": \"can only be a list containing intgers or dicts\"}", 403
    return "all ports checked are in a valid 1-65535 range", 202


# static variables
RABBIT_RPC_QUEUE = "rabbit_api_rpc_queue"

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
rabbit_host = get_conf_setting("rabbit_host", auth_file)
rabbit_vhost = get_conf_setting("rabbit_vhost", auth_file, "/")
rabbit_port = int(get_conf_setting("rabbit_port", auth_file, 5672))
rabbit_user = get_conf_setting("rabbit_user", auth_file)
rabbit_password = get_conf_setting("rabbit_password", auth_file)
mongo_url = get_conf_setting("mongo_url", auth_file)
schema_name = get_conf_setting("schema_name", auth_file, "nebula")
rabbit_heartbeat = int(get_conf_setting("rabbit_heartbeat", auth_file, 3600))
basic_auth_enabled = int(get_conf_setting("basic_auth_enabled", auth_file, True))

# login to db at startup
mongo_connection = MongoConnection(mongo_url, schema_name)
print("opened MongoDB connection")

# ensure mongo is indexed properly
mongo_connection.mongo_create_index("app_name")

# login to rabbit at startup
rabbit_main_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
print("logged into RabbitMQ")

# get current list of apps at startup
nebula_apps = mongo_connection.mongo_list_apps()
print("got list of all mongo apps")

# ensure all apps has their rabbitmq exchanges created at startup
for nebula_app in nebula_apps:
    rabbit_main_channel.rabbit_create_exchange(nebula_app + "_fanout")
print("all apps has rabbitmq exchange created (if needed)")

# close rabbit connection
rabbit_main_channel.rabbit_close()

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
@app.route('/api/status', methods=["GET"])
def check_page():
    return "{\"api_available\": \"True\"}", 200


# prune unused images on all devices running said app
@app.route('/api/apps/<app_name>/prune', methods=["POST"])
def prune_images(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    app_exists, app_json = mongo_connection.mongo_get_app(app_name)
    # check app exists first
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # post to rabbit to restart app
    app_json["command"] = "prune"

    # create the RabbitMQ exchange in case it somehow got deleted
    rabbit_channel.rabbit_create_exchange(app_name + "_fanout")

    rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
    rabbit_channel.rabbit_close()
    return dumps(app_json), 202


# create a new app
@app.route('/api/apps/<app_name>', methods=["POST"])
def create_app(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    # check app does't exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is True:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"True\"}", 403
    else:
        # check the request is passed with all needed parameters
        try:
            app_json = request.json
        except:
            return json.dumps(find_missing_params({})), 400
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
            rabbit_channel.rabbit_close()
            return json.dumps(find_missing_params(app_json)), 400
        # check edge case of port being outside of possible port ranges
        ports_check_return_message, port_check_return_code = check_ports_valid_range(starting_ports)
        if port_check_return_code >= 300:
            rabbit_channel.rabbit_close()
            return ports_check_return_message, port_check_return_code
        # update the db
        mongo_connection.mongo_add_app(app_name, starting_ports, containers_per, env_vars, docker_image, running,
                                       networks, volumes, devices, privileged)
        # create the rabbitmq exchange
        rabbit_channel.rabbit_create_exchange(app_name + "_fanout")
        # post the new app to rabbitmq if app is set to start running
        if running is True:
            rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
            rabbit_channel.rabbit_close()
        return jsonify(**app_json), 202


# delete an app
@app.route('/api/apps/<app_name>', methods=["DELETE"])
def delete_app(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # remove from db
    mongo_connection.mongo_remove_app(app_name)
    # post to rabbit to stop all app containers
    rabbit_channel.rabbit_send(app_name + "_fanout", "{}")
    # remove rabbit exchange
    rabbit_channel.rabbit_delete_exchange(app_name + "_fanout")
    rabbit_channel.rabbit_close()
    return "{}", 202


# restart an app
@app.route('/api/apps/<app_name>/restart', methods=["POST"])
def restart_app(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    app_exists, app_json = mongo_connection.mongo_get_app(app_name)
    # check app exists first
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # check if app already running:
    if app_json["running"] is False:
        rabbit_channel.rabbit_close()
        return "{\"running_before_restart\": \"False\"}", 403
    # post to rabbit to restart app
    app_json["command"] = "restart"

    # create the RabbitMQ exchange in case it somehow got deleted
    rabbit_channel.rabbit_create_exchange(app_name + "_fanout")

    rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
    rabbit_channel.rabbit_close()
    return dumps(app_json), 202


# rolling restart an app
@app.route('/api/apps/<app_name>/roll', methods=["POST"])
def roll_app(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    app_exists, app_json = mongo_connection.mongo_get_app(app_name)
    # check app exists first
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # check if app already running:
    if app_json["running"] is False:
        rabbit_channel.rabbit_close()
        return "{\"running_before_restart\": \"False\"}", 403
    # post to rabbit to restart app
    app_json["command"] = "roll"

    # create the RabbitMQ exchange in case it somehow got deleted
    rabbit_channel.rabbit_create_exchange(app_name + "_fanout")

    rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
    rabbit_channel.rabbit_close()
    return dumps(app_json), 202


# stop an app
@app.route('/api/apps/<app_name>/stop', methods=["POST"])
def stop_app(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # post to db
    app_json = mongo_connection.mongo_update_app_running_state(app_name, False)
    # post to rabbit to stop app
    app_json["command"] = "stop"

    # create the RabbitMQ exchange in case it somehow got deleted
    rabbit_channel.rabbit_create_exchange(app_name + "_fanout")

    rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
    rabbit_channel.rabbit_close()
    return dumps(app_json), 202


# start an app
@app.route('/api/apps/<app_name>/start', methods=["POST"])
def start_app(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # post to db
    app_json = mongo_connection.mongo_update_app_running_state(app_name, True)
    # post to rabbit to stop app
    app_json["command"] = "start"

    # create the RabbitMQ exchange in case it somehow got deleted
    rabbit_channel.rabbit_create_exchange(app_name + "_fanout")

    rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
    rabbit_channel.rabbit_close()
    return dumps(app_json), 202


# POST update an app - requires all the params to be given in the request body
@app.route('/api/apps/<app_name>/update', methods=["POST"])
def update_app(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # check app got all needed parameters
    try:
        app_json = request.json
    except:
        return json.dumps(find_missing_params({})), 400
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
        rabbit_channel.rabbit_close()
        return json.dumps(find_missing_params(app_json)), 400
    # check edge case of port being outside of possible port ranges
    ports_check_return_message, port_check_return_code = check_ports_valid_range(starting_ports)
    if port_check_return_code >= 300:
        rabbit_channel.rabbit_close()
        return ports_check_return_message, port_check_return_code
    # update db
    app_json = mongo_connection.mongo_update_app(app_name, starting_ports, containers_per, env_vars, docker_image,
                                                 running, networks, volumes, devices, privileged)
    # post to rabbit to update app
    app_json["command"] = "update"

    # create the RabbitMQ exchange in case it somehow got deleted
    rabbit_channel.rabbit_create_exchange(app_name + "_fanout")

    rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
    rabbit_channel.rabbit_close()
    return dumps(app_json), 202


# PUT update some fields of an app - params not given will be unchanged from their current value
@app.route('/api/apps/<app_name>/update', methods=["PUT", "PATCH"])
def update_app_fields(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    # check app exists first
    app_exists = mongo_connection.mongo_check_app_exists(app_name)
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # check app got update parameters
    try:
        app_json = request.json
        if len(app_json) == 0:
            rabbit_channel.rabbit_close()
            return "{\"missing_parameters\": \"True\"}", 400
    except:
        rabbit_channel.rabbit_close()
        return "{\"missing_parameters\": \"True\"}", 400
    # check edge case of port being outside of possible port ranges in case trying to update port listing
    try:
        starting_ports = request.json["starting_ports"]
        ports_check_return_message, port_check_return_code = check_ports_valid_range(starting_ports)
        if port_check_return_code >= 300:
            rabbit_channel.rabbit_close()
            return ports_check_return_message, port_check_return_code
    except:
        pass
    # update db
    app_json = mongo_connection.mongo_update_app_fields(app_name, request.json)
    # post to rabbit to update app
    app_json["command"] = "update"

    # create the RabbitMQ exchange in case it somehow got deleted
    rabbit_channel.rabbit_create_exchange(app_name + "_fanout")

    rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
    rabbit_channel.rabbit_close()
    return dumps(app_json), 202


# new version released, does the same as restart & kept as legacy.
@app.route('/api/apps/<app_name>/release', methods=["POST"])
def release_app(app_name):
    rabbit_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost, rabbit_heartbeat)
    app_exists, app_json = mongo_connection.mongo_get_app(app_name)
    # check app exists first
    if app_exists is False:
        rabbit_channel.rabbit_close()
        return "{\"app_exists\": \"False\"}", 403
    # post to rabbit to restart app
    app_json["command"] = "release"

    # create the RabbitMQ exchange in case it somehow got deleted
    rabbit_channel.rabbit_create_exchange(app_name + "_fanout")

    rabbit_channel.rabbit_send(app_name + "_fanout", dumps(app_json))
    rabbit_channel.rabbit_close()
    return dumps(app_json), 202


# list apps
@app.route('/api/apps', methods=["GET"])
def list_apps():
    nebula_apps_list = mongo_connection.mongo_list_apps()
    return "{\"apps\": " + dumps(nebula_apps_list) + " }", 200


# get app info
@app.route('/api/apps/<app_name>', methods=["GET"])
def get_app(app_name):
    app_exists, app_json = mongo_connection.mongo_get_app(app_name)
    if app_exists is True:
        return dumps(app_json), 200
    elif app_exists is False:
        return "{\"app_exists\": \"False\"}", 403


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


# for each request received take the app name from the request body, get that app config from the backend DB & return
# that app config to the requesting server via rabbitmq direct_reply_to
def on_server_rx_rpc_request(ch, method_frame, properties, body):
    try:
        print 'RPC Server got request for initial config of app:', body
        # get app configuration from backend DB
        rpc_app_info = get_app(body)[0]
        # return app configuration to requesting worker
        ch.basic_publish('', routing_key=properties.reply_to, body=rpc_app_info)
        ch.basic_ack(delivery_tag=method_frame.delivery_tag)
    except Exception as e:
        print("rabbit RPC connection failure - dropping container")
        print >> sys.stderr, e
        os._exit(2)


# creates an api rabbitmq work queue and starts processing messages from it 1 at a time, each message gets a name of a
# nebula app which it then quries the backend DB for the app config and then returns it to the requesting worker via
# direct_reply_to
def bootstrap_workers_via_rabbitmq():
    try:
        # login to rabbit at startup
        rabbit_rpc_channel = Rabbit(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                    rabbit_heartbeat)
        rabbit_rpc_channel.rabbit_qos(prefetch_count=1)
        rabbit_rpc_channel.rabbit_create_rpc_api_queue(RABBIT_RPC_QUEUE)
        # start processing rpc calls via rabbitmq
        print("logged into rabbit - RPC connection")
        rabbit_rpc_channel.rabbit_receive(on_server_rx_rpc_request, RABBIT_RPC_QUEUE)
    except Exception as e:
        print("rabbit RPC connection failure - dropping container")
        print >> sys.stderr, e
        os._exit(2)


# opens a thread that will act as an RPC via RabbitMQ to get the app data needed for workers at start
try:
    Thread(target=bootstrap_workers_via_rabbitmq).start()
except Exception as e:
    print("rabbit RPC connection failure - dropping container")
    print >> sys.stderr, e
    os._exit(2)

# will usually run in gunicorn but for debugging set the "ENV" envvar to "dev" to run from flask built in web server
# opens in a new thread, DO NOT SET AS 'dev' FOR PRODUCTION USE!!!
if os.getenv("ENV", "prod") == "dev":
    try:
        Thread(target=run_dev).start()
    except Exception as e:
        print("Flask connection failure - dropping container")
        print >> sys.stderr, e
        os._exit(2)
