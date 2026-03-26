from virtual_disk import VirtualDisk
from fat import FatTableManager
from directory import DirectoryManager, DirectoryEntry

ATTR_DIRECTORY = 0x10  # attribute flag for directories

class FileSystem:
    def __init__(self):
        self.disk = VirtualDisk()
        self.disk.initialize("virtual_disk.bin")
        self.fat = FatTableManager(self.disk)
        self.dir = DirectoryManager(self.disk, self.fat)
        self.current_dir = 5  # starting directory cluster
        self.current_path = "/"  # track current path
        print("file system started")

    def list_dir(self, path=None):
        # return contents of current or specified directory
        if path:
            dir_cluster = self._resolve_path(path)
            if dir_cluster is None:
                return None
        else:
            dir_cluster = self.current_dir
        
        files = self.dir.list_directory(dir_cluster)
        print("listing directory,", len(files), "item(s)")
        return files

    def create_file(self, name):
        # create empty file entry
        entry = DirectoryEntry(name=name, attr=0)
        self.dir.add_directory_entry(self.current_dir, entry)
        print("file created ->", name)

    def create_directory(self, name):
        # create directory entry
        new_cluster = self.fat.allocate_chain(1)
        entry = DirectoryEntry(name=name, attr=ATTR_DIRECTORY, first_cluster=new_cluster, file_size=0)
        self.dir.add_directory_entry(self.current_dir, entry)
        print("directory created ->", name)

    def delete_file(self, name):
        # delete file entry + its FAT chain
        if self.dir.remove_directory_entry(self.current_dir, name):
            print("file deleted ->", name)
            return True
        else:
            print("delete failed,", name, "not found")
            return False

    def delete_directory(self, name):
        # check if directory is empty before deleting
        entry, _ = self.dir.find_directory_entry(self.current_dir, name)
        if entry is None:
            print("directory not found:", name)
            return False
        
        if entry.attr != ATTR_DIRECTORY:
            print("not a directory:", name)
            return False
        
        # check if directory is empty
        contents = self.dir.list_directory(entry.first_cluster)
        if contents:
            print("directory not empty:", name)
            return False
        
        # delete directory
        if self.dir.remove_directory_entry(self.current_dir, name):
            print("directory deleted ->", name)
            return True
        return False

    def change_directory(self, path):
        # change current directory
        if path == "..":
            # go to parent directory (simplified - go to root)
            self.current_dir = 5
            self.current_path = "/"
            return True
        
        entry, _ = self.dir.find_directory_entry(self.current_dir, path)
        if entry is None:
            print("directory not found:", path)
            return False
        
        if entry.attr != ATTR_DIRECTORY:
            print("not a directory:", path)
            return False
        
        self.current_dir = entry.first_cluster
        self.current_path = path if self.current_path == "/" else f"{self.current_path}/{path}"
        return True

    def rename_file(self, old_name, new_name):
        # rename file
        entry, pos = self.dir.find_directory_entry(self.current_dir, old_name)
        if entry is None:
            print("file not found:", old_name)
            return False
        
        # create new entry with same data but new name
        new_entry = DirectoryEntry(
            name=new_name,
            attr=entry.attr,
            first_cluster=entry.first_cluster,
            file_size=entry.file_size
        )
        
        # remove old entry (but don't free FAT chain)
        target = self.dir.format_name_to_8_3(old_name)
        clusters = self.dir._clusters_of_dir(self.current_dir)
        for c in clusters:
            data = bytearray(self.disk.read_cluster(c))
            for i in range(0, len(data), 32):
                entry_data = data[i:i + 32]
                if entry_data[0] == 0x00:
                    continue
                raw_name = entry_data[0:11]
                if raw_name.upper() == target.upper():
                    data[i:i + 32] = b'\x00' * 32
                    self.disk.write_cluster(c, bytes(data))
                    break
        
        # add new entry
        self.dir.add_directory_entry(self.current_dir, new_entry)
        print(f"renamed {old_name} to {new_name}")
        return True

    def copy_file(self, source, destination=None):
        # copy file within virtual disk
        data = self.read_file(source)
        if data is None:
            return False
        
        if destination is None:
            destination = source + "_copy"
        
        # check if destination is a directory
        dest_entry, _ = self.dir.find_directory_entry(self.current_dir, destination)
        if dest_entry and dest_entry.attr == ATTR_DIRECTORY:
            # copy to directory with same name
            destination = source
            old_dir = self.current_dir
            self.current_dir = dest_entry.first_cluster
            self.create_file(destination)
            self.write_file(destination, data)
            self.current_dir = old_dir
        else:
            # copy to new file
            self.create_file(destination)
            self.write_file(destination, data)
        
        print(f"copied {source} to {destination}")
        return True

    def write_file(self, name, data: bytes):
        # locate file entry
        entry, pos = self.dir.find_directory_entry(self.current_dir, name)
        if entry is None:
            print("write failed,", name, "not found")
            return

        # clear old data if file already has clusters
        if entry.first_cluster != 0:
            self.fat.free_chain(entry.first_cluster)

        # allocate enough clusters for new data
        clusters = self.fat.allocate_chain(
            (len(data) // self.disk.CLUSTER_SIZE) + 1
        )
        entry.first_cluster = clusters
        entry.file_size = len(data)

        # write data across FAT chain
        i = 0
        c = clusters
        while c != -1:
            chunk = data[i:i + self.disk.CLUSTER_SIZE]
            padded = chunk.ljust(self.disk.CLUSTER_SIZE, b'\x00')
            self.disk.write_cluster(c, padded)
            i += self.disk.CLUSTER_SIZE
            c = self.fat.get_fat_entry(c)

        # update directory entry with new info
        self.dir.remove_directory_entry(self.current_dir, name)
        self.dir.add_directory_entry(self.current_dir, entry)

        print("data written to", name, "-", entry.file_size, "bytes")

    def read_file(self, name):
        # load file entry
        entry, _ = self.dir.find_directory_entry(self.current_dir, name)
        if entry is None:
            print("read failed,", name, "not found")
            return None

        if entry.attr == ATTR_DIRECTORY:
            print("cannot read directory:", name)
            return None

        # read data following FAT chain
        data = b''
        c = entry.first_cluster
        while c != -1:
            data += self.disk.read_cluster(c)
            c = self.fat.get_fat_entry(c)

        print("read", entry.file_size, "bytes from", name)
        return data[:entry.file_size]

    def _resolve_path(self, path):
        # resolve path to cluster number (simplified implementation)
        if path == "/" or path == "":
            return 5
        
        entry, _ = self.dir.find_directory_entry(self.current_dir, path)
        if entry and entry.attr == ATTR_DIRECTORY:
            return entry.first_cluster
        
        return None
