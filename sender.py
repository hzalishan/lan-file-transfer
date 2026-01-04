import socket
import os
import threading
import time
import struct
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- CONFIG ---
TCP_PORT = 5001
UDP_PORT = 5002
BUFFER_SIZE = 1024 * 1024  # 1 MB Buffer (Best for SSD + Huge Files)

# --- THEME ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")
COLOR_BG = "#1e1e1e"
COLOR_ACCENT = "#1f6aa5"

class SenderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sender (Ultra Fast)")
        self.geometry("400x420")
        self.configure(fg_color=COLOR_BG)
        self.resizable(False, False)
        
        self.path = None
        self.is_folder = False
        self.running = True

        # UI
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(pady=(30, 10))
        self.lbl_status_icon = ctk.CTkLabel(self.status_frame, text="🚀", font=("Arial", 48), text_color=COLOR_ACCENT)
        self.lbl_status_icon.pack()
        self.lbl_status_text = ctk.CTkLabel(self.status_frame, text="Ready", font=("Segoe UI", 16, "bold"), text_color="white")
        self.lbl_status_text.pack()
        
        self.file_card = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.file_card.pack(fill="x", padx=30, pady=10)
        self.lbl_file = ctk.CTkLabel(self.file_card, text="No Item Selected", font=("Segoe UI", 14), text_color="#a0a0a0", wraplength=280)
        self.lbl_file.pack(pady=15)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=25, pady=10)
        
        self.btn_file = ctk.CTkButton(self.btn_frame, text="SELECT FILE", command=self.select_file, height=45, width=160, fg_color=COLOR_ACCENT)
        self.btn_file.pack(side="left", padx=5)
        self.btn_folder = ctk.CTkButton(self.btn_frame, text="SELECT FOLDER", command=self.select_folder, height=45, width=160, fg_color="#333333")
        self.btn_folder.pack(side="right", padx=5)

        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.file_server, daemon=True).start()

    def select_file(self):
        p = filedialog.askopenfilename()
        if p: self.set_selection(p, False)

    def select_folder(self):
        p = filedialog.askdirectory()
        if p: self.set_selection(p, True)

    def set_selection(self, path, is_folder):
        self.path = path
        self.is_folder = is_folder
        self.lbl_file.configure(text=f"{'📂' if is_folder else '📄'} {os.path.basename(path)}")
        self.lbl_status_text.configure(text="Ready to Send")

    def broadcast_presence(self):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind(("", UDP_PORT))
        while self.running:
            try:
                data, addr = udp.recvfrom(1024)
                if data == b"WHO_IS_THERE": udp.sendto(b"SENDER_HERE", addr)
            except: pass

    def file_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", TCP_PORT))
        server.listen(5)
        while self.running:
            try:
                conn, _ = server.accept()
                threading.Thread(target=self.handle_transfer, args=(conn,), daemon=True).start()
            except: pass

    def send_raw_file(self, conn, filepath, rel_path):
        """Helper to send a single file over the existing connection"""
        filesize = os.path.getsize(filepath)
        
        # Header Format: relative_path_len (4 bytes) | relative_path | filesize (8 bytes)
        path_bytes = rel_path.encode('utf-8')
        path_len = len(path_bytes)
        
        # Pack header data using struct
        header = struct.pack(f'!I{path_len}sQ', path_len, path_bytes, filesize)
        conn.sendall(header)
        
        # Send File Data
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data: break
                conn.sendall(data)

    def handle_transfer(self, conn):
        try:
            req = conn.recv(1024).decode()
            if req == "START_TRANSFER" and self.path:
                self.lbl_status_text.configure(text="Sending Data...", text_color=COLOR_ACCENT)
                
                if self.is_folder:
                    # Folder Walk
                    base_folder = os.path.basename(self.path)
                    for root, dirs, files in os.walk(self.path):
                        for file in files:
                            full_path = os.path.join(root, file)
                            # Calculate relative path (e.g., Folder/Subfolder/file.txt)
                            rel_path = os.path.join(base_folder, os.path.relpath(full_path, self.path))
                            self.send_raw_file(conn, full_path, rel_path)
                else:
                    # Single File
                    self.send_raw_file(conn, self.path, os.path.basename(self.path))
                
                # Send "DONE" Signal (Size 0 file indicates end)
                conn.sendall(struct.pack('!I0sQ', 0, b'', 0))
                
                self.lbl_status_text.configure(text="Transfer Complete!")
                
        except Exception as e:
            print(f"Error: {e}")
            self.lbl_status_text.configure(text="Error occurred")
        finally:
            conn.close()

if __name__ == "__main__":
    app = SenderApp()
    app.mainloop()