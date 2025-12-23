import platform
import threading
from mcrcon import MCRcon as BaseMCRcon, timeout_handler
import signal

class ThreadSafeMCRcon(BaseMCRcon):
    def __init__(self, host, password, port=25575, tlsmode=0, timeout=5):
        self.host = host
        self.password = password
        self.port = port
        self.tlsmode = tlsmode
        self.timeout = timeout

        # Only register SIGALRM on non-Windows main thread
        if platform.system() != "Windows" and threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGALRM, timeout_handler)
