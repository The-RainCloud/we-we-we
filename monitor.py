import psutil
import json
import time
import requests
import traceback  # Import the traceback module

API_ENDPOINT = 'http://192.168.0.103:5000/api/metrics'  # Укажите правильный IP-адрес

def get_server_data():
    """Собирает метрики сервера."""
    try:
        cpu_usage = psutil.cpu_percent(interval=None) #Удаляем interval
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        uptime = time.time() - psutil.boot_time()
        disk_io = psutil.disk_io_counters()  # Получаем статистику ввода/вывода диска

        data = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'uptime': uptime,
            'disk_read_bytes': disk_io.read_bytes, # Отправляем общее кол-во прочитанных байт
        }
        print(f"Collected server data: {data}") # Debugging
        return data
    except Exception as e:
        print(f"Error in get_server_data: {e}") # Detailed error message
        traceback.print_exc() # Print the traceback
        return None

if __name__ == '__main__':
    while True:
        data = get_server_data()
        if data is None:
            print("Failed to get server data.  Retrying in 1 second...")
            time.sleep(60)
            continue # Skip the rest of the loop and retry

        try:
            print(f"Sending data to {API_ENDPOINT}: {data}") # Debugging
            response = requests.get(API_ENDPOINT)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            print(f"Data sent successfully.  Response: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending data: {e}")
            traceback.print_exc() # Print the traceback for request exceptions
        except Exception as e:
             print(f"General error in main loop: {e}")
             traceback.print_exc()
        time.sleep(60) #Обновляем данные каждую секунду

    