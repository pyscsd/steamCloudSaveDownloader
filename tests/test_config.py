import pytest
from steamCloudSaveDownloader.config import config
import steamCloudSaveDownloader.err as err

class TestConfig:
    def test_unknown_section(self, tmp_path, caplog):
        test_config = tmp_path / "test.conf"
        with open(test_config, "w") as f:
            f.write('[Definitely Unknown]\n')
        config_ = config(file=test_config)
        config_.get_conf()

        assert len(caplog.records) == 1
        assert 'Definitely Unknown' in caplog.text

    def test_unknown_option(self, tmp_path, caplog):
        test_config = tmp_path / "test.conf"
        with open(test_config, "w") as f:
            f.write('[General]\ndefinitely_unknown_option = value\n')
        config_ = config(file=test_config)
        config_.get_conf()

        assert len(caplog.records) == 1
        assert 'definitely_unknown' in caplog.text
        assert 'General' in caplog.text

    def test_invalid_type(self, tmp_path):
        test_config = tmp_path / "test.conf"
        with open(test_config, "w") as f:
            f.write('[Rotation]\nrotation = value\n')
        config_ = config(file=test_config)
        with pytest.raises(err.err) as e:
            config_.get_conf()
        assert e.value.num() == err.err_enum.INVALID_CONFIG
        assert 'should have type' in e.value.additional_info

    def test_invalid_enumeration(self, tmp_path):
        test_config = tmp_path / "test.conf"
        with open(test_config, "w") as f:
            f.write('[General]\n2fa = value\n')
        config_ = config(file=test_config)
        with pytest.raises(err.err) as e:
            config_.get_conf()
        assert e.value.num() == err.err_enum.INVALID_CONFIG
        assert 'should have these values' in e.value.additional_info

    def test_check_list(self, tmp_path):
        test_config = tmp_path / "test.conf"

        with open(test_config, "w") as f:
            f.write('[Target]\nlist = \n')
        assert config(file=test_config).get_conf()['Target']['list'] == []

        with open(test_config, "w") as f:
            f.write('[Target]\nlist = 123\n')
        assert config(file=test_config).get_conf()['Target']['list'] == [123]
        with open(test_config, "w") as f:
            f.write('[Target]\nlist = 123,456\n')
        assert config(file=test_config).get_conf()['Target']['list'] == [123, 456]

        with open(test_config, "w") as f:
            f.write('[Target]\nlist = 123,\n')
        assert config(file=test_config).get_conf()['Target']['list'] == [123]

        with open(test_config, "w") as f:
            f.write('[Target]\nlist = 123 , 412\n')
        assert config(file=test_config).get_conf()['Target']['list'] == [123, 412]

    def test_arg_override(self, tmp_path):
        test_arg = {
            'log_level': 17,
            'save_dir': 'test',
            'rotation': 3939
        }
        test_config = tmp_path / "test.conf"
        with open(test_config, "w") as f:
            f.write('[Rotation]\nrotation = 39\n[Log]\nlog_level = 3939')
        result = config(file=test_config).load_from_arg(test_arg)
        assert result['Log']['log_level'] == 17
        assert result['Rotation']['rotation'] == 3939

    def test_comobo(self, tmp_path):
        # Check optional value
        test_config = tmp_path / "test.conf"
        with open(test_config, "w") as f:
            f.write('[Log]\nlog_level = 5\n[Notifier]\nnotify_if_no_change=true')
        result = config(file=test_config).get_conf()
        assert result['Log']['log_level'] == 5
        assert result['Notifier']['notify_if_no_change'] == True
