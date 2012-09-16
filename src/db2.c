#include "db2.h"

void
recreate_corpus(const char * restrict corpuscode)
{
    db_exec("DELETE FROM token WHERE corpuscode = ?", BIND(STRING(corpuscode)));
    db_exec("DELETE FROM sample_collection WHERE corpuscode = ?", BIND(STRING(corpuscode)));
    db_exec("DELETE FROM collection WHERE corpuscode = ?", BIND(STRING(corpuscode)));
    db_exec("DELETE FROM sample WHERE corpuscode = ?", BIND(STRING(corpuscode)));
    db_exec("DELETE FROM dataset WHERE corpuscode = ?", BIND(STRING(corpuscode)));
    db_exec("DELETE FROM corpus WHERE corpuscode = ?", BIND(STRING(corpuscode)));
    db_exec("INSERT INTO corpus (corpuscode) VALUES (?)", BIND(STRING(corpuscode)));
}

unsigned
create_temp_sample(const char * restrict corpuscode)
{
    db_exec(
        "CREATE TEMPORARY TABLE tmp_sample AS "
        "SELECT samplecode, wordcount FROM sample WHERE corpuscode = ? ORDER BY samplecode",
        BIND(STRING(corpuscode))
    );
    return db_getuint("SELECT COUNT(0) FROM tmp_sample", NOBIND);
}

unsigned
create_temp_collection(const char * restrict corpuscode)
{
    db_exec(
        "CREATE TEMPORARY TABLE tmp_collection AS "
        "SELECT collectioncode FROM collection WHERE corpuscode = ? ORDER BY collectioncode",
        BIND(STRING(corpuscode))
    );
    return db_getuint("SELECT COUNT(0) FROM tmp_collection", NOBIND);
}

unsigned
create_temp_token(const char * restrict corpuscode, const char * restrict datasetcode)
{
    db_exec(
        "CREATE TEMPORARY TABLE tmp_token AS "
        "SELECT DISTINCT tokencode FROM token "
        "WHERE corpuscode = ? AND datasetcode = ? ORDER BY tokencode",
        BIND(STRING(corpuscode), STRING(datasetcode))
    );
    return db_getuint("SELECT COUNT(0) FROM tmp_token", NOBIND);
}
    
unsigned
create_temp_sample_collection(const char * restrict corpuscode)
{
    db_exec(
        "CREATE TEMPORARY TABLE tmp_sample_collection AS "
        "SELECT tmp_sample.rowid sampleid, tmp_collection.rowid collectionid "
        "FROM sample_collection, tmp_sample, tmp_collection "
        "WHERE sample_collection.collectioncode = tmp_collection.collectioncode "
        "AND sample_collection.samplecode = tmp_sample.samplecode "
        "AND sample_collection.corpuscode = ?",
        BIND(STRING(corpuscode))
    );
    return db_getuint("SELECT COUNT(0) FROM tmp_sample_collection", NOBIND);
}

unsigned
create_temp_sample_token(const char * restrict corpuscode, const char * restrict datasetcode)
{
    db_exec(
        "CREATE TEMPORARY TABLE tmp_sample_token AS "
        "SELECT tmp_sample.rowid sampleid, tmp_token.rowid typeid, token.tokencount tokencount "
        "FROM token, tmp_sample, tmp_token "
        "WHERE token.tokencode = tmp_token.tokencode "
        "AND token.samplecode = tmp_sample.samplecode "
        "AND token.corpuscode = ? "
        "AND token.datasetcode = ?",
        BIND(STRING(corpuscode), STRING(datasetcode))
    );
    return db_getuint("SELECT COUNT(0) FROM tmp_sample_token", NOBIND);
}
