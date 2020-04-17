import base64
import os
import pickle
import time
import uuid
from hashlib import sha256
from multiprocessing import Process, Queue

import cv2
import numpy
from skimage.metrics import structural_similarity

from .browser import BrowserRender, BrowserAgent

"""
    Copyright (c) 2020 Star Inc.(https://starinc.xyz)

    This Source Code Form is subject to the terms of the Mozilla Public
    License, v. 2.0. If a copy of the MPL was not distributed with this
    file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


class Image:
    """
    Handle images for PageView
    """

    def __init__(self, pbp_handle):
        self.capture_handle = WebCapture(pbp_handle.cfg["WebCapture"])
        self.data_control = pbp_handle.data_control

    async def capture(self, url: str):
        """
        Capture Web Page by URL
        :param url: URL to capture
        :return: string hashed and NumPy Array
        """
        cache_file = "{}.png".format(
            uuid.uuid5(uuid.NAMESPACE_URL, url).hex
        )
        layout_path = self.capture_handle.get_page_image(
            target_url=url,
            output_image=cache_file
        )
        image_num_array = None
        count, timeout = 0, 5
        while image_num_array is None:
            assert count < timeout, "Timeout while reading image_num_array"
            image_num_array = self.capture_handle.image_object(layout_path)
            time.sleep(1)
            count += 1
        hash_object = sha256(image_num_array)
        self.capture_handle.delete_page_image(cache_file)
        return hash_object.hexdigest(), image_num_array

    async def signature(self, hex_digest: str):
        """
        Match PageView signature from database
        :param hex_digest: string hashed
        :return: URL or NoneType
        """
        return self.data_control.find_page_by_view_signature(hex_digest)

    async def rank(self, target_num_array: str):
        """
        To rank URL not registered if it same/similar to someone in trustlist.
        :param target_num_array: NumPy Array
        :return: URLs that similar to the target
        """
        q = Queue()
        thread = None

        def _compare(sample: dict):
            """
            Child function, rank sample of URL with samples in trustlist
            :param sample: NumPy Array
            :return:
            """
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

        trust_samples = self.data_control.get_view_narray_from_trustlist()
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

    def __init__(self, config: dict):
        self.capture_browser = config["capture_browser"]
        self.cache_path = config["cache_path"]
        self.browser = config["capture_type"]

        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

    @staticmethod
    def __set_browser_simulation(type_id: str):
        """
        Set Browser Simulation by ID
        :param type_id: Type ID
        :return: class object
        """
        return {
            '1': BrowserRender,
            '2': BrowserAgent
        }[type_id]

    def get_page_image(self, target_url: str, output_image: str = 'out.png'):
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

    def delete_page_image(self, output_image: str = 'out.png'):
        """
        To delete the image of the URL you provided.
        :param output_image: Output path (optional)
        :return: bool
        """
        layout_path = os.path.join(self.cache_path, output_image)
        if os.path.isfile(layout_path):
            os.remove(layout_path)

    @staticmethod
    def image_object(path: str):
        """
        Create NumPy Array
        :param path: The Image Path
        :return: NumPy Array
        """
        return cv2.imread(path, 0)

    @staticmethod
    def image_object_from_b64(b64_string: bytes):
        """
        Import NumPy Array by base64
        :param b64_string: base64 NumPy Array dumped
        :return: NumPy Array
        """
        string = base64.b64decode(b64_string)
        return pickle.loads(string)

    @staticmethod
    def image_compare(img1: numpy.numarray, img2: numpy.numarray):
        """
        To compare image using structural similarity index
        :param img1: Image object
        :param img2: Image object
        :return: float of the similar lever
        """
        return structural_similarity(img1, img2, multichannel=True)
