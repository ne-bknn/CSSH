import os
import sys
import time

i = 0

while True:
    if "flag" in os.listdir("/home/student"):
        f = open("/home/student/flag", "w")
        f.write("hello")
        f.close()

    time.sleep(5)
    i += 1
    if i > 100:
        sys.exit(1)
