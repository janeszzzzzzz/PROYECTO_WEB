# import pymysql

# def get_db_connection():
#     return pymysql.connect(
#         host="localhost",        # MariaDB en Windows
#         user="root",             # o el usuario que uses
#         password="",             # pon tu password si tiene
#         database="proyecto_web",
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True
#     )
# import pymysql

# def get_db_connection():
#     return pymysql.connect(
#         host="127.0.0.1",
#         user="webuser",
#         password="webpass123",
#         database="proyecto_web",
#         port=3307,
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True
#     )


# import pymysql
# import os

# def get_db_connection():
#     return pymysql.connect(
#         host=os.getenv("DB_HOST", "db"),
#         port=int(os.getenv("DB_PORT", 3306)),
#         user=os.getenv("DB_USER", "root"),
#         password=os.getenv("DB_PASSWORD", ""),
#         database=os.getenv("DB_NAME", "proyecto_web"),
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True
#     )

# import os
# import pymysql

# def get_db_connection():
#     return pymysql.connect(
#         host=os.getenv("DB_HOST", "db"),
#         port=int(os.getenv("DB_PORT", 3306)),
#         user=os.getenv("DB_USER", "webuser"),
#         password=os.getenv("DB_PASSWORD", "webpass123"),
#         database=os.getenv("DB_NAME", "proyecto_web"),
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True
#     )



# def get_db_connection():
#     return pymysql.connect(
#         host="127.0.0.1",   # 🔥 NO db
#         port=3307,          # el puerto que tú pusiste
#         user="webuser",
#         password="webpass123",
#         database="proyecto_web",
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True
#     )

import pymysql
import os

def get_db_connection():
    return pymysql.connect(
        host="db",
        port=3306,
        user="webuser",
        password="webpass123",
        database="proyecto_web",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
