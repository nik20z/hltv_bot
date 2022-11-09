from bot.database.connect import cursor, connection


def table(tableName: str):
    cursor.execute(f"DROP TABLE {tableName} IF EXISTS")
    connection.commit()

def one_row(tableName: str, id_: int):
    cursor.execute(f"DELETE FROM {tableName} WHERE id = {id_}")
    connection.commit()

def rows(tableName: str):
    cursor.execute(f"DELETE FROM {tableName}")
    connection.commit()