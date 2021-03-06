import pytest
from requests import Response
from requests.exceptions import HTTPError

from py42.exceptions import Py42BadRequestError
from py42.exceptions import Py42CloudAliasLimitExceededError
from py42.services.detectionlists.user_profile import DetectionListUserService
from py42.services.users import UserService


CLOUD_ALIAS_LIMIT_EXCEEDED_ERROR_MESSAGE = """{
"pop-bulletin": {
"type$": "com.code42.detectionlistmanagement.DetectionListMessages.ValidationError",
"text$": "Command or Query is invalid: Cloud usernames must be less than or equal to 2",
"details": [],
"reason": "Cloud usernames must be less than or equal to 2"
}
}"""


class TestDetectionListUserClient(object):
    @pytest.fixture
    def mock_user_client(self, mock_connection, user_context, py42_response):
        user_client = UserService(mock_connection)
        py42_response.text = '{"username":"username"}'
        mock_connection.get.return_value = py42_response
        return user_client

    @pytest.fixture
    def mock_get_by_id_fails(self, mocker, mock_connection):
        response = mocker.MagicMock(spec=Response)
        response.status_code = 400
        exception = mocker.MagicMock(spec=HTTPError)
        exception.response = response
        mock_connection.post.side_effect = Py42BadRequestError(exception)
        return mock_connection

    @pytest.fixture
    def mock_user_client_raises_exception(
        self, mocker, mock_connection, user_context, py42_response
    ):
        user_client = UserService(mock_connection)
        response = mocker.MagicMock(spec=Response)
        response.status_code = 400
        exception = mocker.MagicMock(spec=HTTPError)
        exception.response = response
        mock_connection.post.side_effect = Py42BadRequestError(exception)
        return user_client

    @pytest.fixture
    def mock_user_client_error_on_adding_cloud_aliases(
        self, mocker, mock_connection, user_context, py42_response
    ):
        user_client = UserService(mock_connection)
        response = mocker.MagicMock(spec=Response)
        response.status_code = 400
        response.text = CLOUD_ALIAS_LIMIT_EXCEEDED_ERROR_MESSAGE
        exception = mocker.MagicMock(spec=HTTPError)
        exception.response = response
        mock_connection.post.side_effect = Py42BadRequestError(exception)
        return user_client

    def test_create_posts_expected_data(
        self, mock_connection, user_context, mock_user_client
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.create("942897397520289999")

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/create"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["userName"] == "942897397520289999"
            and posted_data["riskFactors"] == []
            and posted_data["cloudUsernames"] == []
            and posted_data["notes"] == ""
        )

    def test_get_posts_expected_data(
        self, mock_connection, user_context, mock_user_client
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.get("942897397520289999")

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/getbyusername"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["username"] == "942897397520289999"
        )

    def test_get_by_id_posts_expected_data(
        self, mock_connection, user_context, mock_user_client
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.get_by_id("942897397520289999")

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/getbyid"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["userId"] == "942897397520289999"
        )

    def test_update_notes_posts_expected_data(
        self, mock_connection, user_context, mock_user_client
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.update_notes("942897397520289999", "Test")

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/updatenotes"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["userId"] == "942897397520289999"
            and posted_data["notes"] == "Test"
        )

    @pytest.mark.parametrize("tags", ["test_tag", ["test_tag"]])
    def test_add_risk_tag_posts_expected_data(
        self, mock_connection, user_context, mock_user_client, tags
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.add_risk_tags("942897397520289999", tags)

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/addriskfactors"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["userId"] == "942897397520289999"
            and posted_data["riskFactors"] == ["test_tag"]
        )

    @pytest.mark.parametrize("tags", ["test_tag", ["test_tag"]])
    def test_remove_risk_tag_posts_expected_data(
        self, mock_connection, user_context, mock_user_client, tags
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.remove_risk_tags("942897397520289999", u"Test")

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/removeriskfactors"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["userId"] == "942897397520289999"
            and posted_data["riskFactors"] == ["Test"]
        )

    def test_add_cloud_alias_posts_expected_data(
        self, mock_connection, user_context, mock_user_client
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.add_cloud_alias("942897397520289999", u"Test")

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/addcloudusernames"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["userId"] == "942897397520289999"
            and posted_data["cloudUsernames"] == ["Test"]
        )

    def test_remove_cloud_alias_posts_expected_data(
        self, mock_connection, user_context, mock_user_client
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.remove_cloud_alias("942897397520289999", u"Test")

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/removecloudusernames"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["userId"] == "942897397520289999"
            and posted_data["cloudUsernames"] == ["Test"]
        )

    def test_refresh_posts_expected_data(
        self, mock_connection, user_context, mock_user_client
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection, user_context, mock_user_client
        )
        detection_list_user_client.refresh("942897397520289999")

        posted_data = mock_connection.post.call_args[1]["json"]
        assert mock_connection.post.call_count == 1
        assert mock_connection.post.call_args[0][0] == "v2/user/refresh"
        assert (
            posted_data["tenantId"] == user_context.get_current_tenant_id()
            and posted_data["userId"] == "942897397520289999"
        )

    def test_add_cloud_alias_limit_raises_custom_error_on_limit(
        self,
        mock_connection,
        user_context,
        mock_user_client_error_on_adding_cloud_aliases,
    ):
        detection_list_user_client = DetectionListUserService(
            mock_connection,
            user_context,
            mock_user_client_error_on_adding_cloud_aliases,
        )
        with pytest.raises(Py42CloudAliasLimitExceededError) as err:
            detection_list_user_client.add_cloud_alias("942897397520289999", "Test")
        assert "Cloud alias limit exceeded." in str(err.value)
