import socket
import os
import threading
import time
import struct
import customtkinter as ctk
from tkinter import messagebox

# --- CONFIG ---
TCP_PORT = 5001
UDP_PORT = 5002
BUFFER_SIZE = 1024 * 1024 # 1 MB Buffer
COLOR_BG = "#1e1e1e"
COLOR_ACCENT = "#1f6aa5"

class ReceiverApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Receiver (Ultra Fast)")
        self.geometry("400x480")
        self.configure(fg_color=COLOR_BG)
        self.resizable(False, False)
        
        self.sender_ip = None
        self.running = True
        self.total_recvd = 0
        self.last_bytes = 0
        self.transferring = False

        # UI
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(pady=(40, 20))
        self.lbl_icon = ctk.CTkLabel(self.status_frame, text="🚀", font=("Arial", 50), text_color="#555555")
        self.lbl_icon.pack()
        self.lbl_msg = ctk.CTkLabel(self.status_frame, text="Scanning...", font=("Segoe UI", 16, "bold"), text_color="white")
        self.lbl_msg.pack()

        self.lbl_speed = ctk.CTkLabel(self, text="", text_color=COLOR_ACCENT, font=("Segoe UI", 14, "bold"))
        self.lbl_speed.pack(pady=10)
        
        self.lbl_current_file = ctk.CTkLabel(self, text="", text_color="gray", font=("Segoe UI", 10))
        self.lbl_current_file.pack()

        self.btn_action = ctk.CTkButton(self, text="WAITING...", state="disabled", height=50, fg_color="#333333")
        self.btn_action.pack(side="bottom", pady=(10, 30), padx=30, fill="x")
        
        self.btn_open = ctk.CTkButton(self, text="📂 Open Folder", command=lambda: os.startfile(os.getcwd()), height=30, fg_color="transparent")

        self.reset_scan()

    def reset_scan(self):
        self.sender_ip = None
        self.transferring = False
        self.lbl_icon.configure(text="⚡", text_color="#555555")
        self.lbl_msg.configure(text="Scanning for Sender...")
        self.lbl_speed.configure(text="")
        self.lbl_current_file.configure(text="")
        self.btn_open.pack_forget()
        self.btn_action.configure(state="disabled", text="SEARCHING...", command=None)
        threading.Thread(target=self.scan_network, daemon=True).start()

    def scan_network(self):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp.settimeout(2)
        while self.sender_ip is None and self.running:
            try:
                udp.sendto(b"WHO_IS_THERE", ('<broadcast>', UDP_PORT))
                data, addr = udp.recvfrom(1024)
                if data == b"SENDER_HERE":
                    self.sender_ip = addr[0]
                    self.found_sender()
            except: time.sleep(1)
        udp.close()

    def found_sender(self):
        self.lbl_icon.configure(text="✓", text_color=COLOR_ACCENT)
        self.lbl_msg.configure(text="Sender Found!")
        self.btn_action.configure(state="normal", text="START RECEIVE", fg_color=COLOR_ACCENT, command=self.start_download)

    def start_download(self):
        self.btn_action.configure(state="disabled", text="RECEIVING...", fg_color="#333333")
        self.transferring = True
        self.total_recvd = 0
        self.last_bytes = 0
        threading.Thread(target=self.download_logic, daemon=True).start()
        threading.Thread(target=self.speed_monitor, daemon=True).start()

    def speed_monitor(self):
        while self.transferring:
            time.sleep(1)
            curr = self.total_recvd
            diff = curr - self.last_bytes
            self.last_bytes = curr
            spd = diff / (1024*1024)
            self.lbl_speed.configure(text=f"{spd:.1f} MB/s")

    def recvall(self, sock, count):
        buf = b''
        while count:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def download_logic(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.sender_ip, TCP_PORT))
            s.send(b"START_TRANSFER")

            while True:
                # 1. Read Path Length (4 bytes int)
                raw_len = self.recvall(s, 4)
                if not raw_len: break
                path_len = struct.unpack('!I', raw_len)[0]

                # 2. Check for End Signal
                if path_len == 0: break 

                # 3. Read Path Name
                path_bytes = self.recvall(s, path_len)
                rel_path = path_bytes.decode('utf-8')
                
                # 4. Read File Size (8 bytes unsigned long long)
                raw_size = self.recvall(s, 8)
                file_size = struct.unpack('!Q', raw_size)[0]

                # Update UI
                self.lbl_current_file.configure(text=f"📄 {rel_path[:40]}...")

                # 5. Create Directories
                if os.path.dirname(rel_path):
                    os.makedirs(os.path.dirname(rel_path), exist_ok=True)

                # 6. Read File Data
                received = 0
                with open(rel_path, 'wb') as f:
                    while received < file_size:
                        chunk_size = min(BUFFER_SIZE, file_size - received)
                        data = s.recv(chunk_size)
                        if not data: break
                        f.write(data)
                        received += len(data)
                        self.total_recvd += len(data)

            self.transferring = False
            self.lbl_msg.configure(text="All Files Received!")
            self.lbl_speed.configure(text="DONE")
            self.lbl_icon.configure(text="✅", text_color="#2ea043")
            self.btn_action.configure(state="normal", text="RECEIVE ANOTHER", fg_color=COLOR_ACCENT, command=self.reset_scan)
            self.btn_open.pack(pady=10)
            messagebox.showinfo("Success", "Full Transfer Complete!")
            s.close()

        except Exception as e:
            print(e)
            self.transferring = False
            self.lbl_msg.configure(text="Error occurred")
            self.btn_action.configure(state="normal", text="RETRY", command=self.reset_scan)

if __name__ == "__main__":
    app = ReceiverApp()
    app.mainloop()