# it's offical so i'm using it + alpine so damn small
FROM python:2.7.15-alpine3.8

# copy the codebase
COPY . /www
RUN chmod +x /www/api-manager.py

# install required packages
RUN pip install -r /www/requirements.txt

# adding the gunicorn config
ADD config.py /etc/gunicorn/config.py

#set python to be unbuffered
ENV PYTHONUNBUFFERED=1

#exposing the port
EXPOSE 80

# and running it
CMD ["gunicorn" ,"--config", "/etc/gunicorn/config.py", "api-manager:app"]