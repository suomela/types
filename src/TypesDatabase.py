import sqlite3

DEFAULT_FILENAME = 'db/types.sqlite'

def open_db(filename=DEFAULT_FILENAME):
    conn = sqlite3.connect(filename)
    conn.execute('''PRAGMA foreign_keys = ON''')
    return conn

def create_if_needed(conn):
    conn.executescript('''

        CREATE TABLE IF NOT EXISTS stat (
            statcode TEXT NOT NULL PRIMARY KEY,
            description TEXT,
            ylabel TEXT,
            xlabel TEXT
        );

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('type-word', 'Types vs. running words', 'Types', 'Running words');

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('type-token', 'Types vs. tokens', 'Types', 'Tokens');

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('hapax-word', 'Hapaxes vs. running words', 'Hapaxes', 'Running words');

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('hapax-token', 'Hapaxes vs. tokens', 'Hapaxes', 'Tokens');

        INSERT OR IGNORE INTO stat (statcode, description, ylabel, xlabel)
        VALUES ('token-word', 'Tokens vs. running words', 'Tokens', 'Running words');

        CREATE TABLE IF NOT EXISTS defaultstat (
            statcode TEXT NOT NULL PRIMARY KEY REFERENCES stat(statcode)
        );

        INSERT OR IGNORE INTO defaultstat (statcode) VALUES ('type-word');
        INSERT OR IGNORE INTO defaultstat (statcode) VALUES ('type-token');

        CREATE TABLE IF NOT EXISTS defaultlevel (
            level REAL NOT NULL PRIMARY KEY
        );

        INSERT OR IGNORE INTO defaultlevel (level) VALUES (0.0001);
        INSERT OR IGNORE INTO defaultlevel (level) VALUES (0.001);
        INSERT OR IGNORE INTO defaultlevel (level) VALUES (0.01);
        INSERT OR IGNORE INTO defaultlevel (level) VALUES (0.1);

        CREATE TABLE IF NOT EXISTS corpus (
            corpuscode TEXT NOT NULL PRIMARY KEY,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS dataset (
            corpuscode TEXT NOT NULL REFERENCES corpus(corpuscode),
            datasetcode TEXT NOT NULL,
            description TEXT,
            PRIMARY KEY (corpuscode, datasetcode)
        );

        CREATE TABLE IF NOT EXISTS sample (
            corpuscode TEXT NOT NULL REFERENCES corpus(corpuscode),
            samplecode TEXT NOT NULL,
            wordcount INTEGER NOT NULL,
            description TEXT,
            PRIMARY KEY (corpuscode, samplecode)
        );

        CREATE TABLE IF NOT EXISTS collection (
            corpuscode TEXT NOT NULL REFERENCES corpus(corpuscode),
            collectioncode TEXT NOT NULL,
            groupcode TEXT,
            description TEXT,
            PRIMARY KEY (corpuscode, collectioncode)
        );

        CREATE TABLE IF NOT EXISTS sample_collection (
            corpuscode TEXT NOT NULL,
            samplecode TEXT NOT NULL,
            collectioncode TEXT NOT NULL,
            PRIMARY KEY (corpuscode, samplecode, collectioncode),
            FOREIGN KEY (corpuscode, samplecode) REFERENCES sample(corpuscode, samplecode),
            FOREIGN KEY (corpuscode, collectioncode) REFERENCES collection(corpuscode, collectioncode)
        );

        CREATE TABLE IF NOT EXISTS token (
            corpuscode TEXT NOT NULL,
            samplecode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            tokencode TEXT NOT NULL,
            tokencount INTEGER NOT NULL,
            PRIMARY KEY (corpuscode, samplecode, datasetcode, tokencode),
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode),
            FOREIGN KEY (corpuscode, samplecode) REFERENCES sample(corpuscode, samplecode)
        );

        CREATE TABLE IF NOT EXISTS log (
            id INTEGER PRIMARY KEY NOT NULL,
            corpuscode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            timestamp TEXT,
            description TEXT,
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode)
        );

        CREATE TABLE IF NOT EXISTS result_p (
            id INTEGER PRIMARY KEY NOT NULL,
            corpuscode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            collectioncode TEXT NOT NULL,
            statcode TEXT NOT NULL REFERENCES stat(statcode),
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            total INTEGER NOT NULL,
            below INTEGER NOT NULL,
            above INTEGER NOT NULL,
            logid INTEGER NOT NULL REFERENCES log(id),
            UNIQUE (corpuscode, datasetcode, collectioncode, statcode),
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode),
            FOREIGN KEY (corpuscode, collectioncode) REFERENCES collection(corpuscode, collectioncode)
        );

        CREATE TABLE IF NOT EXISTS result_q (
            i INTEGER PRIMARY KEY NOT NULL,
            n INTEGER NOT NULL,
            corpuscode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            collectioncode TEXT NOT NULL,
            statcode TEXT NOT NULL REFERENCES stat(statcode),
            side TEXT NOT NULL,
            p REAL,
            q REAL,
            UNIQUE (corpuscode, datasetcode, collectioncode, statcode, side),
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode),
            FOREIGN KEY (corpuscode, collectioncode) REFERENCES collection(corpuscode, collectioncode)
        );

        CREATE TABLE IF NOT EXISTS result_curve (
            id INTEGER PRIMARY KEY NOT NULL,
            corpuscode TEXT NOT NULL,
            datasetcode TEXT NOT NULL,
            statcode TEXT NOT NULL REFERENCES stat(statcode),
            level REAL NOT NULL,
            side TEXT NOT NULL,
            xslots INTEGER NOT NULL,
            yslots INTEGER NOT NULL,
            iterations INTEGER NOT NULL,
            logid INTEGER NOT NULL REFERENCES log(id),
            UNIQUE (corpuscode, datasetcode, statcode, level, side),
            FOREIGN KEY (corpuscode, datasetcode) REFERENCES dataset(corpuscode, datasetcode)
        );

        CREATE TABLE IF NOT EXISTS result_curve_point (
            curveid INTEGER NOT NULL REFERENCES result_curve(id),
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            PRIMARY KEY (curveid, x)
        );

        CREATE VIEW IF NOT EXISTS view_corpus AS
        SELECT corpuscode, COUNT(0) AS samplecount
        FROM sample
        GROUP BY corpuscode;

        CREATE VIEW IF NOT EXISTS view_result_type_word AS
        SELECT corpuscode, datasetcode, collectioncode, y AS typecount, x AS wordcount
        FROM result_p
        WHERE statcode = 'type-word'
        ORDER BY corpuscode, datasetcode, collectioncode;

        CREATE VIEW IF NOT EXISTS view_result_type_token AS
        SELECT corpuscode, datasetcode, collectioncode, y AS typecount, x AS tokencount
        FROM result_p
        WHERE statcode = 'type-token'
        ORDER BY corpuscode, datasetcode, collectioncode;

        CREATE VIEW IF NOT EXISTS view_result_hapax_word AS
        SELECT corpuscode, datasetcode, collectioncode, y AS hapaxcount, x AS wordcount
        FROM result_p
        WHERE statcode = 'hapax-word'
        ORDER BY corpuscode, datasetcode, collectioncode;

        CREATE VIEW IF NOT EXISTS view_result_hapax_token AS
        SELECT corpuscode, datasetcode, collectioncode, y AS hapaxcount, x AS tokencount
        FROM result_p
        WHERE statcode = 'hapax-token'
        ORDER BY corpuscode, datasetcode, collectioncode;

        CREATE VIEW IF NOT EXISTS view_result_token_word AS
        SELECT corpuscode, datasetcode, collectioncode, y AS tokencount, x AS wordcount
        FROM result_p
        WHERE statcode = 'token-word'
        ORDER BY corpuscode, datasetcode, collectioncode;

        CREATE VIEW IF NOT EXISTS view_result AS
        SELECT dataset.corpuscode AS corpuscode,
            dataset.datasetcode AS datasetcode,
            collection.collectioncode AS collectioncode, 
            COALESCE(yw.wordcount, hw.wordcount, tw.wordcount) AS wordcount,
            COALESCE(yt.tokencount, ht.tokencount, tw.tokencount) AS tokencount,
            COALESCE(yw.typecount, yt.typecount) AS typecount,
            COALESCE(hw.hapaxcount, ht.hapaxcount) AS hapaxcount
        FROM dataset JOIN collection USING (corpuscode)
        LEFT JOIN view_result_type_word AS yw USING (datasetcode, collectioncode, corpuscode)
        LEFT JOIN view_result_type_token AS yt USING (datasetcode, collectioncode, corpuscode)
        LEFT JOIN view_result_hapax_word AS hw USING (datasetcode, collectioncode, corpuscode)
        LEFT JOIN view_result_hapax_token AS ht USING (datasetcode, collectioncode, corpuscode)
        LEFT JOIN view_result_token_word AS tw USING (datasetcode, collectioncode, corpuscode)
        ORDER BY corpuscode, datasetcode, collectioncode;

        CREATE VIEW IF NOT EXISTS view_missing_curve AS
        SELECT corpuscode, datasetcode, statcode, level, side
        FROM dataset
        JOIN defaultlevel
        JOIN defaultstat
        JOIN (SELECT 'lower' AS side UNION SELECT 'upper' AS side)
        EXCEPT
        SELECT corpuscode, datasetcode, statcode, level, side
        FROM result_curve;

        CREATE VIEW IF NOT EXISTS view_missing_p AS
        SELECT corpuscode, datasetcode, collectioncode, statcode
        FROM dataset
        JOIN collection USING (corpuscode)
        JOIN defaultstat
        EXCEPT
        SELECT corpuscode, datasetcode, collectioncode, statcode
        FROM result_p;

    ''')

