class SuperBlock:
    def __init__(self, disk):
        self.disk = disk
        self.cluster_number = 0
        self.create()

    def create(self):
        # Initialize the super block (cluster 0) and fill it with zeros
        data = b'\x00' * 1024
        self.disk.write_cluster(self.cluster_number, data)

        # Write metadata in the next 4 clusters after the super block
        meta = b'\x01'
        for i in range(1, 5):
            self.disk.write_cluster(i, meta * 1024)

        print("[SuperBlock] Super block initialized successfully.")