# import os
# from urllib.parse import urlparse

# def terminate_connections(db_name, user, password, host, port):
#     # print("Terminating active connections...")

#     terminate_cmd = f'''
#     PGPASSWORD="{password}" psql -h {host} -p {port} -U {user} -d postgres -c "
#     SELECT pg_terminate_backend(pid)
#     FROM pg_stat_activity
#     WHERE datname = '{db_name}' AND pid <> pg_backend_pid();
#     "
#     '''
#     os.system(terminate_cmd)


# def create_sandbox_db(prod_db_url, sandbox_db_name="sandbox_db"):
#     # print("Creating sandbox DB...")

#     url = urlparse(prod_db_url)
#     db_name = url.path[1:]
#     user = url.username
#     password = url.password
#     host = url.hostname or "localhost"
#     port = url.port or 5432

#     dump_file = "sandbox_dump.sql"

#     # print("Dumping production DB...")
#     dump_cmd = f'PGPASSWORD="{password}" pg_dump -h {host} -p {port} -U {user} -d {db_name} > {dump_file}'
#     if os.system(dump_cmd) != 0:
#         raise Exception("pg_dump failed!")

#     terminate_connections(sandbox_db_name, user, password, host, port)

#     print("Dropping old sandbox DB...")
#     os.system(f'PGPASSWORD="{password}" dropdb -h {host} -p {port} -U {user} {sandbox_db_name}')

#     print("Creating sandbox DB...")
#     if os.system(f'PGPASSWORD="{password}" createdb -h {host} -p {port} -U {user} {sandbox_db_name}') != 0:
#         raise Exception("Sandbox DB creation failed!")

#     print("Restoring dump...")
#     if os.system(f'PGPASSWORD="{password}" psql -h {host} -p {port} -U {user} -d {sandbox_db_name} -f {dump_file}') != 0:
#         raise Exception("Restore failed!")

#     # print("Sandbox DB created successfully!")

import os
from urllib.parse import urlparse

def terminate_connections(db_name, user, password, host, port):
    env = os.environ.copy()
    env["PGPASSWORD"] = str(password)

    import subprocess
    cmd = f'psql -h {host} -p {port} -U {user} -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = \'{db_name}\' AND pid <> pg_backend_pid();"'
    subprocess.run(cmd, env=env, shell=True)


def create_sandbox_db(prod_db_url, sandbox_db_name="sandbox_db"):
    url = urlparse(prod_db_url)
    db_name = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname or "localhost"
    port = url.port or 5432

    env = os.environ.copy()
    env["PGPASSWORD"] = str(password)

    import subprocess

    dump_file = "sandbox_dump.sql"

    print("Dumping production DB...")
    result = subprocess.run(f'pg_dump -h {host} -p {port} -U {user} -d {db_name} -f {dump_file}', env=env, shell=True)
    if result.returncode != 0:
        raise Exception("pg_dump failed!")

    terminate_connections(sandbox_db_name, user, password, host, port)

    print("Dropping old sandbox DB...")
    subprocess.run(f'dropdb -h {host} -p {port} -U {user} --if-exists {sandbox_db_name}', env=env, shell=True)

    print("Creating sandbox DB...")
    result = subprocess.run(f'createdb -h {host} -p {port} -U {user} {sandbox_db_name}', env=env, shell=True)
    if result.returncode != 0:
        raise Exception("Sandbox DB creation failed!")

    print("Restoring dump...")
    result = subprocess.run(f'psql -h {host} -p {port} -U {user} -d {sandbox_db_name} -f {dump_file}', env=env, shell=True)
    if result.returncode != 0:
        raise Exception("Restore failed!")

    print("Sandbox DB created successfully!")