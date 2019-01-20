filename = "CMPUT404-assignment-webserver"

try:
    file = open(filename, 'r')
except Exception as e:
    print("some error here: ", e)
