import asyncio
import multiprocessing
import time

from .tools import Tools

"""
    Copyright (c) 2020 Star Inc.(https://starinc.xyz)

    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. 2.0. If a copy of the MPL was not distributed with this
    file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


class Cron:
    def __init__(self, pbp_handle):
        """
        Create a child process as the scheduler

        :param pbp_handle: Analytics object
        """
        self.handle = pbp_handle
        self.task = None

    def start(self):
        """
        Start scheduler

        :return:
        """
        self.task = CronTimer(self.handle)
        self.task.start()

    def stop(self):
        """
        Stop scheduler

        :return:
        """
        if self.task:
            self.task.terminate()


class CronTimer(multiprocessing.Process):
    def __init__(self, pbp_handle):
        """
        Scheduler for database

        :param pbp_handle: Analytics object
        """
        multiprocessing.Process.__init__(self)
        self.handle = pbp_handle
        self.last_time = -1

    def run(self):
        """
        Task of Scheduler to check databases

        :return:
        """
        while True:
            if time.localtime().tm_hour != self.last_time:
                try:
                    threads = Update(self.handle)
                    threads.start()
                    threads.join()
                    print(
                        Tools.get_time(),
                        "[Update] Database was refreshed."
                    )
                except:
                    error_report = Tools.error_report()
                    Tools.logger(error_report)
                if self.last_time == -1:
                    Tools.set_ready(True)
                self.last_time = time.localtime().tm_hour


class Update(multiprocessing.Process):
    def __init__(self, pbp_handle):
        """
        Action to update databases

        :param pbp_handle: Analytics object
        """
        multiprocessing.Process.__init__(self)
        self.handle = pbp_handle

    def run(self):
        """
        Action to checkout

        :return:
        """
        asyncio.run(self.handle.gen_sample())
        self.handle.data_control.clean_result_cache()
        self.handle.update_blacklist_from_phishtank()
