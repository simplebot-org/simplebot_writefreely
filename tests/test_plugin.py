class TestPlugin:
    def test_login(self, mocker, requests_mock) -> None:
        self._requests_mock(requests_mock)
        msgs = mocker.get_replies("/login https://write.as user password")
        assert len(msgs) == 3

        msg = mocker.get_one_reply("/login https://write.as token")
        assert "❌" in msg.text

        msgs = mocker.get_replies(
            "/login https://write.as token", addr="test@example.com"
        )
        assert len(msgs) == 3

    def test_logout(self, mocker, requests_mock) -> None:
        self._requests_mock(requests_mock)
        msg = mocker.get_one_reply("/logout")
        assert "❌" in msg.text

        mocker.get_replies("/login https://write.as token")
        msg = mocker.get_one_reply("/logout")
        assert "✔" in msg.text

    def test_filter(self, mocker, requests_mock) -> None:
        self._requests_mock(requests_mock)
        for msg in mocker.get_replies("/login https://write.as token"):
            if msg.chat.is_group():
                chat = msg.chat
                break
        msgs = mocker.get_replies("blog post", filters="simplebot_writefreely")
        assert not msgs

        msg = mocker.get_one_reply(
            "blog post", group=chat, filters="simplebot_writefreely"
        )
        assert "post-slug" in msg.text

        msg = mocker.get_one_reply(
            "# Post title\nArticle's body", group=chat, filters="simplebot_writefreely"
        )
        assert "post-slug" in msg.text

    @staticmethod
    def _requests_mock(requests_mock) -> None:
        data: dict = {"data": {"access_token": "test-token"}}
        requests_mock.post("https://write.as/api/auth/login", json=data)
        data = {
            "data": [
                {
                    "title": "Blog Title 1",
                    "alias": "test-blog-1",
                    "description": "Blog description 1",
                },
                {
                    "title": "Blog Title 2",
                    "alias": "test-blog-2",
                    "description": "Blog description 2",
                },
            ]
        }
        requests_mock.get("https://write.as/api/me/collections", json=data)

        requests_mock.delete("https://write.as/api/auth/me")  # logout

        data = {
            "data": {
                "collection": {"url": "https://write.as"},
                "slug": "post-slug",
            }
        }
        requests_mock.post(
            "https://write.as/api/collections/test-blog-1/posts", json=data
        )
        requests_mock.post(
            "https://write.as/api/collections/test-blog-2/posts", json=data
        )
