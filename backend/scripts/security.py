import secrets


def generate_secret_key():
    return secrets.token_hex(32)


print(f"SECRET_KEY = {generate_secret_key()}")
