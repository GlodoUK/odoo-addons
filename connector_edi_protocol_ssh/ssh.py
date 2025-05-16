import paramiko


class SSHClient:
    def __init__(
        self, host, port, username, password=None, key=None, key_passphrase=None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        if key or key_passphrase:
            raise NotImplementedError("key support is not yet implemented!")

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def __enter__(self):
        self.client.close()

        self.client.connect(
            self.host,
            self.port,
            username=self.username,
            password=self.password,
            pkey=None,
            look_for_keys=False,
        )
        return self.client

    def __exit__(self, exc_type, value, traceback):
        self.client.close()
        return False
