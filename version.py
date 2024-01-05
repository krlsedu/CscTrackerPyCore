def get_version():
    return open('version.txt', 'r').read().strip()

def get_app_name():
    try:
        return open('app_name.txt', 'r').read().strip()
    except Exception:
        return 'no_app_name'
