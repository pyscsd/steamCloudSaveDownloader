from steamCloudSaveDownloader.notifier import notifier
from steamCloudSaveDownloader.notifier import notify_method
import os
import sys
import pytest

class TestNotifier:
    @pytest.mark.skipif(sys.platform != 'linux', reason="Not Linux")
    def test_shell(self, tmp_path):
        test_script = tmp_path / "test.sh"
        output_txt = tmp_path / "output.txt"
        with open(test_script, "w") as f:
            f.write(f'#!/bin/sh\necho $1 > {output_txt}')
        os.chmod(test_script, 0o744)
        notifier_ = \
            notifier.create_instance(
                method='Script',
                path=str(test_script))
        notifier_.send("achaka", ok=True)
        with open(output_txt, "r") as f:
            content = f.read()
            assert content == "[scsd-Version Unknown] :white_check_mark: achaka\n"
