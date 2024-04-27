import pytest
import os
import argparse
from steamCloudSaveDownloader.args import args


class TestArgs:
    def test_config_file(self, tmp_path):
        test_config = tmp_path / "test.conf"
        with open(test_config, "w") as f:
            f.write('\n')
        result = args().parse(["-f", str(test_config)])
        assert result['conf'] == test_config

    def test_data_dir(self, tmp_path):
        result = args().parse(["-d", str(tmp_path)])
        assert result['save_dir'] == str(tmp_path)

    def test_auth_single_arg(self):
        with pytest.raises(SystemExit):
            args().parse(["-a"])

    def test_auth_correct_arg(self):
        result = args().parse(["-a", "test_account"])
        assert result['auth'] == "test_account"

    def test_stored_empty(self):
        result = args().parse(["-s"])
        assert result['stored'] is None

    def test_stored_appid(self):
        result = args().parse(["-s", "123,456"])
        assert result['stored'] == [123, 456]

    def test_combo(self, tmp_path):
        test_config = tmp_path / "test.conf"
        with open(test_config, "w") as f:
            f.write('\n')
        result = args().parse(["-f", str(test_config), "-d", str(tmp_path), "-l", "3", "-r", "5"])
        assert result['conf'] == test_config
        assert result['save_dir'] == str(tmp_path)
        assert result['log_level'] == 3
        assert result['rotation'] == 5
