"""messages.cli tests."""

import builtins
import sys

import pytest
import conftest

import click
from click import Context
from click.testing import CliRunner

from messages import MESSAGES

import messages.cli
import messages.api
from messages.cli import check_args
from messages.cli import check_type
from messages.cli import get_body_from_file
from messages.cli import trim_args
from messages.cli import create_config_entry
from messages.cli import list_types
from messages.cli import main
from messages.email_ import Email
from messages._exceptions import UnsupportedMessageTypeError


##############################################################################
# FIXTURES
##############################################################################

class ClickConfig(Context):
    """Used to pass ctx for click applications."""
    def __init__(self): pass
    def get_usage(self): pass


@pytest.fixture()
def get_ctx():
    """Returns a mocked click.Context() object."""
    return ClickConfig()


@pytest.fixture()
def main_mocks(mocker):
    """Returns mocks for all funcs inside main()."""
    args_mk = mocker.patch.object(messages.cli, 'check_args')
    type_mk = mocker.patch.object(messages.cli, 'check_type')
    list_mk = mocker.patch.object(messages.cli, 'list_types')
    body_mk = mocker.patch.object(messages.cli, 'get_body_from_file')
    config_mk = mocker.patch.object(messages.cli, 'create_config_entry')
    send_mk = mocker.patch.object(messages.cli, 'send')
    return (args_mk, type_mk, list_mk, body_mk, config_mk, send_mk)


##############################################################################
# TESTS: cli.check_args
##############################################################################

def test_check_args_withArgs(get_ctx):
    """
    GIVEN a call to messages via the CLI
    WHEN check_args is called with args given
    THEN assert no errors occur
    """
    ctx = get_ctx
    kwds = {'test': 1}
    check_args(ctx, kwds)


def test_check_args_withNoArgs(get_ctx, mocker):
    """
    GIVEN a call to messages via the CLI
    WHEN check_args is called with NO args given
    THEN assert click.echo and sys.exit are called
    """
    ctx = get_ctx
    kwds = {}
    echo_mk = mocker.patch('click.echo')
    with pytest.raises(SystemExit) as sysext:
        check_args(ctx, kwds)
        assert echo_mk.call_count == 2
        assert sysext.code == 0


##############################################################################
# TESTS: cli.check_type
##############################################################################

def test_check_type_normal():
    """
    GIVEN a call to messages via the CLI
    WHEN a valid message type is given
    THEN assert no errors occur
    """
    kwds = {'type': 'email'}
    check_type(kwds)


def test_check_type_badType():
    """
    GIVEN a call to messages via the CLI
    WHEN an invalid message type is given
    THEN assert UnsupportedMessageTypeError is raised
    """
    kwds = {'type': 'badType'}
    with pytest.raises(UnsupportedMessageTypeError):
        check_type(kwds)


##############################################################################
# TESTS: cli.get_body_from_file
##############################################################################

@conftest.travis
def test_get_body_from_file(tmpdir):
    """
    GIVEN a call to messages via the CLI
    WHEN a message is specified by filename
    THEN assert the file contents are read and set into the message body
        * this uses the tmpdir pytest built-in fixture to create temporary
          directory and file for the test
    """
    msg_file = tmpdir.join('msg.txt')
    msg_file.write('This is the message to send!')
    kwds = {'body': None, 'file': msg_file}
    body = get_body_from_file(kwds)
    assert kwds == {'body': 'This is the message to send!', 'file': None}


##############################################################################
# TESTS: cli.trim_args
##############################################################################

def test_trim_args_rejectedKV():
    """
    GIVEN a call to messages via the CLI
    WHEN trim_args is called on the CLI args
    THEN assert the correct args are removed
    """
    kwds = {'type': 'email', 'arg1': None, 'arg2': (), 'arg3': 'valid'}
    kwargs = trim_args(kwds)
    assert kwargs == {'arg3': 'valid'}


def test_trim_args_ListItems():
    """
    GIVEN a call to messages via the CLI
    WHEN trim_args is called on the CLI args
    THEN assert values with keys to/cc/bcc/attach are returned as a list
        instead of the tuple generated by the click package
    """
    kwds = {'to': ('me@here.com',), 'cc': ('her@there.com',),
            'bcc': ('him@there.com', 'her@there.com'), 'attachments': ('file1',)}
    kwargs = trim_args(kwds)
    assert kwargs == {'to': ['me@here.com'], 'cc': ['her@there.com'],
            'bcc': ['him@there.com', 'her@there.com'], 'attachments': ['file1']}


##############################################################################
# TESTS: cli.create_config_entry
##############################################################################

def test_create_config_entry_yes_email(capsys, mocker):
    """
    GIVEN a call to messages via the CLI
    WHEN create_config_entry is called with a valid message type with user
        input=yes
    THEN assert correct output is printed and create_config is called
    """
    input_mk = mocker.patch.object(builtins, 'input', return_value='y')
    create_cfg_mk = mocker.patch.object(messages.cli, 'create_config')
    create_config_entry('email')
    out, err = capsys.readouterr()
    assert 'You will need the following information to configure: email' in out
    assert 'from_' in out
    assert 'server' in out
    assert 'port' in out
    assert 'password' in out
    assert input_mk.call_count == 2
    assert create_cfg_mk.call_count == 1


def test_create_config_entry_yes_twilio(capsys, mocker):
    """
    GIVEN a call to messages via the CLI
    WHEN create_config_entry is called with a valid message type with user
        input=yes
    THEN assert correct output is printed and create_config is called
    """
    input_mk = mocker.patch.object(builtins, 'input', return_value='y')
    create_cfg_mk = mocker.patch.object(messages.cli, 'create_config')
    create_config_entry('twilio')
    out, err = capsys.readouterr()
    assert 'You will need the following information to configure: twilio' in out
    assert 'from_' in out
    assert 'acct_sid' in out
    assert 'auth_token' in out
    assert input_mk.call_count == 2
    assert create_cfg_mk.call_count == 1


