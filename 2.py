from datetime import datetime
import pytz

# Устанавливаем временную зону на Москву
moscow_tz = pytz.timezone('Europe/Moscow')
moscow_time = datetime.now(moscow_tz)

print("Текущее московское время:", moscow_time.strftime("%Y-%m-%d %H:%M:%S"))
