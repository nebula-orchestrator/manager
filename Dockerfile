# using ubuntu because it's the smallest i can use that works with mongo ssl
FROM ubuntu:14.04

# copy the codebase
COPY . /www
RUN chmod +x /www/api-manager.py

# install flask and rabbitmq and required packages
RUN apt-get update
RUN apt-get -y install python python-pip
RUN pip install -r /www/requirements.txt

# adding the config
ADD config.py /etc/gunicorn/config.py

#set python to be unbuffered
ENV PYTHONUNBUFFERED=1

#exposing the port
EXPOSE 80

# and running it
CMD gunicorn --config=/etc/gunicorn/config.py  api-manager:app