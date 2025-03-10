# 🚀 Distributed Storage System

This project sets up two standalone MinIO instances behind an Nginx load balancer using Docker Compose.

---

## 📋 Prerequisites

- Docker
- Docker Compose
- Python 3.8+
- `pip` (Python package manager)

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/sharansukesh1003/distributed-storage-system.git
cd distributed_storage
```

### 2️⃣ Create and Activate Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Python Dependencies (Optional if you're integrating with Django)

```bash
pip install -r requirements.txt
```

> 💡 Make sure you add your Django-related dependencies in `requirements.txt` if needed.

---

## 🚀 Run the Project

```bash
docker-compose up -d
```

This will start:

- **MinIO Node 1:**

  - API: `http://localhost:9000`
  - Console: `http://localhost:9001`

- **MinIO Node 2:**

  - API: `http://localhost:9002`
  - Console: `http://localhost:9003`

- **Nginx Load Balancer:**
  - `http://localhost/`

---

## 🔐 MinIO Credentials

```
Username: admin
Password: adminpassword
```

---

## 📌 Notes

- Access MinIO Web Console:

  - Node 1: [http://localhost:9001](http://localhost:9001)
  - Node 2: [http://localhost:9003](http://localhost:9003)

- You can create two buckets in each node:

  - `files`
  - `files-backup`

- Nginx balances file uploads between nodes using **least connections strategy**.

- You can configure replication from the MinIO dashboard or via `mc` CLI.

---

## ✅ Done!

Your local MinIO cluster with load balancing is up and running. Time to integrate it with your Django app or any other project!
