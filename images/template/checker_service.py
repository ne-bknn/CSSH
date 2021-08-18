#!/usr/bin/python3

import os
import sys
import time

def check() -> bool:
    if "test" in os.listdir("/home/student"):
        f = open("/home/student/flag.txt", "w")
        f.write("SPR{first_one_solved}")
        f.close()
        return True

    return False


if __name__ == "__main__":
    while True:
        if check():
            sys.exit()

        time.sleep(10)
    
