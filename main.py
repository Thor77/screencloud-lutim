import os
import time
import warnings

import requests

import ScreenCloud
from PythonQt.QtCore import QFile, QSettings, QStandardPaths
from PythonQt.QtUiTools import QUiLoader


class LutimUploader(object):
    SHORTNAME = 'lutim'

    def __init__(self):
        self.uil = QUiLoader()
        self.loadSettings()

    def showSettingsUI(self, parentWidget):
        self.parentWidget = parentWidget
        self.settingsDialog = self.uil.load(
            QFile(
                os.path.join(
                    ScreenCloud.getPluginDir(), self.SHORTNAME, 'settings.ui'
                )
            ),
            parentWidget
        )
        self.settingsDialog.connect('accepted()', self.saveSettings)
        self.updateUi()
        self.settingsDialog.open()

    def updateUi(self):
        self.loadSettings()
        self.settingsDialog.group_lutim.input_url.setText(self.url)
        self.settingsDialog.group_lutim.input_delay.setValue(self.delay)
        self.settingsDialog.group_lutim.input_firstview.setChecked(
            self.delete_on_firstview)
        self.settingsDialog.group_lutim.input_forever.setChecked(
            self.keep_forever)
        self.settingsDialog.group_lutim.verify_ssl.setChecked(self.verify_ssl)
        self.settingsDialog.adjustSize()

    def loadSettings(self):
        settings = QSettings()
        settings.beginGroup('lutim')
        self.url = settings.value('url', 'https://lut.im/')
        self.delay = int(settings.value('delay', 1))
        self.delete_on_firstview = settings.value('firstview', False) \
            in ['true', True]
        self.keep_forever = settings.value('forever', False) in ['true', True]
        self.verify_ssl = settings.value('verify_ssl', True) in ['true', True]
        settings.endGroup()

    def saveSettings(self):
        settings = QSettings()
        settings.beginGroup('lutim')
        settings.setValue(
            'url', self.settingsDialog.group_lutim.input_url.text)
        settings.setValue(
            'delay', self.settingsDialog.group_lutim.input_delay.value)
        settings.setValue(
            'firstview',
            self.settingsDialog.group_lutim.input_firstview.isChecked()
        )
        settings.setValue(
            'forever',
            self.settingsDialog.group_lutim.input_forever.isChecked()
        )
        settings.setValue(
            'verify_ssl',
            self.settingsDialog.group_lutim.verify_ssl.isChecked()
        )
        settings.endGroup()

    def isConfigured(self):
        return bool(self.url)

    def getFilename(self):
        return time.time()

    def upload(self, screenshot, name):
        self.loadSettings()
        url = self.url

        # check url
        if not url.startswith('http'):
            ScreenCloud.setError('Invalid url!')
            return False
        # append / to url (if needed)
        if not url.endswith('/'):
            url += '/'
        if self.keep_forever:
            delay = 0
        else:
            delay = self.delay
        # save to a temporary file
        timestamp = time.time()
        filename = ScreenCloud.formatFilename(str(timestamp))
        tmpFilename = os.path.join(QStandardPaths.writableLocation(
            QStandardPaths.TempLocation
        ), filename)
        screenshot.save(QFile(tmpFilename), ScreenCloud.getScreenshotFormat())

        def do_request():
            return requests.post(
                url,
                data={
                    'delete-day': delay,
                    'format': 'json',
                    'first-view': int(self.delete_on_firstview)
                },
                files={
                    'file': open(tmpFilename, 'rb')
                },
                verify=self.verify_ssl
            )
        if not self.verify_ssl:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                response = do_request()
        else:
            response = do_request()
        if not response:
            ScreenCloud.setError('No Lutim-Instance there')
            return False
        else:
            response_data = response.json()
        if response_data['success']:
            display_url = url + response_data['msg']['short']
            ScreenCloud.setUrl(display_url)
            return True
        else:
            ScreenCloud.setError(
                'Lutim reports an error: \n' + response_data['message']
            )
            return False
