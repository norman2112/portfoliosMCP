"""Test the PID Api adapter"""

import pytest

from okrs_api.external_apis.pvadmin.adapters import (
    adapt_users_response_with_pvid,
    adapt_user_details_response,
)


@pytest.fixture
def search_user_response():
    return [
        {
            "id": "12345",
            "first_name": "Allan",
            "last_name": "Grant",
            "email_address": "alan@raptorresearch.com",
            "role": "user",
            "administrator": False,
        },
        {
            "id": "5678910",
            "first_name": "Ellie",
            "last_name": "Sattler",
            "email_address": "ellie@dinocouncil.com",
            "role": "user",
            "administrator": False,
        },
        {
            "id": "1112131415",
            "first_name": "Ian",
            "last_name": "Malcom",
            "email_address": "imalcom@chaosrules.com",
            "role": "user",
            "administrator": False,
        },
        {
            "id": "1617181920",
            "first_name": "Mark",
            "last_name": "Hammond",
            "email_address": "mark@hammondcorp.com",
            "role": "user",
            "administrator": False,
        },
    ]


@pytest.fixture
def planview_admin_user_map_response():
    return {
        "tenantGroupId": "LEANKIT~d09-12121222",
        "users": {
            "5678910": "1015678910",
            "12345": "10112345",
            "1112131415": "1011112131415",
        },
    }


@pytest.fixture
def planview_admin_user_no_map_response():
    return {}


@pytest.fixture
def planview_admin_user_details_reponse():
    return [
        {
            "avatarUrl": "https://avatar.me/SSD67",
            "email": "xyz@zyx.abc",
            "firstName": "X",
            "lastName": "Y",
            "id": 122,
            "planview_user_id": "2132321",
        },
        {
            "avatarUrl": "https://avatar.me/SSD68",
            "email": "xyz@zyx.abc",
            "firstName": "X",
            "id": 123,
            "planview_user_id": "2132321",
        },
        {"id": 234},
    ]


def test_adapter_response(search_user_response, planview_admin_user_map_response):
    result = adapt_users_response_with_pvid(
        planview_admin_user_map_response, search_user_response
    )
    assert result == [
        {
            "id": "12345",
            "first_name": "Allan",
            "last_name": "Grant",
            "email_address": "alan@raptorresearch.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": "10112345",
        },
        {
            "id": "5678910",
            "first_name": "Ellie",
            "last_name": "Sattler",
            "email_address": "ellie@dinocouncil.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": "1015678910",
        },
        {
            "id": "1112131415",
            "first_name": "Ian",
            "last_name": "Malcom",
            "email_address": "imalcom@chaosrules.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": "1011112131415",
        },
        {
            "id": "1617181920",
            "first_name": "Mark",
            "last_name": "Hammond",
            "email_address": "mark@hammondcorp.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
    ]


def test_no_mapped_users(search_user_response, planview_admin_user_no_map_response):
    result = adapt_users_response_with_pvid(
        planview_admin_user_no_map_response, search_user_response
    )
    assert result == [
        {
            "id": "12345",
            "first_name": "Allan",
            "last_name": "Grant",
            "email_address": "alan@raptorresearch.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
        {
            "id": "5678910",
            "first_name": "Ellie",
            "last_name": "Sattler",
            "email_address": "ellie@dinocouncil.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
        {
            "id": "1112131415",
            "first_name": "Ian",
            "last_name": "Malcom",
            "email_address": "imalcom@chaosrules.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
        {
            "id": "1617181920",
            "first_name": "Mark",
            "last_name": "Hammond",
            "email_address": "mark@hammondcorp.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
    ]


def test_empty_response(search_user_response):
    result = adapt_users_response_with_pvid(None, search_user_response)
    assert result == [
        {
            "id": "12345",
            "first_name": "Allan",
            "last_name": "Grant",
            "email_address": "alan@raptorresearch.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
        {
            "id": "5678910",
            "first_name": "Ellie",
            "last_name": "Sattler",
            "email_address": "ellie@dinocouncil.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
        {
            "id": "1112131415",
            "first_name": "Ian",
            "last_name": "Malcom",
            "email_address": "imalcom@chaosrules.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
        {
            "id": "1617181920",
            "first_name": "Mark",
            "last_name": "Hammond",
            "email_address": "mark@hammondcorp.com",
            "role": "user",
            "administrator": False,
            "planview_user_id": None,
        },
    ]


def test_adapt_user_details(planview_admin_user_details_reponse):
    result = adapt_user_details_response(planview_admin_user_details_reponse)
    assert result == [
        {
            "avatar": "https://avatar.me/SSD67",
            "email_address": "xyz@zyx.abc",
            "first_name": "X",
            "last_name": "Y",
            "is_deleted": False,
            "id": 122,
            "planview_user_id": "2132321",
        },
        {
            "avatar": "https://avatar.me/SSD68",
            "email_address": "xyz@zyx.abc",
            "first_name": "X",
            "last_name": None,
            "is_deleted": False,
            "id": 123,
            "planview_user_id": "2132321",
        },
        {
            "avatar": None,
            "email_address": None,
            "first_name": None,
            "last_name": None,
            "is_deleted": True,
            "id": 234,
            "planview_user_id": None,
        },
    ]
