import requests

if __name__ == "__main__":
    print("Client Main")
    r = requests.get('http://localhost:8181')
    print(r.json())
