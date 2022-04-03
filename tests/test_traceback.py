def test_should_check_rich_traceback_handler_is_correctly_called(runner, mocker):
    install_mock = mocker.patch('rich.traceback.install')
    # must do the import here to avoid the function "install" to be called before being mocked
    from ws.main import cli

    runner.invoke(cli)

    install_mock.assert_called_once_with(show_locals=True)
