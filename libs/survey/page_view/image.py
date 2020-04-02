import base64
import os
import pickle
from hashlib import sha256
from multiprocessing import Process, Queue

import cv2
from skimage.metrics import structural_similarity

from .browser import BrowserRender, BrowserAgent

"""
    Copyright (c) 2019 SuperSonic(https://randychen.tk)

    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. 2.0. If a copy of the MPL was not distributed with this
    file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


class Image:
    """

    """

    def __init__(self, pbp_capture):
        self.capture_handle = WebCapture(pbp_capture.cfg["WebCapture"])
        self.data_control = pbp_capture.data_control

    async def capture(self, url):
        """

        :param url:
        :return:
        """
        url_hash = sha256(url.encode("utf-8"))
        layout_path = self.capture_handle.get_page_image(
            target_url=url,
            output_image="{}.png".format(
                url_hash.hexdigest()
            )
        )
        image_num_array = self.capture_handle.image_object(layout_path)
        hash_object = sha256(image_num_array)
        return hash_object.hexdigest(), image_num_array

    async def signature(self, hex_digest):
        """

        :param hex_digest:
        :return:
        """
        query = self.data_control.find_page_by_view_signature(hex_digest)
        if query:
            return query[0]

    async def rank(self, target_type, target_num_array):
        """

        :param target_type:
        :param target_num_array:
        :return:
        """
        q = Queue()
        thread = None

        def _compare(sample):
            origin_sample = self.capture_handle.image_object_from_b64(
                sample["target_view_narray"].encode("utf-8")
            )
            q.put([
                sample["url"],
                self.capture_handle.image_compare(
                    target_num_array,
                    origin_sample
                )
            ])

        trust_samples = self.data_control.get_view_narray_from_trustlist_with_target_type(target_type)
        for record in trust_samples:
            thread = Process(
                target=_compare,
                args=(record,)
            )
            thread.start()

        if thread:
            thread.join()

        for _ in trust_samples:
            yield q.get()


class WebCapture:
    """
    To take screenshot for PBP.
    """

    def __init__(self, config):
        self.capture_browser = config["capture_browser"]
        self.cache_path = config["cache_path"]
        self.browser = config["capture_type"]

        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

    @staticmethod
    def __set_browser_simulation(type_id):
        """
        Set Browser Simulation by ID
        :param type_id: Type ID
        :return: class object
        """
        return {
            '1': BrowserRender,
            '2': BrowserAgent
        }[type_id]

    def get_page_image(self, target_url, output_image='out.png'):
        """
        To get the image of the URL you provided.
        :param target_url: The target URL
        :param output_image: Output path (optional)
        :return: bool
        """
        layout_path = os.path.join(self.cache_path, output_image)
        simulation = self.__set_browser_simulation(self.browser)(self.capture_browser)
        if os.path.isfile(layout_path):
            os.remove(layout_path)
        simulation.capture(target_url, layout_path)
        simulation.close()
        return layout_path

    @staticmethod
    def image_object(path):
        """
        Create NumPy Array
        :param path: The Image Path
        :return: NumPy Array
        """
        return cv2.imread(path, 0)

    @staticmethod
    def image_object_from_b64(b64_string):
        """
        Import NumPy Array by base64
        :param b64_string: base64 NumPy Array dumped
        :return: NumPy Array
        """
        string = base64.b64decode(b64_string)
        return pickle.loads(string)

    @staticmethod
    def image_compare(img1, img2):
        """
        To compare image using structural similarity index
        :param img1: Image object
        :param img2: Image object
        :return: float of the similar lever
        """
        return structural_similarity(img1, img2, multichannel=True)
