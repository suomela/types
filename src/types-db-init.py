import sys
sys.path.append('lib')
import TypesDatabase

def db_init(filename=TypesDatabase.DEFAULT_FILENAME):
    conn = TypesDatabase.open_db(filename)
    TypesDatabase.create_if_needed(conn)
    conn.commit()

if len(sys.argv) > 1:
    for filename in sys.argv[1:]:
        db_init(filename)
else:
    db_init()
