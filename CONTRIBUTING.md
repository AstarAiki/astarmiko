# Вклад в проект astarmiko

Спасибо, что хотите внести вклад в развитие astarmiko!

## 🚀 Быстрый старт

1. Сделайте форк репозитория: [https://github.com/astaraiki/astarmiko](https://github.com/astaraiki/astarmiko)

2. Клонируйте его к себе:

   ```bash
   git clone https://github.com/yourusername/astarmiko.git
   cd astarmiko
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

## 💡 Рекомендации по стилю кода

Если вы не уверены, какой стиль принят — пока придерживайтесь следующего:

* Используйте 4 пробела для отступов.
* Оформляйте функции с docstring (как сейчас в `base.py`).
* Для форматирования (опционально) можно использовать:

  ```bash
  pip install black
  black astarmiko/
  ```
* Для базовой проверки синтаксиса:

  ```bash
  pip install flake8
  flake8 astarmiko/
  ```

## 🧪 Тестирование

Если вы добавляете функциональность — по возможности добавьте и примеры использования, либо минимальные тесты.

## 🛠️ Создание Pull Request

1. Создайте новую ветку для своей задачи:

   ```bash
   git checkout -b fix-name-resolution
   ```

2. Сделайте коммит с понятным описанием:

   ```bash
   git commit -am "Fix AD hostname resolution for edge cases"
   ```

3. Отправьте изменения на GitHub:

   ```bash
   git push origin fix-name-resolution
   ```

4. Создайте Pull Request через веб-интерфейс GitHub и дождитесь ревью.

---

Если возникают вопросы — создавайте issue прямо в GitHub. Добро пожаловать в команду! 💻

