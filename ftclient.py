import requests

SERVER_PORT = 8181
SERVER_ADDRESS = 'localhost'


if __name__ == "__main__":
    print("Client Main")
    r = requests.get('http://localhost:8181')
    print(r.json())

    r = requests.get('http://localhost:8181/fuck_my_face')
    print(r.json())

    r = requests.get('http://localhost:8181/current_task')
    print(r.json())
