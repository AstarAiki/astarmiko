# 🚀 Установка примерных конфигов и шаблонов для astarmiko

Чтобы начать использовать `astarmiko`, нужно скопировать примерные файлы конфигурации и шаблоны в удобное место — например, в каталог домашнего пользователя.

---

## 📥 Скачивание и установка

```bash
# 1️⃣ Скачиваем архив с последней версией репозитория
wget https://github.com/astaraiki/astarmiko/archive/refs/heads/main.zip -O /tmp/astarmiko.zip

# 2️⃣ Распаковываем архив
unzip /tmp/astarmiko.zip -d /tmp/

# 3️⃣ Копируем каталоги YAML, TEMPLATES, example в ~/astarmiko/
mkdir -p ~/astarmiko
cp -r /tmp/astarmiko-main/astarmiko/YAML ~/astarmiko/
cp -r /tmp/astarmiko-main/astarmiko/TEMPLATES ~/astarmiko/
cp -r /tmp/astarmiko-main/astarmiko/example ~/astarmiko/

# 4️⃣ Проверяем содержимое
ls ~/astarmiko