def drop_views(conn):
    conn.executescript('''
        DROP VIEW IF EXISTS view_result;
        DROP VIEW IF EXISTS view_result_type_word;
        DROP VIEW IF EXISTS view_result_type_token;
        DROP VIEW IF EXISTS view_result_hapax_word;
        DROP VIEW IF EXISTS view_result_hapax_token;
        DROP VIEW IF EXISTS view_result_token_word;
        DROP VIEW IF EXISTS view_missing_p;
        DROP VIEW IF EXISTS view_missing_curve;
        DROP VIEW IF EXISTS view_collection_dataset_full;
        DROP VIEW IF EXISTS view_collection_dataset;
        DROP VIEW IF EXISTS view_collection;
        DROP VIEW IF EXISTS view_dataset_full;
        DROP VIEW IF EXISTS view_dataset;
        DROP VIEW IF EXISTS view_corpus;
        DROP VIEW IF EXISTS view_q;
        DROP VIEW IF EXISTS view_p2;
        DROP VIEW IF EXISTS view_p;
    ''')

def delete_corpus(conn, corpuscode):
    conn.execute('DELETE FROM result_curve_point WHERE curveid IN (SELECT id FROM result_curve WHERE corpuscode = ?)', (corpuscode,))
    conn.execute('DELETE FROM result_curve WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM result_p WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM log WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM token WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM sample_collection WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM collection WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM sample WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM dataset WHERE corpuscode = ?', (corpuscode,))
    conn.execute('DELETE FROM corpus WHERE corpuscode = ?', (corpuscode,))

