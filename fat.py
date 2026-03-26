import struct
from virtual_disk import VirtualDisk


class FatTableManager:
    def __init__(self, disk: VirtualDisk):
        self.disk = disk
        self.fat = [0] * 1024  # FAT table stored in memory, each entry represents a cluster link

    def load_fat_from_disk(self):
        data = b''
        for i in range(1, 5):
            data += self.disk.read_cluster(i)
        self.fat = list(struct.unpack('<1024i', data))  # Load FAT structure from disk into memory
        print("fat loaded from disk")

    def flush_fat_to_disk(self):
        data = struct.pack('<1024i', *self.fat)
        for i in range(4):
            start = i * 1024
            end = start + 1024
            cluster_data = data[start:end]
            self.disk.write_cluster(i + 1, cluster_data)  # Save the updated FAT back to disk
        print("fat saved to disk")

    def get_fat_entry(self, index: int):
        return self.fat[index]

    def set_fat_entry(self, index: int, value: int):
        self.fat[index] = value

    def read_all_fat(self):
        return self.fat

    def write_all_fat(self, entries):
        self.fat = entries[:1024]

    def follow_chain(self, start_cluster: int):
        # Follow the FAT linked-list starting from a given cluster and return the full chain
        chain = []
        current = start_cluster
        while current != -1 and current != 0:
            chain.append(current)
            current = self.fat[current]
        return chain

    def allocate_chain(self, count: int):
        # Finds free clusters, links them together, and returns the first allocated cluster
        free_clusters = [i for i, val in enumerate(self.fat[5:], start=5) if val == 0]
        if len(free_clusters) < count:
            raise Exception("not enough free clusters")

        allocated = free_clusters[:count]
        for i in range(count - 1):
            self.fat[allocated[i]] = allocated[i + 1]
        self.fat[allocated[-1]] = -1  # mark last as end of file

        print("allocated", count, "clusters starting from", allocated[0])
        return allocated[0]

    def free_chain(self, start_cluster: int):
        # Frees a whole FAT chain by resetting its entries to 0
        current = start_cluster
        while current != -1 and current != 0:
            next_cluster = self.fat[current]
            self.fat[current] = 0
            current = next_cluster

        print("freed chain starting from", start_cluster)
