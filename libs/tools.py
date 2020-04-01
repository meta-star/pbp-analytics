import sys
import time
import traceback

"""
    Copyright (c) 2019 SuperSonic(https://randychen.tk)

    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. 2.0. If a copy of the MPL was not distributed with this
    file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


class Tools:
    @staticmethod
    def get_time(time_format="%b %d %Y %H:%M:%S %Z"):
        """

        :param time_format:
        :return:
        """
        time_ = time.localtime(time.time())
        return time.strftime(time_format, time_)

    @staticmethod
    def error_report():
        """
        Report errors as tuple
        :return: tuple
        """
        err1, err2, err3 = sys.exc_info()
        traceback.print_tb(err3)
        tb_info = traceback.extract_tb(err3)
        filename, line, func, text = tb_info[-1]
        error_info = "occurred in\n{}\n\non line {}\nin statement {}".format(filename, line, text)
        return err1, err2, err3, error_info
