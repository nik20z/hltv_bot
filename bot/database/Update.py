from bot.database.connect import cursor, connection


def user_timezone(user_id: int, timezone_):
    """Обновляем часовой пояс пользователя (timezone) по егo id (user_id)"""
    query = "UPDATE telegram SET timezone_ = '{1}' WHERE user_id = {0}".format(user_id, timezone_)
    cursor.execute(query)
    connection.commit()


def user_bool_parameter(user_id: int, column_name: str):
    """Обновляем данные о булевых значениях настроек по id пользователя (user_id) и названию параметра (colomn_name)"""
    query = "UPDATE telegram SET {1} = NOT telegram.{1} WHERE user_id = {0}".format(user_id, column_name)
    cursor.execute(query)
    connection.commit()


def user_notice(user_id: int, type_notice: str, id_: int, limit=20):
    column_name = 'notice_' + type_notice
    query = """UPDATE telegram 
                SET {1} = CASE
                    WHEN 
                        ('{1}' IN ('notice_teams', 'notice_events') OR 
                        '{1}' = 'notice_matches' 
                        AND {2} = (SELECT match.match_id FROM match WHERE match.match_id = {2}))
                        AND cardinality(ARRAY[{1}]) < {3} 
                        AND NOT ARRAY[{1}] @> ARRAY[{2}] 
                            THEN array_append({1}, {2}) 
                    ELSE array_remove({1}, {2}) 
                END
                WHERE telegram.user_id = {0} 
                RETURNING {2} = ANY (ARRAY[{1}]), cardinality(ARRAY[{1}]) >= {3};
            """.format(user_id, column_name, id_, limit)

    cursor.execute(query)
    connection.commit()
    update_result, limit_condition = cursor.fetchone()
    return update_result, not update_result and limit_condition

    # def delete_old_events(self):
    # cursor.execute(query_update_delete_old_events)
    # connection.commit()


def stars_matches_display(user_id: int):
    query = """UPDATE telegram 
                    SET stars_matches_display = CASE 
                    WHEN stars_matches_display < 5
                        THEN stars_matches_display + 1
                    ELSE 0
                    END
                WHERE telegram.user_id = {0}
            """.format(user_id)
    cursor.execute(query)
    connection.commit()
