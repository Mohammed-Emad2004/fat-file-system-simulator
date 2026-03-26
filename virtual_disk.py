import os

class VirtualDisk:
    CLUSTER_SIZE = 1024
    TOTAL_CLUSTERS = 1024
    DISK_SIZE = CLUSTER_SIZE * TOTAL_CLUSTERS

    def __init__(self):
        self.disk = None

    # Initializes the virtual disk file: creates it filled with zeros if it doesn't exist
    # and opens it in read/write binary mode.
    def initialize(self, path, create_if_missing=True):
        if not os.path.exists(path):
            if create_if_missing:
                with open(path, "wb") as f:
                    f.write(b'\x00' * self.DISK_SIZE)
                print("virtual disk created")
            else:
                raise FileNotFoundError("Disk file not found")

        self.disk = open(path, "r+b")
        print("disk initialized")

    # Handles cluster operations:
    # read_cluster reads 1024 bytes from a specific cluster
    def read_cluster(self, cluster_number):
        if cluster_number < 0 or cluster_number >= self.TOTAL_CLUSTERS:
            raise ValueError("Invalid cluster number")

        offset = cluster_number * self.CLUSTER_SIZE
        self.disk.seek(offset)
        data = self.disk.read(self.CLUSTER_SIZE)

        if len(data) < self.CLUSTER_SIZE:
            data += b'\x00' * (self.CLUSTER_SIZE - len(data))

        return data

    # write_cluster writes exactly 1024 bytes after validation.
    def write_cluster(self, cluster_number, data):
        if cluster_number < 0 or cluster_number >= self.TOTAL_CLUSTERS:
            raise ValueError("Invalid cluster number")
        if len(data) != self.CLUSTER_SIZE:
            raise ValueError("Data must be 1024 bytes exactly")

        offset = cluster_number * self.CLUSTER_SIZE
        self.disk.seek(offset)
        self.disk.write(data)
        self.disk.flush()

        print("cluster", cluster_number, "written")

    # Helper utilities: get_disk_size returns file size
    def get_disk_size(self):
        self.disk.seek(0, os.SEEK_END)
        return self.disk.tell()

    # get_free_clusters counts empty clusters
    def get_free_clusters(self):
        free = 0
        self.disk.seek(0)
        for _ in range(self.TOTAL_CLUSTERS):
            data = self.disk.read(self.CLUSTER_SIZE)
            if data == b'\x00' * self.CLUSTER_SIZE:
                free += 1
        return free

    # close_disk safely closes the virtual disk.
    def close_disk(self):
        if self.disk:
            self.disk.close()
            self.disk = None
            print("disk closed")
