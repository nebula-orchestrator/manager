import pika


# connect to rabbit function
class Rabbit:

    def __init__(self, rabbit_user, rabbit_pass, rabbit_host, rabbit_port, rabbit_virtual_host, rabbit_heartbeat):
        credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host, rabbit_port,
                                                                            rabbit_virtual_host, credentials,
                                                                            heartbeat=rabbit_heartbeat))
        self.channel = self.connection.channel()

    # close connection to rabbit function
    def rabbit_close(self):
        self.channel.close()
        self.connection.close()

    # set qos
    def rabbit_qos(self, prefetch_count=1):
        self.channel.basic_qos(prefetch_count=prefetch_count)

    # create exchange
    def rabbit_create_exchange(self, exchange_name):
        self.channel.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=True)

    # delete exchange
    def rabbit_delete_exchange(self, exchange_name):
        self.channel.exchange_delete(exchange=exchange_name)

    # send message
    def rabbit_send(self, exchange_name, rabbit_send_message):
        self.channel.basic_publish(exchange=exchange_name, routing_key='', body=rabbit_send_message)

    # receive message
    def rabbit_receive(self, rabbit_work_function, rabbit_receive_queue):
        self.channel.basic_consume(rabbit_work_function, queue=rabbit_receive_queue)
        self.channel.start_consuming()

    # ack message
    def rabbit_ack(self, rabbit_ack_method):
        self.channel.basic_ack(delivery_tag=rabbit_ack_method.delivery_tag)

    # create queue
    def rabbit_create_queue(self, rabbit_queue_name):
        created_queue = self.channel.queue_declare(queue=rabbit_queue_name, arguments={"x-expires": 300000})
        return created_queue

    # create rpc api queue
    def rabbit_create_rpc_api_queue(self, rabbit_queue_name):
        created_queue = self.channel.queue_declare(queue=rabbit_queue_name, durable=True)
        return created_queue

    # bind queue to exchange
    def rabbit_bind_queue(self, rabbit_bind_queue_name, rabbit_bind_exchange):
        self.channel.queue_bind(exchange=rabbit_bind_exchange, queue=rabbit_bind_queue_name)
