import socket

def check_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Порт {port} открыт на {host}")
        else:
            print(f"❌ Порт {port} закрыт или недоступен на {host}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки порта: {e}")

# Проверяем оба порта
check_port("rc1a-f7cbaqtvudip1knj.mdb.yandexcloud.net", 8123)
check_port("rc1a-f7cbaqtvudip1knj.mdb.yandexcloud.net", 8443)
