# for each request recieved take the app name from the request body, get that app config from the backend DB & return
# that app config to the requesting server via rabbitmq direct_reply_to
def on_server_rx_rpc_request(ch, method_frame, properties, body):
    print 'RPC Server got request:', body

    ch.basic_publish('', routing_key=properties.reply_to, body='Polo')

    ch.basic_ack(delivery_tag=method_frame.delivery_tag)

    print 'RPC Server says good bye'
