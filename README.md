# 🚀 Ultra-Fast LAN File & Folder Transfer (Python)

This project is a desktop-based file and folder sharing application built using **Python socket programming**.  
It allows **direct high-speed transfer over local Wi-Fi** without using the internet.

---

## 📌 Key Features
- Automatic sender discovery using **UDP broadcast**
- High-speed file transfer using **TCP sockets**
- Supports **full folder transfer** with original directory structure
- Large buffer size (1 MB) for maximum throughput
- Real-time speed display in **MB/s**
- Modern GUI using **CustomTkinter**
- No cloud, no compression, no internet dependency

---

## ⚙️ How It Works (Simple Explanation)

1. Receiver scans the local network using UDP
2. Sender responds automatically (no IP needed)
3. Receiver connects to sender using TCP
4. Files are transferred in **1 MB chunks**
5. Folder structure is preserved on receiver side

---

## ⚡ Performance (Real World Testing)

- **5 GHz Wi-Fi:** 25–30 MB/s (≈200–240 Mbps)
- **6 GHz Wi-Fi (Wi-Fi 6E):** 80+ MB/s (hardware dependent)

> Performance is network-bound, not code-bound.

---

## 🛠 Tech Stack
- Python
- Socket Programming (TCP / UDP)
- Multithreading
- CustomTkinter GUI

---

## ▶ How to Run the Project

### 1. Install dependency
```bash
pip install customtkinter
