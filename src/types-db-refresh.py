import sys
sys.path.append('lib')
import TypesDatabase

def db_init(filename=TypesDatabase.DEFAULT_FILENAME):
    conn = TypesDatabase.open_db(filename)
    TypesDatabase.drop_views(conn)
    TypesDatabase.create_if_needed(conn)
    TypesDatabase.refresh_result(conn)
    conn.commit()

if len(sys.argv) > 1:
    for filename in sys.argv[1:]:
        db_init(filename)
else:
    db_init()
