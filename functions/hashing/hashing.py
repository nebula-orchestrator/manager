import bcrypt


def hash_secret(value_to_hash):
    hashed_secret = bcrypt.hashpw(value_to_hash.encode('utf-8'), bcrypt.gensalt())
    return hashed_secret.decode('utf-8')


def check_secret_matches(value_to_check, hashed_value):
    if bcrypt.checkpw(value_to_check.encode('utf-8'), hashed_value.encode('utf-8')):
        return True
    else:
        return False
