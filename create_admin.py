import requests
import json

def create_admin_user(username, email, password):
    url = 'http://localhost:5001/create-admin'
    data = {
        'username': username,
        'email': email,
        'password': password
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 201:
            print("Admin user created successfully!")
        else:
            print(f"Error: {response.json().get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    
    create_admin_user(username, email, password) 