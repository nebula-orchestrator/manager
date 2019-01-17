#!/usr/bin/env bash

# run the following to start the API, MongoDB
sudo docker-compose -f test/travis_ci_scripts/docker-compose.yml pull
sudo docker-compose -f test/travis_ci_scripts/docker-compose.yml up -d
