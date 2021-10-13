import os
import subprocess
import time

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

WIDTH = 1280
HEIGHT = 720
DISPLAY = ":0"
USERNAME = "User"


def set_display(display):
    os.environ["DISPLAY"] = display


def set_sink():
    os.system("pacmd set-default-source v1.monitor")


def kill(process):
    process.kill()
    process.wait()


class ZoomClient:
    def __init__(self, url):
        self.url = url

        options = Options()
        options.set_preference("permissions.default.microphone", False)
        options.set_preference("media.navigator.permission.disabled", True)

        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(10)
        self.driver.set_window_size(WIDTH, HEIGHT)

    def join_meeting(self):
        self.driver.get(self.url)
        self.accept_cookies()
        self.click_launch_meeting()
        self.click_join_from_browser()
        self.input_user_name_and_join()
        self.check_for_invalid_meeting()
        self.agree_terms()
        self.wait_for_loading_screen()
        self.join_audio()
        self.mute()

    def mute(self):
        mute_button = self.driver.find_element_by_xpath(
            "//button[contains(@class,'join-audio-container__btn') and contains(i/@class, 'unmuted')]")

        ActionChains(self.driver) \
            .move_by_offset(100, 100) \
            .move_to_element(mute_button) \
            .click() \
            .perform()

    def join_audio(self):
        ActionChains(self.driver) \
            .move_by_offset(100, 100) \
            .move_to_element(self.driver.find_element_by_class_name('join-audio-by-voip__join-btn')) \
            .click() \
            .perform()

    def wait_for_loading_screen(self):
        self.wait().until_not(EC.presence_of_element_located((By.CLASS_NAME, "loading-layer")))

    def agree_terms(self):
        self.driver.find_element_by_id("wc_agree1").click()

    def check_for_invalid_meeting(self):
        meeting_invalid_elements = self.driver.find_elements_by_xpath(
            "//span[@class='error-message' and contains(text(), 'This meeting link is invalid')]")
        if len(meeting_invalid_elements) > 0 and meeting_invalid_elements[0].is_displayed():
            raise Exception("Meeting link is invalid")

    def input_user_name_and_join(self):
        self.driver.find_element_by_id("inputname").send_keys(USERNAME)
        self.driver.find_element_by_id("joinBtn").click()

    def click_join_from_browser(self):
        self.driver.find_element_by_xpath("//a[contains(text(), 'Join from Your Browser')]").click()

    def click_launch_meeting(self):
        self.click_when_clickable((By.XPATH, "//div[@role='button' and contains(text(), 'Launch Meeting')]"))

    def accept_cookies(self):
        self.click_when_clickable((By.ID, "onetrust-accept-btn-handler"))
        self.wait().until_not(EC.visibility_of_element_located((By.ID, "onetrust-accept-btn-handler")))

    def move_mouse(self, x=100, y=100):
        ActionChains(self.driver) \
            .move_by_offset(x, y) \
            .perform()

    def wait(self, timeout=20):
        return WebDriverWait(self.driver, timeout)

    def click_when_clickable(self, locator):
        self.wait(10).until(EC.visibility_of_element_located(locator))
        self.wait(10).until(EC.element_to_be_clickable(locator)).click()

    def stop(self):
        self.driver.quit()


class ZoomRecorder:
    def __init__(self, url):
        self.__start_xvfb()
        self.__start_pulse_audio()
        self.__create_sink()

        set_display(DISPLAY)
        set_sink()
        self.zoomClient = ZoomClient(url)

    def record(self):
        self.__start_ffmpeg()
        self.zoomClient.join_meeting()

    def stop(self):
        self.zoomClient.stop()
        self.__stop_ffmpeg()
        self.__stop_xvfb()

    def __start_ffmpeg(self):
        self.ffmepg = subprocess.Popen([
            "ffmpeg",
            "-video_size", f'{WIDTH}x{HEIGHT}',
            "-framerate", "25",
            "-f", "x11grab",
            "-i", DISPLAY,
            "-f", "alsa",
            "-ac", "2",
            "-i", "default",
            "-y",
            "output.mp4"
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def __start_xvfb(self):
        self.xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{WIDTH}x{HEIGHT}x24"], stdout=subprocess.PIPE)

    def __start_pulse_audio(self):
        os.system("pulseaudio -D --exit-idle-time=-1")

    def __stop_xvfb(self):
        kill(self.xvfb)

    def __stop_ffmpeg(self):
        self.ffmepg.communicate(b'q')
        self.ffmepg.wait()

    def __create_sink(self):
        os.system("pacmd load-module module-virtual-sink sink_name=v1")
        os.system("pacmd set-default-sink v1")
