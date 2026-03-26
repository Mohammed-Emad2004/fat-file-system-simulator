import os
import shutil
from filesystem import FileSystem


class Shell:
    def __init__(self):
        self.fs = FileSystem()
        print("Shell started. Type 'help' for available commands.")

    def run(self):
        while True:
            try:
                cmd_input = input(f"{self.fs.current_path}>> ").strip()
                cmd = cmd_input.split()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting shell...")
                break

            if not cmd:
                continue

            command = cmd[0].lower()

            # 1. CLS - Clear screen
            if command == "cls":
                if len(cmd) > 1:
                    print("Error: cls command does not accept arguments")
                else:
                    os.system('cls' if os.name == 'nt' else 'clear')

            # 2. DIR - List directory
            elif command == "dir" or command == "ls":
                if len(cmd) == 1:
                    files = self.fs.list_dir()
                    if not files:
                        print("Directory is empty.")
                    else:
                        print(f"\nDirectory of {self.fs.current_path}\n")
                        for e in files:
                            file_type = "<DIR>" if e.attr == 0x10 else ""
                            print(f"{e.name:20} {file_type:10} {e.file_size:>10} bytes")
                else:
                    for arg in cmd[1:]:
                        files = self.fs.list_dir(arg)
                        if files is None:
                            print(f"Directory not found: {arg}")
                        elif not files:
                            print(f"Directory is empty: {arg}")
                        else:
                            print(f"\nDirectory of {arg}\n")
                            for e in files:
                                file_type = "<DIR>" if e.attr == 0x10 else ""
                                print(f"{e.name:20} {file_type:10} {e.file_size:>10} bytes")

            # 3. QUIT - Exit shell
            elif command == "quit" or command == "exit":
                print("Goodbye!")
                break

            # 4. HELP - Show help
            elif command == "help":
                if len(cmd) == 1:
                    self._show_help()
                else:
                    self._show_command_help(cmd[1].lower())

            # 5. TYPE - Display file contents
            elif command == "type" or command == "cat":
                if len(cmd) < 2:
                    print("Usage: type [file]+")
                else:
                    for filename in cmd[1:]:
                        print(f"\n=== {filename} ===")
                        content = self.fs.read_file(filename)
                        if content:
                            print(content.decode(errors="ignore"))
                        print()

            # 6. RENAME - Rename file
            elif command == "rename" or command == "ren":
                if len(cmd) != 3:
                    print("Usage: rename [fileName] [newFileName]")
                else:
                    self.fs.rename_file(cmd[1], cmd[2])

            # 7. DEL - Delete files/directories
            elif command == "del" or command == "delete":
                if len(cmd) < 2:
                    print("Usage: del [dirFile]+")
                else:
                    for item in cmd[1:]:
                        confirm = input(f"Delete {item}? (y/n): ").lower()
                        if confirm == 'y':
                            entry, _ = self.fs.dir.find_directory_entry(self.fs.current_dir, item)
                            if entry and entry.attr == 0x10:
                                self.fs.delete_directory(item)
                            else:
                                self.fs.delete_file(item)
                        else:
                            print(f"Cancelled deletion of {item}")

            # 8. CD - Change directory
            elif command == "cd":
                if len(cmd) == 1:
                    print(f"Current directory: {self.fs.current_path}")
                else:
                    if not self.fs.change_directory(cmd[1]):
                        print(f"Error: Directory not found: {cmd[1]}")

            # 9. RD - Remove directory
            elif command == "rd" or command == "rmdir":
                if len(cmd) < 2:
                    print("Usage: rd [directory]+")
                else:
                    for directory in cmd[1:]:
                        confirm = input(f"Remove directory {directory}? (y/n): ").lower()
                        if confirm == 'y':
                            self.fs.delete_directory(directory)
                        else:
                            print(f"Cancelled removal of {directory}")

            # 10. MD - Make directory
            elif command == "md" or command == "mkdir":
                if len(cmd) != 2:
                    print("Usage: md [directory]")
                else:
                    self.fs.create_directory(cmd[1])

            # 11. COPY - Copy files
            elif command == "copy" or command == "cp":
                if len(cmd) < 2:
                    print("Usage: copy [source] or copy [source] [destination]")
                elif len(cmd) == 2:
                    self.fs.copy_file(cmd[1])
                else:
                    self.fs.copy_file(cmd[1], cmd[2])

            # 12. IMPORT - Import from physical disk
            elif command == "import":
                if len(cmd) < 2:
                    print("Usage: import [source] or import [source] [destination]")
                else:
                    source = cmd[1]
                    destination = cmd[2] if len(cmd) > 2 else os.path.basename(source)
                    
                    if not os.path.exists(source):
                        print(f"Error: Source file not found: {source}")
                        continue
                    
                    if os.path.isfile(source):
                        try:
                            with open(source, 'rb') as f:
                                data = f.read()
                            self.fs.create_file(destination)
                            self.fs.write_file(destination, data)
                            print(f"Imported {source} to {destination}")
                        except Exception as e:
                            print(f"Error importing file: {e}")
                    elif os.path.isdir(source):
                        print("Directory import not fully implemented")
                        # Create directory and import all files
                        self.fs.create_directory(destination)
                        old_dir = self.fs.current_dir
                        if self.fs.change_directory(destination):
                            for file in os.listdir(source):
                                file_path = os.path.join(source, file)
                                if os.path.isfile(file_path):
                                    try:
                                        with open(file_path, 'rb') as f:
                                            data = f.read()
                                        self.fs.create_file(file)
                                        self.fs.write_file(file, data)
                                        print(f"Imported {file}")
                                    except Exception as e:
                                        print(f"Error importing {file}: {e}")
                            self.fs.current_dir = old_dir

            # 13. EXPORT - Export to physical disk
            elif command == "export":
                if len(cmd) < 2:
                    print("Usage: export [source] or export [source] [destination]")
                else:
                    source = cmd[1]
                    destination = cmd[2] if len(cmd) > 2 else source
                    
                    data = self.fs.read_file(source)
                    if data is not None:
                        try:
                            with open(destination, 'wb') as f:
                                f.write(data)
                            print(f"Exported {source} to {destination}")
                        except Exception as e:
                            print(f"Error exporting file: {e}")

            elif command == "create":
                if len(cmd) > 1:
                    self.fs.create_file(cmd[1])
                else:
                    print("Usage: create <filename>")

            elif command == "write":
                if len(cmd) > 1:
                    data = input("Enter data: ").encode()
                    self.fs.write_file(cmd[1], data)
                else:
                    print("Usage: write <filename>")

            elif command == "load":
                self.fs.fat.load_fat_from_disk()
                print("FAT table loaded from disk.")

            elif command == "save":
                self.fs.fat.flush_fat_to_disk()
                print("FAT table saved to disk.")

            elif command == "format":
                confirm = input("This will erase all data. Continue? (yes/no): ")
                if confirm.lower() == "yes":
                    self.fs.disk.close_disk()
                    if os.path.exists("virtual_disk.bin"):
                        os.remove("virtual_disk.bin")
                    self.fs = FileSystem()
                    print("Disk formatted successfully.")
                else:
                    print("Format cancelled.")

            elif command == "stat":
                if len(cmd) > 1:
                    entry, _ = self.fs.dir.find_directory_entry(self.fs.current_dir, cmd[1])
                    if entry:
                        print(f"Name: {entry.name}")
                        print(f"Type: {'Directory' if entry.attr == 0x10 else 'File'}")
                        print(f"Size: {entry.file_size} bytes")
                        print(f"First Cluster: {entry.first_cluster}")
                        print(f"Attributes: {entry.attr}")
                    else:
                        print(f"File not found: {cmd[1]}")
                else:
                    print("Usage: stat <filename>")

            elif command == "diskinfo":
                print(f"Cluster Size: {self.fs.disk.CLUSTER_SIZE} bytes")
                print(f"Total Clusters: {self.fs.disk.TOTAL_CLUSTERS}")
                print(f"Total Disk Size: {self.fs.disk.DISK_SIZE} bytes")
                print(f"Free Clusters: {self.fs.disk.get_free_clusters()}")

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands.")

    def _show_help(self):
        print("\nAvailable Commands:")
        print("=" * 60)
        print("cls          - Clear the screen")
        print("dir          - List directory contents")
        print("cd           - Change or display current directory")
        print("md           - Make a new directory")
        print("rd           - Remove an empty directory")
        print("type         - Display file contents")
        print("copy         - Copy files")
        print("rename       - Rename a file")
        print("del          - Delete files or directories")
        print("import       - Import files from physical disk")
        print("export       - Export files to physical disk")
        print("create       - Create a new file")
        print("write        - Write data to a file")
        print("stat         - Show file information")
        print("diskinfo     - Display disk statistics")
        print("load         - Load FAT from disk")
        print("save         - Save FAT to disk")
        print("format       - Format the disk")
        print("help         - Show this help or help for specific command")
        print("quit         - Exit the shell")
        print("\nType 'help [command]' for detailed information")

    def _show_command_help(self, command):
        help_text = {
            "cls": "CLS\n  Clears the screen.\n  Syntax: cls",
            
            "dir": "DIR\n  Displays directory contents.\n  Syntax: dir [directory]*\n  Examples:\n    dir\n    dir mydir\n    dir file.txt",
            
            "cd": "CD\n  Changes current directory or displays current path.\n  Syntax: cd [directory]\n  Examples:\n    cd          (shows current directory)\n    cd mydir    (change to mydir)\n    cd ..       (go to parent)",
            
            "md": "MD\n  Creates a new directory.\n  Syntax: md [directory]\n  Example: md newfolder",
            
            "rd": "RD\n  Removes an empty directory.\n  Syntax: rd [directory]+\n  Example: rd oldfolder",
            
            "type": "TYPE\n  Displays file contents.\n  Syntax: type [file]+\n  Example: type file.txt file2.txt",
            
            "copy": "COPY\n  Copies files.\n  Syntax: copy [source] [destination]\n  Examples:\n    copy file.txt\n    copy file.txt newfile.txt\n    copy file.txt mydir",
            
            "rename": "RENAME\n  Renames a file.\n  Syntax: rename [fileName] [newFileName]\n  Example: rename old.txt new.txt",
            
            "del": "DEL\n  Deletes files or directories.\n  Syntax: del [dirFile]+\n  Example: del file.txt mydir",
            
            "import": "IMPORT\n  Imports files from physical disk.\n  Syntax: import [source] [destination]\n  Examples:\n    import C:\\file.txt\n    import C:\\file.txt newname.txt",
            
            "export": "EXPORT\n  Exports files to physical disk.\n  Syntax: export [source] [destination]\n  Examples:\n    export file.txt\n    export file.txt C:\\output.txt",
            
            "quit": "QUIT\n  Exits the shell.\n  Syntax: quit",
            
            "help": "HELP\n  Shows help information.\n  Syntax: help [command]\n  Example: help copy"
        }
        
        if command in help_text:
            print("\n" + help_text[command])
        else:
            print(f"No help available for: {command}")


if __name__ == '__main__':
    sh = Shell()
    sh.run()
