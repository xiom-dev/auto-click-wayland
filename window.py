# window.py
#
# Copyright 2024 Satvik Patwardhan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Xdp', '1.0')
gi.require_version('GtkSource', '5')
from gi.repository import Adw
from gi.repository import Gtk, Gdk, GLib, Gio
from gi.repository import Xdp, GtkSource

# We import libevdev just for libevdev.EV_KEY.BTN_*.value.
# We don't need to do this for keyboard events as it can take Gdk.KEY_* instead.
import libevdev

import os, sys, time
import threading

class vsep(Gtk.Separator):
    def __init__(self):
        super().__init__(orientation = Gtk.Orientation.VERTICAL)
        self.add_css_class('spacer')

class hsep(Gtk.Separator):
    def __init__(self):
        super().__init__(orientation = Gtk.Orientation.HORIZONTAL)
        self.add_css_class('spacer')

class ClickerWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ClickerWindow'

    label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(700,300)
        self.set_title(_('Clicker'))

        self.is_running = False
        self.stop_event = threading.Event()
        self.session = None
        self.skip_delay = False

        toolbarview = Adw.ToolbarView()

        headerbar = Adw.HeaderBar()
        
        toolbar = Gtk.Box()
        toolbar.append(hsep())
        delay_img = Gtk.Image()
        delay_img.set_from_icon_name('delay-long-symbolic')
        delay_img.set_tooltip_text(_('Delay'))
        toolbar.append(delay_img)

        toolbar.append(hsep())

        self.delay_dropdown = Gtk.DropDown.new_from_strings([_('5 seconds'), _('15 seconds'), _('30 seconds'), _('1 minute')])
        toolbar.append(self.delay_dropdown)
        toolbar.append(hsep())

        interval_img = Gtk.Image()
        interval_img.set_from_icon_name('hourglass-symbolic')
        interval_img.set_tooltip_text(_('Duration between repeats'))
        toolbar.append(interval_img)

        toolbar.append(hsep())

        self.interval_spinbox = Gtk.SpinButton()
        self.interval_spinbox.set_range(0, 10000000000000)
        self.interval_spinbox.set_increments(10, 100)
        self.interval_spinbox.set_value(100)
        self.interval_spinbox.set_hexpand(True)
        toolbar.append(self.interval_spinbox)
        toolbar.append(hsep())
        ms_label = Gtk.Label()
        #Translators: this is milliseconds
        ms_label.set_markup("<b>{}</b>".format(_("ms")))
        toolbar.append(ms_label)

        headerbar.pack_start(toolbar)

        self.start_button = Gtk.Button()
        self.start_button.set_icon_name('media-playback-start-symbolic')
        self.start_button.set_tooltip_text(_('Start'))
        self.start_button.add_css_class('suggested-action')
        headerbar.pack_end(self.start_button)

        about_button = Gtk.Button()
        about_button.set_icon_name('help-about-symbolic')
        about_button.set_tooltip_text(_('About'))
        about_button.connect('clicked', self.get_application().on_about_action, None)
        headerbar.pack_end(about_button)
        
        toolbarview.add_top_bar(headerbar)

        self.view_stack = Adw.ViewStack()

        view_stack_bar = Adw.ViewSwitcherBar()
        view_stack_bar.set_reveal(True)
        view_stack_bar.set_stack(self.view_stack)
        toolbarview.add_top_bar(view_stack_bar)

        box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        box.append(vsep())

        mouse_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)

        buttons_box = Gtk.Box()
        buttons_box.add_css_class('linked')
        buttons_box.set_halign(Gtk.Align.CENTER)
        buttons_box.set_vexpand(True)

        self.left_button = Gtk.ToggleButton()
        self.left_button.add_css_class('flat')
        left_button_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        left_button_image = Gtk.Image()
        left_button_image.set_from_icon_name('mouse-primary-click-symbolic')
        left_button_image.set_pixel_size(128)
        left_button_box.append(left_button_image)
        left_button_box.append(Gtk.Label(label = _('Left')))
        self.left_button.set_child(left_button_box)
        self.left_button.set_active(True)
        buttons_box.append(self.left_button)

        right_button = Gtk.ToggleButton()
        right_button.add_css_class('flat')
        right_button_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        right_button_image = Gtk.Image()
        right_button_image.set_from_icon_name('mouse-secondary-click-symbolic')
        right_button_image.set_pixel_size(128)
        right_button_box.append(right_button_image)
        right_button_box.append(Gtk.Label(label = _('Right')))
        right_button.set_child(right_button_box)
        right_button.set_group(self.left_button)
        buttons_box.append(right_button)

        mouse_box.append(buttons_box)
        self.view_stack.add_titled_with_icon(mouse_box, 'mouse', _('Mouse'), 'input-mouse-symbolic')

        keyboard_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)

        select_key_label = Gtk.Label()
        select_key_label.set_markup('<b>{}</b>'.format(_("Key:")))
        keyboard_box.append(select_key_label)

        keyboard_box.append(vsep())

        self.key_dropdown = Gtk.DropDown.new_from_strings([
            'Enter (Return)', 'Space', "Meta (Super Key/ Start Key)",'Escape', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
            'Up', 'Down', 'Left', 'Right',
            'Backspace', 'Delete', 'Insert', 'Home', 'End', 'PageUp', 'PageDown', 'Tab',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            '-', '=', '[', ']', '\\', ';', "'", '`', ',', '.', '/'
            ])
        self.key_dropdown.set_hexpand(False)
        self.key_dropdown.set_halign(Gtk.Align.CENTER)
        keyboard_box.append(self.key_dropdown)

        keyboard_box.append(vsep())

        modifiers_box = Gtk.Box()
        modifiers_box.add_css_class('linked')
        modifiers_box.set_halign(Gtk.Align.CENTER)

        self.shift_button = Gtk.ToggleButton()
        self.shift_button.add_css_class('flat')
        self.shift_button.set_tooltip_text('Shift')
        self.shift_button.set_label('Shift')
        modifiers_box.append(self.shift_button)

        self.ctrl_button = Gtk.ToggleButton()
        self.ctrl_button.add_css_class('flat')
        self.ctrl_button.set_tooltip_text('Control')
        self.ctrl_button.set_label('Ctrl')
        modifiers_box.append(self.ctrl_button)

        self.alt_button = Gtk.ToggleButton()
        self.alt_button.add_css_class('flat')
        self.alt_button.set_tooltip_text('Alt')
        self.alt_button.set_label('Alt')
        modifiers_box.append(self.alt_button)

        keyboard_box.append(modifiers_box)
        ctrl_button_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        
        self.view_stack.add_titled_with_icon(keyboard_box, 'keyboard', _('Keyboard'), 'input-keyboard-symbolic')

        pattern_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)

        warnclamp = Adw.Clamp()
        warningbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
        warningbox.add_css_class('card')
        pattern_warning = Gtk.Label()
        pattern_warning.set_markup("<b>{}</b>".format(_("Only use this if you know what you're doing!")))
        pattern_warning.add_css_class("warning")
        warningbox.append(pattern_warning)
        warning_text_label = Gtk.Label()
        warning_text_label.set_wrap(True)
        warning_text_label.add_css_class("dim-label")
        t1 = _("Enter each key press on a new line using the exact key name from the Keyboard section.")
        #Translators: DO NOT TRANSLATE the 'delay time' within quotes, keep it in english. It is code that the user has to enter.
        warning_text_label.set_text('{}\n{}'.format(t1,_("Add a time delay with 'delay <time>' (time in seconds).")))
        warning_text_label.set_justify(Gtk.Justification.CENTER)
        warningbox.append(warning_text_label)
        warnclamp.set_child(warningbox)
        pattern_box.append(warnclamp)

        pattern_box.append(vsep())

        entryclamp = Adw.Clamp()
        self.pattern_buffer = GtkSource.Buffer()
        
        self.pattern_buffer.set_text('''Meta (Super Key/ Start Key)
c
l
i
c
k
e
r
delay 1''')

        pattern_textview = GtkSource.View()
        pattern_textview.set_monospace(True)
        pattern_textview.set_show_line_numbers(True)
        pattern_textview.set_buffer(self.pattern_buffer)

        frame = Gtk.Frame()
        scrolled = Gtk.ScrolledWindow()
        frame.set_valign(Gtk.Align.FILL)
        frame.set_vexpand(True)
        scrolled.set_hexpand(False)
        scrolled.set_child(pattern_textview)
        frame.set_child(scrolled)

        entryclamp.set_child(frame)
        pattern_box.append(entryclamp)

        self.view_stack.add_titled_with_icon(pattern_box, 'pattern', _('Pattern'), 'code-symbolic')

        box.append(self.view_stack)

        box.append(vsep())

        warning_label = Gtk.Label()
        warning_label.set_text(_('When you press start, make sure to allow remote interaction in the prompt.'))
        warning_label.add_css_class('dim-label')
        warning_label.set_wrap(True)
        warning_label.set_justify(Gtk.Justification.CENTER)
        box.append(warning_label)
        toolbarview.set_content(box)

        duration_box = Gtk.Box()
        duration_box.add_css_class('toolbar')
        duration_box.set_halign(Gtk.Align.CENTER)
        duration_box.set_vexpand(True)

        duration_img = Gtk.Image()
        duration_label =  Gtk.Label()
        duration_label.set_markup('<b>{}</b>'.format(_("Duration of automation:")))
        duration_box.append(duration_label)

        self.min_duration_spin = Gtk.SpinButton()
        self.min_duration_spin.connect('value-changed', self.sensitive_button)
        self.min_duration_spin.set_range(0, 10000000000000)
        self.min_duration_spin.set_increments(1, 1)
        self.min_duration_spin.set_digits(3)
        self.min_duration_spin.set_value(1)
        self.min_duration_spin.set_hexpand(True)
        duration_box.append(self.min_duration_spin)

        min_label = Gtk.Label()
        min_label.set_markup("<b>{}</b>".format(_("minutes")))
        duration_box.append(min_label)

        duration_box.append(vsep())

        self.s_duration_spin = Gtk.SpinButton()
        self.s_duration_spin.connect('value-changed', self.sensitive_button)
        self.s_duration_spin.set_range(0, 10000000000000)
        self.s_duration_spin.set_increments(1, 1)
        self.s_duration_spin.set_digits(3)
        self.s_duration_spin.set_value(1)
        self.s_duration_spin.set_hexpand(True)
        duration_box.append(self.s_duration_spin)

        s_label = Gtk.Label()
        s_label.set_markup("<b>{}</b>".format(_("seconds")))
        duration_box.append(s_label)

        toolbarview.add_bottom_bar(duration_box)

        self.automation_state = {'left': self.left_button, 'mode': self.view_stack,
        'delay': self.delay_dropdown, 'interval': self.interval_spinbox,
        'min_duration': self.min_duration_spin, 's_duration': self.s_duration_spin,
        'key': self.key_dropdown, 'shift': self.shift_button, 'ctrl': self.ctrl_button, 'alt': self.alt_button,
        'pattern': self.pattern_buffer}
        self.start_button.connect('clicked', self.on_start_stop_clicked)
        self.set_content(toolbarview)

        self.show_warning_dialog()

        self.setup_global_shortcut()

    def sensitive_button(self, spinbutton):
        try:
            # don't touch the button while it acts as a Stop button
            if self.is_running:
                return
            # if both spinboxes have been initialized
            if self.min_duration_spin.get_value() == 0 and self.s_duration_spin.get_value() == 0:
                self.start_button.set_sensitive(False)
            else:
                self.start_button.set_sensitive(True)
        except:
            pass

    def on_start_stop_clicked(self, button):
        self.toggle_automation()

    def toggle_automation(self, instant=False):
        if self.is_running:
            # Interrompre l'automatisation en cours.
            self.stop_event.set()
        else:
            self.skip_delay = instant   # F9 : démarrage immédiat, sans le délai
            self.stop_event.clear()
            self.is_running = True
            self.set_stop_button()
            self.create_session(self.automation_state)
        return False   # au cas où appelé via GLib.idle_add

    def set_stop_button(self):
        self.start_button.set_icon_name('media-playback-stop-symbolic')
        self.start_button.set_tooltip_text(_('Stop'))
        self.start_button.remove_css_class('suggested-action')
        self.start_button.add_css_class('destructive-action')

    def reset_start_button(self):
        self.is_running = False
        self.stop_event.clear()
        self.start_button.set_icon_name('media-playback-start-symbolic')
        self.start_button.set_tooltip_text(_('Start'))
        self.start_button.remove_css_class('destructive-action')
        self.start_button.add_css_class('suggested-action')
        return False   # for GLib.idle_add

    def finish_automation(self, session):
        session.close()
        self.session = None
        GLib.idle_add(self.reset_start_button)

    def create_session(self, state):
        def create_session_finish(portal, result, error, state):
            if error != None:
                print(error.message)
                self.reset_start_button()
                return
            self.session = portal.create_remote_desktop_session_finish(result)
            self.session.start(None, None, lambda session, result, error: self.start_session(session, result, error, state), None)
        self.portal = Xdp.Portal()
        # Souris ET clavier dans une seule session : couvre tous les modes.
        device = Xdp.DeviceType.POINTER | Xdp.DeviceType.KEYBOARD
        self.portal.create_remote_desktop_session(device, Xdp.OutputType.MONITOR, Xdp.RemoteDesktopFlags.MULTIPLE, Xdp.CursorMode.EMBEDDED, None, lambda portal, result, error: create_session_finish(portal, result, error, state), None)

    def start_session(self, session, result, error, state):
        def get_key(key):
            if key == 'Enter (Return)':
                key = Gdk.KEY_Return
            elif key == 'Space':
                key = Gdk.KEY_space
            elif key == 'Meta (Super Key/ Start Key)':
                key = Gdk.KEY_Super_L
            elif key == 'Backspace':
                key = Gdk.KEY_BackSpace
            elif key == 'PageUp':
                key = Gdk.KEY_Page_Up
            elif key == 'PageDown':
                key = Gdk.KEY_Page_Down
            elif key in ['-', '=', '[', ']', '\\', ';', "'", '`', ',', '.', '/']:
                keys = ['-', '=', '[', ']', '\\', ';', "'", '`', ',', '.', '/']
                keysyms_suffix = ['minus', 'equal', 'bracketleft', 'bracketright', 'backslash', 'semicolon', 'apostrophe', 'grave', 'comma', 'period', 'slash']
                for i in range(len(keys)):
                    if key == keys[i]:
                        key = eval(f'Gdk.KEY_{keysyms_suffix[i]}')
            else:
                key = eval(f'Gdk.KEY_{key}')
            return key

        if error:
            print(error)
            self.session = None
            self.reset_start_button()
            return
        if not session.get_streams():
            self.session = None
            self.reset_start_button()
            return
        #device = session.get_devices()
        mode = state['mode'].get_visible_child_name()
        stream = session.get_streams()[0][0] # I have absolutely no idea whatsoever as to what a stream is, except that its a Pipewire thing

        if state['delay'].get_selected_item().get_string() == '5 seconds':
                delay = 5
        elif state['delay'].get_selected_item().get_string() == '15 seconds':
            delay = 10
        elif state['delay'].get_selected_item().get_string() == '30 seconds':
            delay = 30
        elif state['delay'].get_selected_item().get_string() == '1 minute':
            delay = 60        
        if self.skip_delay:
            delay = 0   # démarrage immédiat (déclenché au clavier)
        interval = state['interval'].get_value() * 0.001 # seconds
        min_duration = state['min_duration'].get_value() * 60 # seconds
        s_duration = state['s_duration'].get_value()
        duration = min_duration + s_duration

        # TODO: When Global Shortcuts are implemented, add a shortcut to stop execution.

        if mode == 'mouse':
            button = 'left' if state['left'].get_active() else 'right'

            clicking_thread = threading.Thread(target = self.start_clicking, args = (session, delay, interval, button, duration))
            clicking_thread.start()

        elif mode == 'keyboard':
            key = state['key'].get_selected_item().get_string()
            key = get_key(key)

            shift, ctrl, alt = False, False, False
            if state['shift'].get_active():
                shift = True
            if state['ctrl'].get_active():
                ctrl = True
            if state['alt'].get_active():
                alt = True

            pressing_thread = threading.Thread(target = self.start_pressing, args = (session, delay, interval, duration, key, shift, ctrl, alt))
            pressing_thread.start()
        
        elif mode == 'pattern':
            pattern = state['pattern'].get_text(state['pattern'].get_start_iter(), state['pattern'].get_end_iter(), False).strip()
            keys = []
            for i in pattern.split('\n'):
                if i.startswith("delay"):
                    keys.append(i)
                    continue
                try:
                    keys.append(get_key(i))
                except Exception as e:
                    print(e)
                    return
            
            pattern = keys
            pattern_thread = threading.Thread(target = self.start_pattern, args = (session, delay, interval, duration, pattern))
            pattern_thread.start()

    def start_clicking(self, session, delay, interval, button, duration):
        if self.stop_event.wait(delay):
            self.finish_automation(session)
            return

        end_time = time.time() + duration
        while time.time() < end_time and not self.stop_event.is_set():
            session.pointer_button(libevdev.EV_KEY.BTN_LEFT if button == 'left' else libevdev.EV_KEY.BTN_RIGHT, Xdp.ButtonState.PRESSED)
            time.sleep(0.01)
            session.pointer_button(libevdev.EV_KEY.BTN_LEFT if button == 'left' else libevdev.EV_KEY.BTN_RIGHT, Xdp.ButtonState.RELEASED)
            if self.stop_event.wait(interval):
                break
        self.finish_automation(session)

    def start_pressing(self, session, delay, interval, duration, key, shift, ctrl, alt):
        if self.stop_event.wait(delay):
            self.finish_automation(session)
            return

        end_time = time.time() + duration

        while time.time() < end_time and not self.stop_event.is_set():
            self.press_key(session, key, shift, ctrl, alt)
            if self.stop_event.wait(interval):
                break

        self.finish_automation(session)

    def start_pattern(self, session, delay, interval, duration, pattern):
        if self.stop_event.wait(delay):
            self.finish_automation(session)
            return

        end_time = time.time() + duration
        while time.time() < end_time and not self.stop_event.is_set():
            for key in pattern:
                if self.stop_event.is_set():
                    break
                if type(key) == str and key.startswith('delay'):
                    time.sleep(float(key[6:]))
                    continue
                self.press_key(session, key, False, False, False)
            if self.stop_event.wait(interval):
                break

        self.finish_automation(session)

    def press_key(self, session, key, shift, ctrl, alt):
        if shift:
            session.keyboard_key(True, Gdk.KEY_Shift_L, Xdp.KeyState.PRESSED)
        if ctrl:
            session.keyboard_key(True, Gdk.KEY_Control_L, Xdp.KeyState.PRESSED)
        if alt:
            session.keyboard_key(True, Gdk.KEY_Alt_L, Xdp.KeyState.PRESSED)
        session.keyboard_key(True, key, Xdp.KeyState.PRESSED)
        time.sleep(0.01)
        if shift:
            session.keyboard_key(True, Gdk.KEY_Shift_L, Xdp.KeyState.RELEASED)
        if ctrl:
            session.keyboard_key(True, Gdk.KEY_Control_L, Xdp.KeyState.RELEASED)
        if alt:
            session.keyboard_key(True, Gdk.KEY_Alt_L, Xdp.KeyState.RELEASED)
        session.keyboard_key(True, key, Xdp.KeyState.RELEASED)

    def show_warning_dialog(self):
        if os.path.exists(os.path.expanduser('~/.var/app/net.codelogistics.clicker/seen_dialog')):
            return
        def set_dont_show(dialog, response):
            if dont_show_cb.get_active():
                with open(os.path.expanduser('~/.var/app/net.codelogistics.clicker/seen_dialog'), 'w') as f:
                    f.write('1')
        #Translators: Do not translate the word Portal
        message = Adw.MessageDialog.new(self, _("Portal access"), _("Clicker needs permission to simulate input by simulating a connection to this computer. It does not connect to any remote host."))
        message.add_response("ok", _("OK"))
        dont_show_cb = Gtk.CheckButton()
        dont_show_cb.set_label(_("Don't show this message again"))
        message.set_extra_child(dont_show_cb)
        message.connect('response', set_dont_show)
        message.present()

    def setup_global_shortcut(self):
        # Raccourci clavier GLOBAL (marche même quand Clicker n'a pas le focus).
        # libportal 0.7.1 ne l'expose pas, on passe donc par le portail en D-Bus.
        self.gs_session_handle = None
        try:
            self.dbus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except Exception as e:
            print('Global shortcut unavailable:', e)
            return
        self.sender_token = self.dbus.get_unique_name()[1:].replace('.', '_')
        self.dbus.signal_subscribe(
            'org.freedesktop.portal.Desktop',
            'org.freedesktop.portal.GlobalShortcuts', 'Activated',
            '/org/freedesktop/portal/desktop', None,
            Gio.DBusSignalFlags.NONE, self.on_shortcut_activated, None)
        self.create_shortcut_session()

    def on_shortcut_activated(self, conn, sender, path, iface, signal, params, user_data):
        session_handle, shortcut_id, timestamp, options = params.unpack()
        if shortcut_id == 'toggle':
            # Démarrage instantané au clavier : pas de compte à rebours.
            GLib.idle_add(self.toggle_automation, True)

    def _finish_call(self, conn, result, user_data):
        try:
            conn.call_finish(result)
        except GLib.Error as e:
            print('Portal call error:', e.message)

    def create_shortcut_session(self):
        token = 'clicker_{}'.format(int(time.time() * 1000))
        session_token = 'clicker_sess_{}'.format(int(time.time() * 1000))
        request_path = '/org/freedesktop/portal/desktop/request/{}/{}'.format(self.sender_token, token)
        sub = {}
        def responded(conn, s, p, i, sig, params, user_data):
            conn.signal_unsubscribe(sub['id'])
            response, results = params.unpack()
            if response != 0:
                print('GlobalShortcuts CreateSession failed:', response)
                return
            self.gs_session_handle = results['session_handle']
            self.bind_shortcuts()
        sub['id'] = self.dbus.signal_subscribe(
            'org.freedesktop.portal.Desktop', 'org.freedesktop.portal.Request',
            'Response', request_path, None, Gio.DBusSignalFlags.NONE, responded, None)
        self.dbus.call(
            'org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop',
            'org.freedesktop.portal.GlobalShortcuts', 'CreateSession',
            GLib.Variant('(a{sv})', ({
                'handle_token': GLib.Variant('s', token),
                'session_handle_token': GLib.Variant('s', session_token),
            },)),
            GLib.VariantType('(o)'),
            Gio.DBusCallFlags.NONE, -1, None, self._finish_call, None)

    def bind_shortcuts(self):
        token = 'clicker_bind_{}'.format(int(time.time() * 1000))
        request_path = '/org/freedesktop/portal/desktop/request/{}/{}'.format(self.sender_token, token)
        sub = {}
        def responded(conn, s, p, i, sig, params, user_data):
            conn.signal_unsubscribe(sub['id'])
            response, results = params.unpack()
            if response != 0:
                print('GlobalShortcuts BindShortcuts failed:', response)
        sub['id'] = self.dbus.signal_subscribe(
            'org.freedesktop.portal.Desktop', 'org.freedesktop.portal.Request',
            'Response', request_path, None, Gio.DBusSignalFlags.NONE, responded, None)
        self.dbus.call(
            'org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop',
            'org.freedesktop.portal.GlobalShortcuts', 'BindShortcuts',
            GLib.Variant('(oa(sa{sv})sa{sv})', (
                self.gs_session_handle,
                [('toggle', {
                    'description': GLib.Variant('s', _('Start/Stop clicking')),
                    'preferred_trigger': GLib.Variant('s', 'F9'),
                })],
                '',
                {'handle_token': GLib.Variant('s', token)},
            )),
            GLib.VariantType('(o)'), Gio.DBusCallFlags.NONE, -1, None, self._finish_call, None)