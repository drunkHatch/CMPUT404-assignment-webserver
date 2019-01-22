#  coding: utf-8
import socketserver
import re
import socket
import datetime
import os
import mimetypes as MT
import sys

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

STATUS_CODE_RESPONSE = {
    0: " 0 Surprise!",
    200: " 200 OK",
    404: " 404 Not Found",
    405: " 405 METHOD NOT ALLOWED"
}

HTTP_REQUEST_METHODS = {
    "GET": 1,
}

END_OF_LINE_RESPONSE = "\r\n"
PROTOCOL_RESPONSE = "HTTP/1.1"
DIRECTORY_TO_SERVE = "www"

# open file error here
GOODFILE = 1
ISADIRECTORY = 2
NOFILE = 3

class MyServerResponse:

    def __init__(self, status=0, expire_time="-1", content_type="default", accept_ranges="none"):
        self.response_header = {
            "status_response": PROTOCOL_RESPONSE + STATUS_CODE_RESPONSE[status],
            "date_response": "Date: " + datetime.datetime.now().strftime('%A, %d %b %Y %X %Z'),
            "expires": "Expires: " + expire_time,
            "content_type": "Content-Type: " + content_type,
            "accept_ranges": "Accept-Ranges: " + accept_ranges
        }

    def send_header(self, conn):
        tmp = self.response_header["status_response"] + END_OF_LINE_RESPONSE
        conn.sendall(tmp.encode("utf-8"))

        tmp = self.response_header["expires"] + END_OF_LINE_RESPONSE
        conn.sendall(tmp.encode("utf-8"))

        if self.response_header["content_type"] != "default":
            tmp = self.response_header["content_type"] + END_OF_LINE_RESPONSE
            conn.sendall(tmp.encode("utf-8"))

        tmp = self.response_header["accept_ranges"] + END_OF_LINE_RESPONSE
        conn.sendall(tmp.encode("utf-8"))

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

        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        full_data = b""
        with self.request as conn:
            new_request = MyServerRequest()
            status_code = 0
            open_file = True
            file = None
            content_type = "void of magic"
            file_name = "none"
            type_of_file = "default"

            # recv all data
            while True:
                data = conn.recv(1024)
                if not data: break
                full_data += data
                if b"\r\n" in data:
                    break
            str_full_data = full_data.decode("utf-8")
            splited_commands = re.split('[\r|\n]+', str_full_data)
            whole_request = splited_commands[0].split(' ')

            if len(whole_request) > 0:

                new_request.method = whole_request[0]
                new_request.url = whole_request[1]

                if not new_request.method_is_valid():
                    status_code = 405
                    open_file = False
                    content_type = "none"

            if open_file:
                open_result, file, file_name = openRequestedFile(new_request.url)

                status_code = checkErrorsOfOpenedFile(status_code, open_result, file, file_name)
                status_code = checkPermissionOfRequestedFile(status_code, open_result, file, file_name)
                if status_code == 200 and file_name != None:
                    type_of_file = MT.guess_type(file_name, False)[0]

                #type_of_file = MT.guess_type(file_name, False)[0]

            new_response = MyServerResponse()
            new_response.set_status_response(status_code)
            if open_result == GOODFILE and type_of_file != None:
                new_response.response_header["content_type"] = "Content-Type: "
                new_response.response_header["content_type"] += type_of_file
            new_response.send_header(conn)
            self.request.sendall(b"\r\n")

            # then open file/directory and send it
            if file:
                self.request.sendfile(file)
                #pass
            #error_handler(conn, status_c)
            self.request.sendall(b"\r\n")
            #conn.sendall(END_OF_LINE_RESPONSE.encode("utf-8"))
        self.request.close()


def openRequestedFile(client_request_url):

    cru = client_request_url

    if cru[-1] == r'/':
        cru += "index.html"

    complete_path = DIRECTORY_TO_SERVE + cru
    try:
        result = open(complete_path, 'rb')
        content_type = cru.split(".")
        return GOODFILE, result, cru
    except IsADirectoryError as e:
        return ISADIRECTORY, None, None
    except FileNotFoundError as n:
        return NOFILE, None, None

def checkErrorsOfOpenedFile(status_code,open_result, file, file_name):
    if open_result == GOODFILE:
        status_code = 200
        type_of_file = MT.guess_type(file_name, False)[0]
    elif open_result == ISADIRECTORY:
        status_code = 301
    elif open_result == NOFILE:
        status_code = 404

    #print("!",os.path.abspath(file.name))
    #print("!",os.getcwd()[1])
    """
    abs_path_of_serving_dir = os.getcwd()
    length_of_serving_dir = len(path_of_serving_dir)
    abs_path_of_request = os.path.abspath(file_name)
    length_of_requested_object = len(abs_path_of_request)

    if length_of_serving_dir > length_of_requested_object:
        status_code = 404
    elif abs_path_of_serving_dir[length_of_serving_dir] != abs_path_of_request[length_of_serving_dir]:
        status_code = 404
    """
    return status_code

def checkPermissionOfRequestedFile(status_code,open_result, file, file_name):

    if file_name == None:
        return status_code

    abs_path_of_serving_dir = os.getcwd()
    length_of_serving_dir = len(abs_path_of_serving_dir)
    abs_path_of_request = os.path.abspath(file.name)
    length_of_requested_object = len(abs_path_of_request)

    if length_of_serving_dir > length_of_requested_object:
        status_code = 404
    elif abs_path_of_serving_dir != abs_path_of_request[:length_of_serving_dir]:
        status_code = 404

    return status_code


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer) # https://stackoverflow.com/questions/15260558/python-tcpserver-address-already-in-use-but-i-close-the-server-and-i-use-allow
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
