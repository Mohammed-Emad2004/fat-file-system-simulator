# FAT File System Simulator with CLI Shell

A full simulation of a File Allocation Table (FAT) file system implemented in Python, featuring a custom command-line shell for file and disk management.

## 🧠 Overview
This project simulates how a FAT-based file system works internally, including disk structure, file allocation, and directory management. It also provides an interactive shell that mimics real operating system commands.

## 🚀 Features
- Virtual disk creation and initialization
- Full FAT (File Allocation Table) management
- File and directory operations
- Custom command-line interface (CLI)
- Import/export between virtual and real disk
- Disk formatting and statistics
- Persistent storage (load/save FAT)

## 💻 Supported Commands
cls, dir, cd, md, rd  
type, copy, rename, del  
import, export  
create, write  
stat, diskinfo  
load, save, format  
help, quit  

## ⚙️ System Components
- Shell → Handles user commands  
- File System → Manages files and directories  
- FAT Table → Tracks block allocation  
- Virtual Disk → Simulates storage  

## ▶️ How to Run
```bash
python shell.py

## 📖 Command Reference

### 📁 File & Directory Commands
- `dir` → List directory contents  
- `cd` → Change current directory  
- `md` → Create a new directory  
- `rd` → Remove an empty directory  

### 📄 File Operations
- `create` → Create a new file  
- `write` → Write data to a file  
- `type` → Display file contents  
- `del` → Delete files or directories  
- `rename` → Rename a file  
- `copy` → Copy files  

### 🔄 Import / Export
- `import` → Import file from real disk  
- `export` → Export file to real disk  

### 💽 Disk & FAT Management
- `diskinfo` → Show disk statistics  
- `stat` → Show file information  
- `format` → Format the virtual disk  
- `load` → Load FAT from disk  
- `save` → Save FAT to disk  

### ⚙️ System Commands
- `cls` → Clear the screen  
- `help` → Show available commands  
- `quit` → Exit the shell  
