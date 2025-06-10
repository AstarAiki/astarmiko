# 🚀 Установка примерных конфигов и шаблонов для astarmiko

Этот репозиторий содержит примерные файлы конфигурации и шаблоны, которые нужно скопировать в системный каталог (например, `/etc/astarmiko/`).

---

## 📥 Скачивание и установка

```bash
# 1️⃣ Скачиваем архив с последней версией репозитория
wget https://github.com/astaraiki/astarmiko/archive/refs/heads/main.zip -O /tmp/astarmiko.zip

# 2️⃣ Распаковываем архив
unzip /tmp/astarmiko.zip -d /tmp/

# 3️⃣ Копируем каталоги YAML, TEMPLATES, example в /etc/astarmiko/
sudo mkdir -p /etc/astarmiko
sudo cp -r /tmp/astarmiko-main/astarmiko/YAML /etc/astarmiko/
sudo cp -r /tmp/astarmiko-main/astarmiko/TEMPLATES /etc/astarmiko/
sudo cp -r /tmp/astarmiko-main/astarmiko/example /etc/astarmiko/

# 4️⃣ Проверяем содержимое
ls /etc/astarmiko

