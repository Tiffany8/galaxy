import json

from requests import (
    delete,
    get,
    put,
)

from galaxy_test.base.api_asserts import assert_object_id_error
from galaxy_test.base.populators import skip_without_tool
from ._framework import ApiTestCase

TEST_USER_EMAIL = "user_for_users_index_test@bx.psu.edu"
TEST_USER_EMAIL_DELETE = "user_for_delete_test@bx.psu.edu"
TEST_USER_EMAIL_PURGE = "user_for_purge_test@bx.psu.edu"
TEST_USER_EMAIL_UNDELETE = "user_for_undelete_test@bx.psu.edu"


class UsersApiTestCase(ApiTestCase):
    def test_index(self):
        self._setup_user(TEST_USER_EMAIL)
        all_users_response = self._get("users", admin=True)
        self._assert_status_code_is(all_users_response, 200)
        all_users = all_users_response.json()
        # New user is in list
        assert len([u for u in all_users if u["email"] == TEST_USER_EMAIL]) == 1
        # Request made from admin user, so should at least self and this
        # new user.
        assert len(all_users) > 1

    def test_index_only_self_for_nonadmins(self):
        self._setup_user(TEST_USER_EMAIL)
        with self._different_user():
            all_users_response = self._get("users")
            # Non admin users can only see themselves
            assert len(all_users_response.json()) == 1

    def test_show(self):
        user = self._setup_user(TEST_USER_EMAIL)
        with self._different_user(email=TEST_USER_EMAIL):
            show_response = self.__show(user)
            self._assert_status_code_is(show_response, 200)
            self.__assert_matches_user(user, show_response.json())

    def test_update(self):
        new_name = "linnaeus"
        user = self._setup_user(TEST_USER_EMAIL)
        not_the_user = self._setup_user("email@example.com")
        with self._different_user(email=TEST_USER_EMAIL):

            # working
            update_response = self.__update(user, username=new_name)
            self._assert_status_code_is(update_response, 200)
            update_json = update_response.json()
            self.assertEqual(update_json["username"], new_name)

            # too short
            update_response = self.__update(user, username="mu")
            self._assert_status_code_is(update_response, 400)

            # not them
            update_response = self.__update(not_the_user, username=new_name)
            self._assert_status_code_is(update_response, 403)

            # non-existent
            no_user_id = "5d7db0757a2eb7ef"
            update_url = self._api_url(f"users/{no_user_id}", use_key=True)
            update_response = put(update_url, data=json.dumps(dict(username=new_name)))
            assert_object_id_error(update_response)

    def test_admin_update(self):
        new_name = "flexo"
        user = self._setup_user(TEST_USER_EMAIL)
        update_url = self._api_url(f"users/{user['id']}", params=dict(key=self.master_api_key))
        update_response = put(update_url, data=json.dumps(dict(username=new_name)))
        self._assert_status_code_is(update_response, 200)
        update_json = update_response.json()
        self.assertEqual(update_json["username"], new_name)

    def test_delete_user(self):
        user = self._setup_user(TEST_USER_EMAIL_DELETE)
        self._delete(f"users/{user['id']}", admin=True)
        updated_user = self._get(f"users/deleted/{user['id']}", admin=True).json()
        assert updated_user["deleted"] is True, updated_user

    def test_purge_user(self):
        """Delete user and then purge them."""
        user = self._setup_user(TEST_USER_EMAIL_PURGE)
        response = self._delete(f"users/{user['id']}", admin=True)
        self._assert_status_code_is_ok(response)
        data = dict(purge="True")
        response = self._delete(f"users/{user['id']}", data=data, admin=True)
        self._assert_status_code_is_ok(response)
        payload = {"deleted": "True"}
        purged_user = self._get(f"users/{user['id']}", payload, admin=True).json()
        assert purged_user["deleted"] is True, purged_user
        assert purged_user["purged"] is True, purged_user

    def test_undelete_user(self):
        """Delete user and then undelete them."""
        user = self._setup_user(TEST_USER_EMAIL_UNDELETE)
        self._delete(f"users/{user['id']}", admin=True)
        payload = {"deleted": "True"}
        deleted_user = self._get(f"users/{user['id']}", payload, admin=True).json()
        assert deleted_user["deleted"] is True, deleted_user
        self._post(f"users/deleted/{user['id']}/undelete", admin=True)
        undeleted_user = self._get(f"users/{user['id']}", admin=True).json()
        assert undeleted_user["deleted"] is False, undeleted_user

    def test_information(self):
        user = self._setup_user(TEST_USER_EMAIL)
        url = self.__url("information/inputs", user)
        response = get(url).json()
        self.assertEqual(response["username"], user["username"])
        self.assertEqual(response["email"], TEST_USER_EMAIL)
        put(url, data=json.dumps(dict(username="newname", email="new@email.email")))
        response = get(url).json()
        self.assertEqual(response["username"], "newname")
        self.assertEqual(response["email"], "new@email.email")
        put(url, data=json.dumps(dict(username=user["username"], email=TEST_USER_EMAIL)))
        response = get(url).json()
        self.assertEqual(response["username"], user["username"])
        self.assertEqual(response["email"], TEST_USER_EMAIL)
        put(url, data=json.dumps({"address_0|desc": "_desc"}))
        response = get(url).json()
        self.assertEqual(len(response["addresses"]), 1)
        self.assertEqual(response["addresses"][0]["desc"], "_desc")

    def test_create_api_key(self):
        user = self._setup_user(TEST_USER_EMAIL)
        user_id = user["id"]
        response = self._put(f"users/{user_id}/api_key/inputs", admin=True)
        self._assert_status_code_is_ok(response)
        self.assertEqual(response.json()["inputs"][0]["name"], "api-key")

    @skip_without_tool("cat1")
    def test_favorites(self):
        user = self._setup_user(TEST_USER_EMAIL)
        # adding a tool to favorites
        url = self._api_url(f"users/{user['id']}/favorites/tools", params=dict(key=self.master_api_key))
        put_response = put(url, data=json.dumps({"object_id": "cat1"}))
        self._assert_status_code_is_ok(put_response)
        self.assertEqual(put_response.json()["tools"][0], "cat1")
        # not implemented for workflows yet
        url = self._api_url(f"users/{user['id']}/favorites/workflows", params=dict(key=self.master_api_key))
        put_response = put(url, data=json.dumps({"object_id": "14ds68f4sda68gf46dsag4"}))
        self._assert_status_code_is(put_response, 400)
        # delete existing tool favorite
        url = self._api_url(f"users/{user['id']}/favorites/tools/cat1", params=dict(key=self.master_api_key))
        delete_response = delete(url)
        self._assert_status_code_is_ok(delete_response)
        self.assertEqual(delete_response.json()["tools"], [])
        # delete non-existing tool favorite
        url = self._api_url(
            f"users/{user['id']}/favorites/tools/madeuptoolthatdoes/not/exist/in/favs",
            params=dict(key=self.master_api_key),
        )
        delete_response = delete(url)
        self._assert_status_code_is(delete_response, 404)
        # delete non existing workflow favorite
        url = self._api_url(
            f"users/{user['id']}/favorites/workflows/1as5das5das56d465", params=dict(key=self.master_api_key)
        )
        delete_response = delete(url)
        self._assert_status_code_is(delete_response, 400)

    @skip_without_tool("cat1")
    def test_search_favorites(self):
        user, user_key = self._setup_user_get_key(TEST_USER_EMAIL)
        url = self._api_url(f"users/{user['id']}/favorites/tools", params=dict(key=user_key))
        fav_response = put(url, data=json.dumps({"object_id": "cat1"}))
        self._assert_status_code_is_ok(fav_response)
        assert "cat1" in fav_response.json()["tools"]
        url = self._api_url("tools", params=dict(q="#favs", key=user_key))
        search_response = get(url).json()
        assert "cat1" in search_response

    def __url(self, action, user):
        return self._api_url(f"users/{user['id']}/{action}", params=dict(key=self.master_api_key))

    def __show(self, user):
        return self._get(f"users/{user['id']}")

    def __update(self, user, **new_data):
        update_url = self._api_url(f"users/{user['id']}", use_key=True)
        return put(update_url, data=new_data)

    def __assert_matches_user(self, userA, userB):
        self._assert_has_keys(userB, "id", "username", "total_disk_usage")
        assert userA["id"] == userB["id"]
        assert userA["username"] == userB["username"]
