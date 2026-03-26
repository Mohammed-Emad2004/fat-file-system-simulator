import struct
from virtual_disk import VirtualDisk
from fat import FatTableManager

ENTRY_SIZE = 32
NAME_BYTES = 11
RESERVED_BYTES = ENTRY_SIZE - (NAME_BYTES + 1 + 4 + 4)

class DirectoryEntry:
    # Represents a single directory entry (file metadata record)
    def __init__(self, name='', attr=0, first_cluster=0, file_size=0):
        self.name = name
        self.attr = attr
        self.first_cluster = first_cluster
        self.file_size = file_size

    def to_bytes(self):
        # Convert directory entry to FAT-compatible binary format
        name_b = DirectoryManager.format_name_to_8_3(self.name)
        return struct.pack('<11sBii{}s'.format(RESERVED_BYTES),
            name_b,
            self.attr,
            int(self.first_cluster),
            int(self.file_size),
            b'\x00' * RESERVED_BYTES
        )

    @staticmethod
    def from_bytes(b):
        # Convert raw bytes back to a DirectoryEntry object
        raw_name, attr, first_cluster, file_size, _ = struct.unpack('<11sBii{}s'.format(RESERVED_BYTES), b )
        name = DirectoryManager.parse_8_3_name(raw_name)
        return DirectoryEntry(
            name=name, attr=attr, first_cluster=first_cluster, file_size=file_size
        )


class DirectoryManager:
    # Manages directory reading, writing, searching, and editing
    def __init__(self, disk: VirtualDisk, fat: FatTableManager):
        if not isinstance(disk, VirtualDisk):
            raise TypeError('disk must be VirtualDisk')
        if not isinstance(fat, FatTableManager):
            raise TypeError('fat must be FatTableManager')
        self.disk = disk
        self.fat = fat

    @staticmethod
    def format_name_to_8_3(name: str) -> bytes:
        # Convert normal filename to FAT 8.3 format
        name = name.upper()
        if '.' in name:
            parts = name.split('.')
            base = parts[0][:8]
            ext = parts[1][:3] if len(parts) > 1 else ''
        else:
            base = name[:8]
            ext = ''
        base = base.ljust(8)
        ext = ext.ljust(3)
        return (base + ext).encode('ascii')

    @staticmethod
    def parse_8_3_name(raw: bytes) -> str:
        # Convert FAT 8.3 name back to readable string
        s = raw.decode('ascii', errors='ignore')
        base = s[:8].rstrip()
        ext = s[8:11].rstrip()
        if ext:
            return f'{base}.{ext}'
        return base

    def _clusters_of_dir(self, start_cluster):
        return self.fat.follow_chain(start_cluster)

    def read_directory(self, start_cluster):
        # Read all valid directory entries from directory clusters
        entries = []
        clusters = self._clusters_of_dir(start_cluster)
        for c in clusters:
            data = self.disk.read_cluster(c)
            for i in range(0, len(data), ENTRY_SIZE):
                entry_data = data[i:i + ENTRY_SIZE]
                if entry_data[0] == 0x00:
                    continue
                entries.append(DirectoryEntry.from_bytes(entry_data))

        print(f"[Directory] Read directory: {len(entries)} entry(ies) found.")
        return entries

    def find_directory_entry(self, start_cluster, name):
        # Find a specific file entry inside directory
        target = self.format_name_to_8_3(name)
        clusters = self._clusters_of_dir(start_cluster)
        for c in clusters:
            data = self.disk.read_cluster(c)
            for i in range(0, len(data), ENTRY_SIZE):
                entry_data = data[i:i + ENTRY_SIZE]
                if entry_data[0] == 0x00:
                    continue
                raw_name = entry_data[0:NAME_BYTES]
                if raw_name.upper() == target.upper():
                    return DirectoryEntry.from_bytes(entry_data), (c, i)
        return None, None

    def add_directory_entry(self, start_cluster, entry: DirectoryEntry):
        # Add new file entry to directory, allocate new cluster if needed
        clusters = self._clusters_of_dir(start_cluster)
        if not clusters:
            new = self.fat.allocate_chain(1)
            clusters = [new]

        for c in clusters:
            data = bytearray(self.disk.read_cluster(c))
            for i in range(0, len(data), ENTRY_SIZE):
                slot = data[i:i + ENTRY_SIZE]
                if slot[0] == 0x00:
                    data[i:i + ENTRY_SIZE] = entry.to_bytes()
                    self.disk.write_cluster(c, bytes(data))
                    print(f"[Directory] Entry added: {entry.name}")
                    return c, i

        new_cluster = self.fat.allocate_chain(1)
        last = clusters[-1]
        self.fat.set_fat_entry(last, new_cluster)
        self.fat.set_fat_entry(new_cluster, -1)

        buf = bytearray(self.disk.CLUSTER_SIZE)
        buf[0:ENTRY_SIZE] = entry.to_bytes()
        self.disk.write_cluster(new_cluster, bytes(buf))
        print(f"[Directory] Entry added (new cluster allocated): {entry.name}")
        return new_cluster, 0

    def remove_directory_entry(self, start_cluster, entry_name):
        # Delete directory entry and free its FAT chain
        target = self.format_name_to_8_3(entry_name)
        clusters = self._clusters_of_dir(start_cluster)
        for c in clusters:
            data = bytearray(self.disk.read_cluster(c))
            for i in range(0, len(data), ENTRY_SIZE):
                entry_data = data[i:i + ENTRY_SIZE]
                if entry_data[0] == 0x00:
                    continue
                raw_name = entry_data[0:NAME_BYTES]
                if raw_name.upper() == target.upper():
                    de = DirectoryEntry.from_bytes(entry_data)
                    data[i:i + ENTRY_SIZE] = b'\x00' * ENTRY_SIZE
                    self.disk.write_cluster(c, bytes(data))
                    if de.first_cluster != 0:
                        try:
                            self.fat.free_chain(de.first_cluster)
                        except Exception:
                            pass
                    print(f"[Directory] Entry removed: {entry_name}")
                    return True

        print(f"[Directory] Remove failed: {entry_name} not found.")
        return False

    def list_directory(self, start_cluster):
        return self.read_directory(start_cluster)