def create_corpus(conn, corpuscode, description):
    conn.execute(
        'INSERT INTO corpus (corpuscode, description) VALUES (?, ?)',
        ( corpuscode, description )
    )

def delete_collection(conn, corpuscode, collectioncode):
    conn.execute('DELETE FROM result_p WHERE corpuscode = ? AND collectioncode = ?', (corpuscode, collectioncode))
    conn.execute('DELETE FROM sample_collection WHERE corpuscode = ? AND collectioncode = ?', (corpuscode, collectioncode))
    conn.execute('DELETE FROM collection WHERE corpuscode = ? AND collectioncode = ?', (corpuscode, collectioncode))

def create_collection(conn, corpuscode, groupcode, collectioncode, description):
    conn.execute(
        'INSERT INTO collection (corpuscode, groupcode, collectioncode, description) VALUES (?, ?, ?, ?)',
        (corpuscode, groupcode, collectioncode, description)
    )

def refresh_result(conn):
    conn.execute('''
        CREATE TEMPORARY TABLE tmp_r AS
        SELECT corpuscode, datasetcode, collectioncode, statcode,
            'below' AS side, CAST(below AS REAL)/CAST(total AS REAL) AS p
        FROM result_p
        UNION
        SELECT corpuscode, datasetcode, collectioncode, statcode,
            'above' AS side, CAST(above AS REAL)/CAST(total AS REAL) AS p
        FROM result_p
        ORDER BY p
    ''')

    r = conn.execute('SELECT COUNT(0) FROM tmp_r')
    n = [ i[0] for i in r ][0]

    conn.execute('DELETE FROM result_q')
    conn.execute('''
        INSERT INTO result_q (i, n, corpuscode, datasetcode, collectioncode, statcode, side, p, q)
        SELECT rowid, ?, corpuscode, datasetcode, collectioncode, statcode, side, p,
            p / (CAST(rowid AS REAL)/CAST(? AS REAL)) AS q
        FROM tmp_r
        ORDER BY rowid
    ''', (n, n))
