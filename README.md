# TGC UdL
**TGC UdL** (Trading Card Game UdL) is a web application built with Django and Tailwind CSS that allows users to collect and trade digital cards featuring professors from the University of Lleida (UdL). It's a fun and gamified way to engage with the academic environment.

---

## 🚀 Demo

Coming soon...

---

## 📚 Table of Contents

- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Using Docker](#-using-docker)
  - [Running Locally](#-running-locally)
- [Contributing](#-contributing)
- [Issues](#-issues)
- [Versions](#-versions)
- [License](#-license)

---

## ✅ Requirements

### Using Docker

- Docker
- Docker Compose

### Running Locally

- Python 3.12
- [Poetry](https://python-poetry.org/)

---
## 🔧 Installation

### 🐳 Using Docker

1. Clone the repository:

```bash
git clone https://github.com/nsaadig16/DjangoProjectWeb.git
```

2. Navigate to the project directory:
```bash
cd DjangoProjectWeb
```

3. Build and run the Docker container:
```bash
docker-compose up --build
```

4. Access the application at `http://localhost:8000`.

### 💻 Running Locally

1. Clone the repository:

```bash
git clone https://github.com/nsaadig16/DjangoProjectWeb.git
```

2. Navigate to the project directory:
```bash
cd DjangoProjectWeb
```

3. Create a virtual enviorentment (OPTIONAL)
```bash
python -m venv venv
source venv/bin/activate
```

4. Install the project dependencies:
```bash
poetry install
```

5. Make migrations:
```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
# If tables missing poetry run python manage.py migrate --run-syncdb
```

## 🤝 Contributing

We welcome contributions of all kinds!  
To get started:

1. 🍴 Fork the repository  
2. 🌱 Create a new branch: `git checkout -b feature-name`  
3. ✍️ Make your changes and commit: `git commit -m 'Add new feature'`  
4. 🚀 Push the branch: `git push origin feature-name`  
5. 🔁 Open a Pull Request

## 🐛 Issues

Found a bug or have a feature request?  
Feel free to [open an issue](https://github.com/nsaadig16/DjangoProjectWeb/issues) and let us know!

- 🐞 Bug reports help us improve
- 💡 Feature requests are always welcome

## 📦 Versions

- **Project:** TGC UdL v0.1.0  
- **Python:** >=3.12  
- **Django:** >=5.1.6, <6.0.0  
- **Pillow:** >=11.1.0, <12.0.0  
- **Poetry:** Configured with Poetry (package-mode disabled)  

## 📄 License

This project is licensed under the MIT License.  
Feel free to use, modify, and distribute it as you like — just keep the original license.  

📝 See the full [LICENSE](LICENSE) file for more details.
