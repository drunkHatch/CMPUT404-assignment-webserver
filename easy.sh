#!/bin/bash
# Run the webserver, run the tests and kill the webserver!
python3 server.py &
ID=$!
python3 freetests.py
kill $ID
#pkill -P $$
