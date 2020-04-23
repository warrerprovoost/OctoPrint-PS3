# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import subprocess
from time import sleep
from threading import Thread
import octoprint_xbox.xbox

class XboxPlugin(octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.AssetPlugin,
                 octoprint.plugin.ShutdownPlugin,
                 octoprint.plugin.StartupPlugin,
                 octoprint.plugin.EventHandlerPlugin,
                 octoprint.plugin.TemplatePlugin):

    def __init__(self):
        self.bStop =                        False
        self.bConnected =                   False
        self.bStarted =                     False
        self.joy =                          None

    def get_settings_defaults(self):
        return dict()

    def get_assets(self):
        return dict(
            js=["js/xbox.js"],
            css=["css/xbox.css"],
            less=["less/xbox.less"]
        )

    def on_event(self, event, payload):
        # self._logger.info('on_event ' + str(event))
        if event == 'Connected':
            self._logger.info('on_event Connected')
            self.bConnected =               True
            self.bStarted =                 False
            return
        if event == 'Disconnected':
            self._logger.info('on_event Disconnected')
            self.bConnected =               False
            self.bStarted =                 False
            return
        if event == 'PrintStarted':
            self._logger.info('on_event PrintStarted')
            self.bStarted =                 True
            return
        if event in ('PrintFailed', 'PrintDone', 'PrintCancelled'):
            self.bStarted =                 False
            return
        return

    def send(self, gcode):
        if gcode is not None:
            self._printer._comm.sendCommand(gcode, tags={"trigger:comm.on_connected",}, part_of_job=False)

    def threadAcceptInput(self):
        self._logger.info('threadAcceptInput running')
        while not self.bStop:
            if self.bConnected:
                if not self.bStarted:
                    # -------------------------------------------------------------------------------------------------
                    # Idle-related commands
                    # -------------------------------------------------------------------------------------------------
                    # fltLJoyX =              self.joy.leftX()              # mapped absolute move based on bed width
                    # fltLJoyY =              self.joy.leftY()              # mapped absolute move based on bed depth
                    # fltRJoyX =              self.joy.rightX()             # relative move X mapped 0.1 to 10mm
                    # fltRJoyY =              self.joy.rightY()             # relative move Y mapped 0.1 to 10mm
                    # fltLTrig =              self.joy.leftTrigger()        # relative retraction mapped 0.1 to 10mm
                    # fltRTrig =              self.joy.rightTrigger()       # relative extrusion mapped 0.1 to 10mm
                    # bX =                    self.joy.X()
                    # bY =                    self.joy.Y()
                    # bDpadUp =               self.joy.dpadUp()             # relative Z +1mm
                    # bDpadDown =             self.joy.dpadDown()           # relative Z -1mm
                    # bDpadLeft =             self.joy.dpadLeft()           # relative Z +0.1mm
                    # bDpadRight =            self.joy.dpadRight()          # relative Z -0.1mm
                    # bGuide =                self.joy.Guide()
                    bStart =                self.joy.Start()              # Home the XYZ
                    if bStart:
                        self._logger.info('threadAcceptInput Start button pressed')
                        self.send('G28 X Y Z')
                    # bLT =                   self.joy.leftThumbstick()     # Pushing down on left joystick
                    # bRT =                   self.joy.rightThumbstick()    # Pushing down on right joystick
                    bLB =                   self.joy.leftBumper()
                    if bLB:
                        self._logger.info('threadAcceptInput Left Bumper button pressed')
                        self.send('M83')
                        self.send('G0 E-130.0 F400')
                    bRB =                   self.joy.rightBumper()
                    if bRB:
                        self._logger.info('threadAcceptInput Right Bumper button pressed')
                        self.send('M83')
                        self.send('G0 E130.0 F400')
                    # tupleLXY =              self.joy.leftStick()          # Left stick scaled between -1.0 to 1.0 (X, Y)
                    # tupleRXY =              self.joy.rightStick()         # Right stick scaled between -1.0 to 1.0 (X, Y)
                else:
                    # -------------------------------------------------------------------------------------------------
                    # Printing-related commands
                    # -------------------------------------------------------------------------------------------------
                    bA =                    self.joy.A()                  # Resume during printing
                    if bA:
                        self._logger.info('threadAcceptInput resuming print')
                        self._printer.resume_print()
                    bB =                    self.joy.B()                  # Pause during printing
                    if bB:
                        self._logger.info('threadAcceptInput pausing print')
                        self._printer.pause_print()
                    bBack =                 self.joy.Back()               # Cancel during printing
                    if bBack:
                        self._logger.info('threadAcceptInput cancelling print')
                        self._printer.cancel_print()
            sleep(0.2)
            # End of while loop ---------------------------------------------------------------------------------------
        self._logger.info('threadAcceptInput exiting')

    def on_shutdown(self):
        self._logger.info('Shutdown received...')
        self.bStop =                        True
        subprocess.run(["sudo", "/home/pi/scripts/killxbox"])

    def on_after_startup(self):
        self._logger.info("on_after_startup")
        try:
            self.joy =                      xbox.Joystick()
            self.threadAcceptInput()
        # When the receiver wasn't stopped the last time: "[Errno 1] Operation not permitted"
        except BaseException as e:
            self._logger.info("Xbox receiver exception " + str(e))
            pass

    def get_update_information(self):
        return dict(
            xbox=dict(
                displayName="Xbox Plugin",
                displayVersion=self._plugin_version,
                type="github_release",
                user="OutsourcedGuru",
                repo="OctoPrint-Xbox",
                current=self._plugin_version,
                pip="https://github.com/OutsourcedGuru/OctoPrint-Xbox/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "Xbox Plugin"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = XboxPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
}