def test_create_config_entry_yes_slackwebhook(capsys, mocker):
    """
    GIVEN a call to messages via the CLI
    WHEN create_config_entry is called with a valid message type with user
        input=yes
    THEN assert correct output is printed and create_config is called
    """
    input_mk = mocker.patch.object(builtins, 'input', return_value='y')
    create_cfg_mk = mocker.patch.object(messages.cli, 'create_config')
    create_config_entry('slackwebhook')
    out, err = capsys.readouterr()
    assert 'You will need the following information to configure: slackwebhook' in out
    assert 'from_' in out
    assert 'url' in out
    assert input_mk.call_count == 2
    assert create_cfg_mk.call_count == 1


def test_create_config_entry_yes_tgram(capsys, mocker):
    """
    GIVEN a call to messages via the CLI
    WHEN create_config_entry is called with a valid message type with user
        input=yes
    THEN assert correct output is printed and create_config is called
    """
    input_mk = mocker.patch.object(builtins, 'input', return_value='y')
    create_cfg_mk = mocker.patch.object(messages.cli, 'create_config')
    create_config_entry('telegrambot')
    out, err = capsys.readouterr()
    assert 'You will need the following information to configure: telegrambot' in out
    assert 'chat_id' in out
    assert 'bot_token' in out
    assert input_mk.call_count == 2
    assert create_cfg_mk.call_count == 1


def test_create_config_entry_no(capsys, mocker):
    """
    GIVEN a call to messages via the CLI
    WHEN create_config_entry is called with a valid message type with user
        input=no
    THEN assert create_config is not called
    """
    input_mk = mocker.patch.object(builtins, 'input', return_value='n')
    create_cfg_mk = mocker.patch.object(messages.cli, 'create_config')
    create_config_entry('email')
    out, err = capsys.readouterr()
    assert input_mk.call_count == 1
    assert create_cfg_mk.call_count == 0


##############################################################################
# TESTS: cli.list_types
##############################################################################

def test_list_types(capsys):
    """
    GIVEN a call to messages vis the CLI
    WHEN list_types() is called
    THEN assert the proper output prints
    """
    list_types()
    out, err = capsys.readouterr()
    assert 'Available message types:' in out
    for m in MESSAGES:
        assert m in out
    assert '' in err


##############################################################################
# TESTS: cli.main
##############################################################################

def test_main_listTypes(main_mocks):
    """
    GIVEN a call to messages via the CLI
    WHEN args = ['-T']
    THEN assert only certain functions are called
    """
    args_mk, type_mk, list_mk, body_mk, config_mk, send_mk = main_mocks
    runner = CliRunner()
    runner.invoke(main, ['-T'], catch_exceptions=False)
    assert args_mk.call_count == 1
    assert list_mk.call_count == 1
    assert type_mk.call_count == 0
    assert body_mk.call_count == 0
    assert config_mk.call_count == 0
    assert send_mk.call_count == 0


def test_main_configure(main_mocks):
    """
    GIVEN a call to messages via the CLI
    WHEN args = ['-C']
    THEN assert only certain functions are called
    """
    args_mk, type_mk, list_mk, body_mk, config_mk, send_mk = main_mocks
    runner = CliRunner()
    runner.invoke(main, ['-C'], catch_exceptions=False)
    assert args_mk.call_count == 1
    assert list_mk.call_count == 0
    assert type_mk.call_count == 0
    assert body_mk.call_count == 0
    assert config_mk.call_count == 1
    assert send_mk.call_count == 0


def test_main_configure_and_listTypes(main_mocks):
    """
    GIVEN a call to messages via the CLI
    WHEN args = ['-C', '-T']
    THEN assert only certain functions are called
    """
    args_mk, type_mk, list_mk, body_mk, config_mk, send_mk = main_mocks
    runner = CliRunner()
    runner.invoke(main, ['-C', '-T'], catch_exceptions=False)
    assert args_mk.call_count == 1
    assert list_mk.call_count == 1
    assert type_mk.call_count == 0
    assert body_mk.call_count == 0
    assert config_mk.call_count == 0
    assert send_mk.call_count == 0


def test_main_MessageFromFile(main_mocks):
    """
    GIVEN a call to messages via the CLI
    WHEN args = ['email', -M', './somefile']
    THEN assert only certain functions are called
    """
    args_mk, type_mk, list_mk, body_mk, config_mk, send_mk = main_mocks
    runner = CliRunner()
    runner.invoke(main, ['email', '-M', './somefile'], catch_exceptions=False)
    assert args_mk.call_count == 1
    assert list_mk.call_count == 0
    assert type_mk.call_count == 1
    assert body_mk.call_count == 1
    assert config_mk.call_count == 0
    assert send_mk.call_count == 1


def test_main_MessageFromFile_noType(main_mocks, mocker):
    """
    GIVEN a call to messages via the CLI
    WHEN args = [-M', './somefile']
    THEN assert only certain functions are called
    """
    args_mk, type_mk, list_mk, body_mk, config_mk, send_mk = main_mocks
    echo_mk = mocker.patch('click.echo')
    runner = CliRunner()
    runner.invoke(main, ['-M', './somefile'], catch_exceptions=False)
    assert args_mk.call_count == 1
    assert list_mk.call_count == 1
    assert type_mk.call_count == 0
    assert body_mk.call_count == 1
    assert config_mk.call_count == 0
    assert send_mk.call_count == 0
    assert echo_mk.call_count == 2
