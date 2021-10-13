import signal
import subprocess
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

WIDTH = 1280
HEIGHT = 720
DISPLAY = ":0"
USERNAME = "User"


def set_display(display):
    os.environ["DISPLAY"] = display


def kill(process):
    os.kill(process.pid, signal.SIGKILL)
    process.wait()


class ZoomRecorder:
    def __init__(self, url):
        self.url = url
        self.__start_xvfb()
        self.__start_pulse_audio()
        self.__setup_driver()

    def record(self):
        self.__start_ffmpeg()
        self.__start_meeting()

    def stop(self):
        self.driver.stop_client()
        self.__stop_ffmpeg()
        self.__stop_xvfb()

    def __start_ffmpeg(self):
        self.ffmepg = subprocess.Popen([
            "ffmpeg",
            "-video_size", f'{WIDTH}x{HEIGHT}',
            "-framerate", "25",
            "-f", "x11grab",
            "-i", DISPLAY,
            # "-f", "alsa",
            # "-ac", "2",
            # "-i", "hw:0",
            "-y",
            "output.mp4"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def __start_xvfb(self):
        self.xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{WIDTH}x{HEIGHT}x24"], stdout=subprocess.PIPE)

    def __start_pulse_audio(self):
        os.system(f'DISPLAY={DISPLAY} pulseaudio --start')

    def __setup_driver(self):
        set_display(DISPLAY)
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)
        self.driver.get(self.url)
        self.driver.set_window_size(WIDTH, HEIGHT)

    def __stop_xvfb(self):
        kill(self.xvfb)

    def __stop_ffmpeg(self):
        self.ffmepg.communicate(b'q')
        self.ffmepg.wait()

    def __start_meeting(self):
        self.click_when_clickable((By.ID, "onetrust-accept-btn-handler"))
        self.click_when_clickable((By.XPATH, "//div[@role='button' and contains(text(), 'Launch Meeting')]"))
        self.driver.find_element_by_xpath("//a[contains(text(), 'Join from Your Browser')]").click()
        self.driver.find_element_by_id("inputname").send_keys(USERNAME)
        self.driver.find_element_by_id("joinBtn").click()

        meeting_invalid_elements = self.driver.find_elements_by_xpath(
            "//span[@class='error-message' and contains(text(), 'This meeting link is invalid')]")

        if len(meeting_invalid_elements) > 0 and meeting_invalid_elements[0].is_displayed():
            raise Exception("Meeting link is invalid")

        self.driver.find_element_by_id("wc_agree1").click()

    def click_when_clickable(self, locator):
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(locator)).click()
