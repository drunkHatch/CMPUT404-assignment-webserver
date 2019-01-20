#  coding: utf-8
import socketserver
import re
import socket
import datetime
import os

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

#################################################
# 1, eat the request
# 2, check the type of the request
# 3, return status code 405 to unhandled method
   # and return 200 for get
# 4,
#################################################

STATUS_CODE_RESPONSE = {
    0: " 0 Surprise!",
    200: " 200 OK"
}

HTTP_REQUEST_METHODS = {
    "GET": 1,
    "HEAD": 2,
    "POST": 3,
    "PUT": 4,
    "DELETE": 5,
    "CONNECT": 6,
    "OPTIONS": 7,
    "TRACE": 8,
}

END_OF_LINE_RESPONSE = "\r\n"
PROTOCOL_RESPONSE = "HTTP/1.1"
DIRECTORY_TO_SERVE = "www"

# open file error here
GOODFILE = 1
ISADIRECTORY = 2
NOFILE = 3

class MyServerResponse:

    def __init__(self, status=0, expire_time="-1", content_type="", accept_ranges="none"):
        self.response_header = {
            "status_response": PROTOCOL_RESPONSE + STATUS_CODE_RESPONSE[status],
            "date_response": "Date: " + datetime.datetime.now().strftime('%A, %d %b %Y %X %Z'),
            "expires": "Expires: " + expire_time,
            "content_type": "Content-Type: " + content_type,
            "accept_ranges": "Accept-Ranges: " + accept_ranges
        }

    def generate_header(self):
        full_header = ""
        """
        for each in self.response_header:
            if self.response_header[each] == "":
                pass
            elif self.response_header[each] == None:
                pass
            else:
                #full_header += "< " + self.response_header[each] + END_OF_LINE_RESPONSE
                pass
        """
        full_header += "< " + self.response_header["status_response"] + END_OF_LINE_RESPONSE
        full_header += "< " + self.response_header["date_response"] + END_OF_LINE_RESPONSE
        full_header += "< " + self.response_header["expires"] + END_OF_LINE_RESPONSE
        full_header += "< " + self.response_header["content_type"] + END_OF_LINE_RESPONSE
        full_header += "< " + self.response_header["accept_ranges"] + END_OF_LINE_RESPONSE

        return full_header

    def set_status_response(self, status_code):
        self.response_header["status_response"] = PROTOCOL_RESPONSE + STATUS_CODE_RESPONSE[status_code]


class MyServerRequest:

    def __init__(self):
        self.method = None
        self.url = None

    def method_is_valid(self):
        if self.method in HTTP_REQUEST_METHODS:
            return True
        else:
            return False

    # add more implementation here
    def url_is_valid(self):
        return True

class MyWebServer(socketserver.BaseRequestHandler):

    def handle(self):
        #print("Client address: ", self.client_address) # this is the
        #print("Client request class: ", type(self.request)) # self.request is the conn, class socket.socket
        rest_protocol_flag = False
        standard_rest_cmd = "GET / HTTP/1.1"

        full_data = b""
        with self.request as conn:
            new_request = MyServerRequest()

            # recv all data
            while True:
                data = conn.recv(1024)
                if not data: break
                full_data += data
                if b"\r\n" in data:
                    break

            # byte to string with the data we get
            #print(full_data)
            str_full_data = full_data.decode("utf-8")
            splited_commands = re.split('[\r|\n]+', str_full_data)

            # we may need to check the correctness of request
            # so we put request in MyServerRequestHandler
            whole_request = splited_commands[0].split(' ')

            if len(whole_request) > 0:
                new_request.method = whole_request[0]
                new_request.url = whole_request[1]
            else:
                # Error: invalid method might be found here
                pass

            server_host = self.server.server_address
            server_ip = server_host[0]
            server_port = str(server_host[1])
            server_addr = server_ip + ":" +server_port

            if not new_request.url_is_valid():
                # might report some errors here
                pass

            status_code = 0
            content_type = "void of magic"
            path = os.getcwd()

            open_result, file = openRequestedFile(new_request.url, path)

            if open_result != GOODFILE:
                status_code = 0
            else:
                status_code = 200
            # might check some more errors of url here

            # next we figure out what to send
            # assume that url is correct
            new_response = MyServerResponse()
            new_response.set_status_response(status_code)
            new_response.response_header["content_type"] = content_type
            header = new_response.generate_header()
            # get file here
            # finish generation
            # new we send it!
            # send header here
            self.request.sendall(header.encode("utf-8"))
            # then open file/directory and send it
            if file:
                for line in file:
                    self.request.sendall(line)


def openRequestedFile(client_request_url, path_on_server):

    cru = client_request_url

    if cru[-1] == r'/':
        cru += "index.html"

    complete_path = DIRECTORY_TO_SERVE + cru

    try:
        result = open(complete_path, 'rb')
        return GOODFILE, result
    except IsADirectoryError as e:
        return ISADIRECTORY, None
    except FileNotFoundError as n:
        return NOFILE, None



if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
