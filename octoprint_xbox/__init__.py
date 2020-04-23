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
        self.maxX =                         126.0
        self.maxY =                         126.0
        self.midX =                         self.maxX / 2
        self.midY =                         self.maxY / 2
        self.iota =                         0.25

    def threadAcceptInput(self):
        self._logger.info('threadAcceptInput running')
        while not self.bStop:
            if self.bConnected:
                if not self.bStarted:
                    # -------------------------------------------------------------------------------------------------
                    # Idle-related commands
                    # -------------------------------------------------------------------------------------------------
                    # -------------------------------------
                    # Triggers
                    # -------------------------------------
                    fltLTrig =              self.joy.leftTrigger()        # relative retraction mapped 0.1 to 10mm
                    if fltLTrig > 0:
                        _E = fltLTrig * 10.0
                        if _E > 0:
                            self._logger.info('Left trigger pressed, relative retraction: ' + str(fltLTrig))
                            self.send('M83')
                            self.send('G0 E-' + str(_E) + ' F400')
                        sleep(3)
                    fltRTrig =              self.joy.rightTrigger()       # relative extrusion mapped 0.1 to 10mm
                    if fltRTrig > 0:
                        _E = fltRTrig * 10.0
                        if _E > 0:
                            self._logger.info('Left trigger pressed, relative extrusion: ' + str(fltLTrig))
                            self.send('M83')
                            self.send('G0 E' + str(_E) + ' F400')
                        sleep(3)
                    # -------------------------------------
                    # X and Y buttons
                    # -------------------------------------
                    bX =                    self.joy.X()                  # Cool the extruder
                    if bX:
                        self._logger.info('X button pressed, cooling extruder')
                        self.send('M104 S0')
                        sleep(3)
                    bY =                    self.joy.Y()                  # Preheat the extruder
                    if bY:
                        self._logger.info('X button pressed, preheating extruder to 190C')
                        self.send('M104 S190')
                        sleep(3)
                    # -------------------------------------
                    # Z
                    # -------------------------------------
                    bDpadUp =               self.joy.dpadUp()             # relative Z +1mm
                    if bDpadUp:
                        self._logger.info('dpad up button pressed, up 1mm')
                        self.send('G91')
                        self.send('G1 Z-1.0 F200')
                        self.send('G90')
                    bDpadDown =             self.joy.dpadDown()           # relative Z -1mm
                    if bDpadDown:
                        self._logger.info('dpad down button pressed, down 1mm')
                        self.send('G91')
                        self.send('G1 Z1.0 F200')
                        self.send('G90')
                    bDpadLeft =             self.joy.dpadLeft()           # relative Z +0.1mm
                    if bDpadLeft:
                        self._logger.info('dpad left button pressed, up 0.1mm')
                        self.send('G91')
                        self.send('G1 Z-0.1 F200')
                        self.send('G90')
                    bDpadRight =            self.joy.dpadRight()          # relative Z -0.1mm
                    if bDpadRight:
                        self._logger.info('dpad right button pressed, down 0.1mm')
                        self.send('G91')
                        self.send('G1 Z0.1 F200')
                        self.send('G90')
                    # -------------------------------------
                    # Guide
                    # -------------------------------------
                    # bGuide =                self.joy.Guide()
                    # -------------------------------------
                    # Start
                    # -------------------------------------
                    bStart =                self.joy.Start()              # Home the XYZ
                    if bStart:
                        self._logger.info('Start button pressed, homing axes')
                        self.send('G28 X Y Z')
                        sleep(3)
                    # -------------------------------------
                    # Bumpers
                    # -------------------------------------
                    bLB =                   self.joy.leftBumper()
                    if bLB:
                        self._logger.info('Left Bumper button pressed, unloading filament')
                        self.send('M83')
                        self.send('G0 E-130.0 F400')
                        sleep(5)
                    bRB =                   self.joy.rightBumper()
                    if bRB:
                        self._logger.info('Right Bumper button pressed, loading filament')
                        self.send('M83')
                        self.send('G0 E130.0 F400')
                        sleep(5)
                    # -------------------------------------
                    # Left thumstick
                    # -------------------------------------
                    bLT =                   self.joy.leftThumbstick()     # Pushing down on left joystick
                    if bLT:
                        self._logger.info('Left joystick push button pressed, centering X/Y')
                        self.send('G90')
                        self.send('G0 X' + str(self.midX) + ' Y' + str(self.midY))
                        sleep(3)
                    # -------------------------------------
                    # Left joystick
                    # -------------------------------------
                    tupleLXY =              self.joy.leftStick()          # Left stick scaled between -1.0 to 1.0 (X, Y)
                    if abs(tupleLXY[0]) > self.iota or abs(tupleLXY[1]) > self.iota:
                        _X = tupleLXY[0]
                        _Y = tupleLXY[1]
                        _X = (_X * self.midX) + self.midX   if _X > 0   else self.midX + (_X * self.midX)
                        _Y = self.midY + (_Y * self.midY)   if _Y > 0   else (_Y * self.midY) + self.midY
                        self._logger.info('Left joystick X: ' + str(tupleLXY[0]) + ' Y: ' + str(tupleLXY[1]) + ' [' + str(_X) + '][' + str(_Y) + ']')
                        self.send('G90')
                        self.send('G1 X' + str(_X) + ' Y' + str(_Y))
                        sleep(3)
                    # fltLJoyX =              self.joy.leftX()              # mapped absolute move based on bed width
                    # fltLJoyY =              self.joy.leftY()              # mapped absolute move based on bed depth
                    # -------------------------------------
                    # Right thumstick
                    # -------------------------------------
                    # bRT =                   self.joy.rightThumbstick()    # Pushing down on right joystick
                    # -------------------------------------
                    # Right joystick
                    # -------------------------------------
                    # tupleRXY =              self.joy.rightStick()         # Right stick scaled between -1.0 to 1.0 (X, Y)
                    # fltRJoyX =              self.joy.rightX()             # relative move X mapped 0.1 to 10mm
                    # fltRJoyY =              self.joy.rightY()             # relative move Y mapped 0.1 to 10mm
                else:
                    # -------------------------------------------------------------------------------------------------
                    # Printing-related commands
                    # -------------------------------------------------------------------------------------------------
                    bA =                    self.joy.A()                  # Resume during printing
                    if bA:
                        self._logger.info('A button pressed, resuming print')
                        self._printer.resume_print()
                    bB =                    self.joy.B()                  # Pause during printing
                    if bB:
                        self._logger.info('B button pressed, pausing print')
                        self._printer.pause_print()
                    bBack =                 self.joy.Back()               # Cancel during printing
                    if bBack:
                        self._logger.info('Back button pressed, cancelling print')
                        self._printer.cancel_print()
            sleep(0.2)
            # End of while loop ---------------------------------------------------------------------------------------
        self._logger.info('threadAcceptInput exiting')

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
