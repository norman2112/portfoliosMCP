"""Generate SQL insert statements for test data."""
import random
import sys
import json

TENANT_ID = "LK~d09-12345678"
OBJ_PER_WIC = 10
KR_PER_OBJ = 10


def generate_for_settings(user_id, tenant_id_str):
    """Generate an insert for settings table."""

    return """
        insert into settings (
            tenant_id_str,
            app_created_by,
            app_last_updated_by
        ) values (
            '{tenant_id_str}',
            '{user_id}',
            '{user_id}'
        )
    """.format(
        tenant_id_str=tenant_id_str, user_id=user_id
    )


def generate_for_wic(boards, users, tenant_id_str):
    """Generate inserts for WIC table."""

    s = []
    templ = """
        insert into work_item_containers (
            external_title,
            external_id,
            tenant_id_str,
            external_type,
            app_created_by,
            app_last_updated_by,
            deleted_at_epoch,
            app_name
        ) values (
            'Migration Test',
            '{external_id}',
            '{tenant_id_str}',
            'leankit',
            '{user_id}',
            '{user_id}',
            0,
            'leankit'
        );
    """

    for board_id in boards:
        user_id = random.choice(users)
        s.append(
            templ.format(
                external_id=board_id, tenant_id_str=tenant_id_str, user_id=user_id
            )
        )

    return s


def generate_for_objective(wics, users, tenant_id_str):
    """Generate inserts for OBJ table."""

    s = []
    templ = """
        insert into objectives (
            name,
            starts_at,
            ends_at,
            work_item_container_id,
            tenant_id_str,
            app_owned_by,
            app_created_by,
            app_last_updated_by,
            deleted_at_epoch,
            level_depth
        ) values (
            'Migration Test Obj',
            '2023-08-01',
            '2023-08-30',
            {wic_id},
            '{tenant_id_str}',
            '{user_id}',
            '{user_id}',
            '{user_id}',
            0,
            3
        );
    """

    for wic_id in wics:
        for i in range(OBJ_PER_WIC):
            user_id = random.choice(users)
            s.append(
                templ.format(
                    wic_id=wic_id, tenant_id_str=tenant_id_str, user_id=user_id
                )
            )

    return s


def generate_for_keyresults(obj_ids, users, tenant_id_str):
    """Generate inserts for KR table."""

    s = []
    templ = """
        insert into key_results (
            name,
            starts_at,
            ends_at,
            starting_value,
            target_value,
            objective_id,
            tenant_id_str,
            app_owned_by,
            app_created_by,
            app_last_updated_by,
            deleted_at_epoch
        ) values (
            'Migration Test KR',
            '2023-08-01',
            '2023-08-30',
            0,
            100,
            {obj_id},
            '{tenant_id_str}',
            '{user_id}',
            '{user_id}',
            '{user_id}',
            0
        );
    """

    for obj_id in obj_ids:
        for i in range(KR_PER_OBJ):
            user_id = random.choice(users)
            s.append(
                templ.format(
                    obj_id=obj_id, tenant_id_str=tenant_id_str, user_id=user_id
                )
            )

    return s


def generate_for_work_items(wic_id, users, cards, tenant_id_str):
    """Generate inserts for WI table."""

    templ = """
        insert into work_items (
            work_item_container_id,
            external_id,
            external_type,
            app_name,
            tenant_id_str,
            app_created_by,
            app_last_updated_by
        ) values (
            {wic_id},
            '{card_id}',
            'leankit',
            'leankit',
            '{tenant_id_str}',
            '{user_id}',
            '{user_id}'
        );
    """

    return templ.format(
        wic_id=wic_id, card_id=cards[0], tenant_id_str=tenant_id_str, user_id=users[0]
    )


def generate_for_mapping(wi_id, kr_id, users, tenant_id_str):
    """Generate inserts for WI table."""

    templ = """
        insert into key_result_work_item_mappings (
            key_result_id,
            work_item_id,
            tenant_id_str,
            app_created_by,
            app_last_updated_by
        ) values (
            {wi_id},
            {kr_id},
            '{tenant_id_str}',
            '{user_id}',
            '{user_id}'
        );
    """

    return templ.format(
        wi_id=wi_id, kr_id=kr_id, tenant_id_str=tenant_id_str, user_id=users[0]
    )


#
# For converting IDs from SQL to Python list use this command:
# tr '\n' ','
#


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)

    with open(sys.argv[1]) as jsonfile:
        noted_ids = json.load(jsonfile)

    boards = noted_ids["board"][0:10]
    cards = noted_ids["card"][0:200]
    users = noted_ids["user"][0:100]

    step = int(sys.argv[2])

    if step == 1:
        print("Step - 1")
        print("SETTINGS")
        print(generate_for_settings(users[0], TENANT_ID))
        print("==" * 20)

        print("WORK_ITEM_CONTAINERS")
        sqls = generate_for_wic(boards, users, TENANT_ID)
        for sql in sqls:
            print(sql)
        print("==" * 20)

        print("GET WORK_ITEM_CONTAINERS for IDs")
        print(
            f"select id from work_item_containers where tenant_id_str = '{TENANT_ID}'"
        )
        print("==" * 20)

        sys.exit(0)

    # populate here
    wic_ids = []
    if step == 2 and wic_ids:
        print("Step - 2")
        print("OBJECTIVES")
        sqls = generate_for_objective(wic_ids, users, TENANT_ID)
        for sql in sqls:
            print(sql)
        print("==" * 20)
        print("GET OBJECTIVES for IDs")
        print(f"select id from objectives where tenant_id_str = '{TENANT_ID}'")
        print("==" * 20)
        print("WORK_ITEM")
        print(generate_for_work_items(wic_ids[0], users, cards, TENANT_ID))
        print("==" * 20)
        print("GET WORK_ITEMS for IDs")
        print(f"select id from work_items where tenant_id_str = '{TENANT_ID}'")
        print("==" * 20)
        sys.exit(0)

    # populate here
    obj_ids = []
    wic_id = None
    if step == 3 and obj_ids and wic_id:
        print("Step - 3")
        print("KEY_RESULTS")
        sqls = generate_for_keyresults(obj_ids, users, TENANT_ID)
        for sql in sqls:
            print(sql)
        print("==" * 20)
        print("GET KEY_RESULTS for IDs")
        print(
            f"""
            select kr.id from key_results kr inner join objectives obj on obj.id = kr.objective_id
            inner join work_item_containers wic on obj.work_item_container_id = wic.id
            where kr.tenant_id_str = '{TENANT_ID}' and wic.id = {wic_id}
            """
        )
        print("==" * 20)
        sys.exit(0)

    # populate here
    kr_id = None
    wi_id = None
    if step == 4 and kr_id:
        print("KEY_RESULT_WORK_ITEM_MAPPINGS")
        print(generate_for_mapping(kr_id, wi_id, users, TENANT_ID))
        print("==" * 20)
