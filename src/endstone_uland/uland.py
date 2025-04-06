import json
import datetime
import os
import re
import math
import time
import random

from endstone_uland.lang import lang
from endstone.level import Location
from endstone import ColorFormat, Player
from endstone.plugin import Plugin
from endstone.command import Command, CommandSender, CommandSenderWrapper
from endstone.form import ActionForm, ModalForm, Dropdown, Toggle, TextInput
from endstone.event import *

current_dir = os.getcwd()
first_dir = os.path.join(current_dir, 'plugins', 'uland')
zx_ui_dir = os.path.join(current_dir, 'plugins', 'zx_ui')

if not os.path.exists(first_dir):
    os.mkdir(first_dir)

lang_dir = os.path.join(first_dir, 'lang')
if not os.path.exists(lang_dir):
    os.mkdir(lang_dir)

land_data_file_path = os.path.join(first_dir, 'land.json')
config_data_file_path = os.path.join(first_dir, 'config.json')
money_data_file_path = os.path.join(current_dir, 'plugins', 'umoney', 'money.json')


class uland(Plugin):
    api_version = '0.6'

    def on_enable(self):
        # Check whether the pre-plugin umoney has been installed.
        if not os.path.exists(money_data_file_path):
            self.logger.error(f'{ColorFormat.RED}Missing pre-plugin UMoney...')
            self.server.plugin_manager.disable_plugin(self)

        # Load land data.
        if not os.path.exists(land_data_file_path):
            land_data = {}
            with open(land_data_file_path, 'w', encoding='utf-8') as f:
                json_str = json.dumps(land_data, indent=4, ensure_ascii=False)
                f.write(json_str)
        else:
            with open(land_data_file_path, 'r', encoding='utf-8') as f:
                land_data = json.loads(f.read())

        # Initialize land data.
        if len(land_data) != 0:
            allowed_key_list = [
                'dimension', 'range', 'area', 'land_expense', 'land_buy_time', 'land_tp', 'permissions'
                'public_land', 'fire_protect', 'explode_protect', 'anti_wither_enter',
                'anti_right_click_block', 'anti_break_block', 'anti_right_click_entity',
                'anti_player_attack'
            ]
            land: dict
            land_info: dict
            for land in land_data.values():
                for land_info in land.values():
                    for key in list(land_info.keys()):
                        if key not in allowed_key_list:
                            land_info.pop(key)

            for land in land_data.values():
                for land_info in land.values():
                    for key in allowed_key_list[7:]:
                        if land_info.get(key) is None:
                            if key == 'public_land':
                                land_info[key] = False
                            else:
                                land_info[key] = True

            with open(land_data_file_path, 'w+', encoding='utf-8') as f:
                json_str = json.dumps(land_data, indent=4, ensure_ascii=False)
                f.write(json_str)

        self.land_data = land_data

        # Load config data.
        if not os.path.exists(config_data_file_path):
            config_data = {'land_buy_price': 5,
                           'land_create_timeout': 30,
                           'max_area': 40000,
                           'max_land_per_player': 3,
                           'is_land_sell_rate_on': True,
                           'land_sell_cool_down_timeout': 3}
            with open(config_data_file_path, 'w', encoding='utf-8') as f:
                json_str = json.dumps(config_data, indent=4, ensure_ascii=False)
                f.write(json_str)
        else:
            with open(config_data_file_path, 'r', encoding='utf-8') as f:
                config_data = json.loads(f.read())
        self.config_data = config_data

        # Load lang data.
        self.lang_data = lang.load_lang(self, lang_dir)

        self.record_create_land_event = {}
        self.register_events(self)
        self.server.scheduler.run_task(self, self.check_player_pos, delay=0, period=20)
        self.server.scheduler.run_task(self, self.land_protect_task, delay=0, period=20)
        self.CommandSenderWrapper = CommandSenderWrapper(
            sender=self.server.command_sender,
            on_message=None
        )
        self.logger.info(f'{ColorFormat.YELLOW}ULand is enabled...')

    commands = {
        'ul': {
            'description': 'Call out the main form of ULand',
            'usages': ['/ul'],
            'permissions': ['uland.command.ul']
        },
        'posa': {
            'description': 'Select point A',
            'usages': ['/posa'],
            'permissions': ['uland.command.posa']
        },
        'posb': {
            'description': 'Select point B',
            'usages': ['/posb'],
            'permissions': ['uland.command.posb']
        }
    }

    permissions ={
        'uland.command.ul': {
            'description': 'Call out the main form of ULand',
            'default': True
        },
        'uland.command.posa': {
            'description': 'Select point A',
            'default': True
        },
        'uland.command.posb': {
            'description': 'Select point B',
            'default': True
        }
    }

    def on_command(self, sender: CommandSender, command: Command, args: list[str]):
        if command.name == 'ul':
            if not isinstance(sender, Player):
                sender.send_message(f'{ColorFormat.RED}This command can only be executed by a player...')
                return
            player = sender

            land_main_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "main_form.title")}',
                content=f'{ColorFormat.GREEN}{self.get_text(player, "main_form.content")}',
            )
            land_main_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "main_form.button.create_new_land")}',
                                      icon='textures/ui/icon_new', on_click=self.create_land)
            land_main_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "main_form.button.my_land")}',
                                      icon='textures/ui/icon_recipe_nature', on_click=self.my_land)
            land_main_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "main_form.button.land_info")}',
                                      icon='textures/ui/magnifyingGlass', on_click=self.land_info)
            land_main_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "main_form.button.public_land")}',
                                      icon='textures/ui/mashup_world', on_click=self.server_public_land)
            if player.is_op:
                land_main_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "main_form.button.land_manage")}',
                                          icon='textures/ui/op', on_click=self.manage_all_lands)
                land_main_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "main_form.button.reload_config")}',
                                          icon='textures/ui/settings_glyph_color_2x', on_click=self.reload_config_data)
            if not os.path.exists(zx_ui_dir):
                land_main_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "main_form.button.close")}',
                                          icon='textures/ui/cancel', on_click=None)
                land_main_form.on_close = None
            else:
                land_main_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "main_form.button.back_to_zx_ui")}',
                                          icon='textures/ui/refresh_light', on_click=self.back_to_menu)
                land_main_form.on_close = self.back_to_menu
            player.send_form(land_main_form)

        # /posa -- Command to select point A under land create mode.
        if command.name == 'posa':
            if not isinstance(sender, Player):
                sender.send_message(f'{ColorFormat.RED}This command can only be executed by a player...')
                return
            player = sender

            if not self.record_create_land_event.get(player.name):
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_1")}')
                return

            PosA = [math.floor(player.location.x), math.floor(player.location.z), math.floor(player.location.y)]
            if self.record_create_land_event[player.name].get('PosA'):
                self.record_create_land_event[player.name]['PosA'] = PosA
                player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "create_land.message.success_2")}\n'
                                    f'{self.get_text(player, "coordinates")} ({PosA[0]}, ~, {PosA[1]})')
            else:
                self.record_create_land_event[player.name]['PosA'] = PosA
                player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "create_land.message.success_1")}\n'
                                    f'{self.get_text(player, "coordinates")} ({PosA[0]}, ~, {PosA[1]})')
            dimension = player.location.dimension.name
            self.record_create_land_event[player.name]['dimension'] = dimension

        # /posa -- Command to select point B under land create mode.
        if command.name == 'posb':
            if not isinstance(sender, Player):
                sender.send_message(f'{ColorFormat.RED}This command can only be executed by a player...')
                return
            player = sender

            if not self.record_create_land_event.get(player.name):
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_1")}')
                return

            if not self.record_create_land_event[player.name].get('PosA'):
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_5")}: '
                                    f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_5.reason_1")}')
                return

            if self.record_create_land_event[player.name]['dimension'] != player.location.dimension.name:
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_5")}: '
                                    f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_5.reason_2")}')
                return

            PosB = [math.floor(player.location.x), math.floor(player.location.z)]
            PosA = self.record_create_land_event[player.name]['PosA']
            if PosA == PosB:
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_5")}: '
                                    f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_5.reason_3")}')
                return

            self.record_create_land_event[player.name]['PosB'] = PosB
            player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "create_land.message.success_3")}\n'
                                f'{self.get_text(player, "coordinates")} ({PosB[0]}, ~, {PosB[1]})')

    # Activate land create mode
    def create_land(self, player: Player):
        if len(self.land_data[player.name].keys()) >= self.config_data['max_land_per_player']:
            player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_2")}: '
                                f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_2.reason_1")}')
            return

        if not self.record_create_land_event.get(player.name):
            self.record_create_land_event[player.name] = {}
            time_start = round(time.time())
            self.record_create_land_event[player.name]['time_start'] = time_start
            task = self.server.scheduler.run_task(self, lambda x=player: self.on_create_land(player), delay=0, period=20)
            self.record_create_land_event[player.name]['task'] = task
            player.send_message(ColorFormat.YELLOW + self.get_text(player, "create_land.message_1").format(self.config_data["land_create_timeout"])
                                + '\n\n' +
                                f'{self.get_text(player, "create_land.message_2")}\n\n'
                                f'{self.get_text(player, "create_land.message_3")}\n\n'
                                f'{self.get_text(player, "create_land.message_4")}')
        else:
            player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_2")}: '
                                f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_2.reason_2")}')
            return

    # Land create task
    def on_create_land(self, player: Player):
        time_start = self.record_create_land_event[player.name]['time_start']
        time_now = round(time.time())
        if time_now - time_start > self.config_data['land_create_timeout'] and len(self.record_create_land_event[player.name]) < 5:
            self.server.scheduler.cancel_task(self.record_create_land_event[player.name]['task'].task_id)
            del self.record_create_land_event[player.name]
            player.send_message(f'{ColorFormat.RED}{self.get_text(player,  "create_land.message.fail_3")}: '
                                f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_4")}')
            return

        if len(self.record_create_land_event[player.name]) == 5:
            self.server.scheduler.cancel_task(self.record_create_land_event[player.name]['task'].task_id)
            self.on_further_create_land(player)

    # Land create
    def on_further_create_land(self, player: Player):
        PosA = self.record_create_land_event[player.name]['PosA']
        PosB = self.record_create_land_event[player.name]['PosB']
        dimension = self.record_create_land_event[player.name]['dimension']

        for land in self.land_data.values():
            for land_info in land.values():
                if dimension == land_info['dimension']:
                    range = []
                    it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                    for i in it:
                        range.append(int(i.group()))
                    if ((min(range[0], range[2]) <= PosA[0] <= max(range[0], range[2])
                         and min(range[1], range[3]) <= PosA[1] <= max(range[1], range[3]))
                            or (min(range[0], range[2]) <= PosB[0] <= max(range[0], range[2])
                                and min(range[1], range[3]) <= PosB[1] <= max(range[1], range[3]))
                            or (((min(PosA[0], PosB[0]) <= range[0] <= max(PosA[0], PosB[0]))
                                and (min(PosA[1], PosB[1]) <= range[1] <= max(PosA[1], PosB[1])))
                                and ((min(PosA[0], PosB[0]) <= range[2] <= max(PosA[0], PosB[0]))
                                and (min(PosA[1], PosB[1]) <= range[3] <= max(PosA[1], PosB[1]))))):
                        del self.record_create_land_event[player.name]
                        player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_2")}: '
                                            f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_2.reason_3")}')
                        return

        width1 = abs(PosA[0] - PosB[0])
        width2 = abs(PosA[1] - PosB[1])
        area = width1 * width2
        if area < 4:
            del self.record_create_land_event[player.name]
            player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_2")}: '
                                f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_2.reason_4")}')
            return
        if area > self.config_data['max_area']:
            del self.record_create_land_event[player.name]
            player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_2")}: {ColorFormat.WHITE}'
                                + self.get_text(player, "create_land.message.fail_2.reason_5").format({self.config_data["max_area"]}))
            return

        land_expense = area * self.config_data['land_buy_price']
        player_money = self.server.plugin_manager.get_plugin('umoney').api_get_player_money(player.name)
        if player_money < land_expense:
            del self.record_create_land_event[player.name]
            player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_2")}: '
                                f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_2.reason_6")}\n'
                                f'{ColorFormat.RED}{self.get_text(player, "land_buy_expense")}: {ColorFormat.WHITE}{land_expense}\n'
                                f'{self.get_text(player, "player_money")}: {ColorFormat.WHITE}{player_money}')
            return

        textinput1 = TextInput(
            label=f'{ColorFormat.YELLOW}{self.get_text(player, "dimension")}: {ColorFormat.WHITE}{dimension}\n'
                  f'{ColorFormat.YELLOW}{self.get_text(player, "point_a")}: {ColorFormat.WHITE}({PosA[0]}, ~, {PosA[1]})\n'
                  f'{ColorFormat.YELLOW}{self.get_text(player, "point_b")}: {ColorFormat.WHITE}({PosB[0]}, ~, {PosB[1]})\n'
                  f'{ColorFormat.YELLOW}{self.get_text(player, "area")}: {ColorFormat.WHITE}{area}\n'
                  f'{ColorFormat.YELLOW}{self.get_text(player, "land_buy_expense")}: {ColorFormat.WHITE}{land_expense}\n'
                  f'\n'
                  f'{ColorFormat.GREEN}{self.get_text(player, "create_land.from.textinput.label_1")}\n' +
                  self.get_text(player, 'create_land.from.textinput.label_2').format(player.name),
            placeholder=f'{self.get_text(player, "create_land.from.textinput.placeholder")}'
        )
        further_create_land_form = ModalForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "create_land.from.title")}',
            controls=[textinput1],
            on_close=self.on_cancel_further_create_land
        )
        def on_submit(player: Player, json_str):
            data = json.loads(json_str)
            if len(data[0]) == 0:
                land_name = self.get_text(player, "default_new_land_name").format(player.name)
            else:
                land_name = data[0]
            if land_name in list(self.land_data[player.name].keys()):
                del self.record_create_land_event[player.name]
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.fail_2")}: {ColorFormat.WHITE}' +
                                    self.get_text(player, "create_land.message.fail_2.reason_7").format(land_name))
                return
            land_buy_time = str(datetime.datetime.now()).split(' ')[0]
            self.land_data[player.name][land_name] = {'dimension': dimension,
                                                      'range': f'({PosA[0]}, ~, {PosA[1]}) - ({PosB[0]}, ~, {PosB[1]})',
                                                      'area': area,
                                                      'land_expense': land_expense,
                                                      'land_buy_time': land_buy_time,
                                                      'land_tp': [PosA[0], PosA[2], PosA[1]],
                                                      'permissions': [],
                                                      'public_land': False,
                                                      'fire_protect': True,
                                                      'explode_protect': True,
                                                      'anti_wither_enter': True,
                                                      'anti_right_click_block': True,
                                                      'anti_break_block': True,
                                                      'anti_right_click_entity': True,
                                                      'anti_player_attack': True}
            del self.record_create_land_event[player.name]
            self.save_land_data()
            player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "create_land.message.success_4")}')
            self.server.plugin_manager.get_plugin('umoney').api_change_player_money(player.name, -land_expense)
        further_create_land_form.on_submit = on_submit
        player.send_form(further_create_land_form)

    # Cancel the land create task.
    def on_cancel_further_create_land(self, player: Player) -> None:
        del self.record_create_land_event[player.name]
        player.send_message(f'{ColorFormat.RED}{self.get_text(player, "create_land.message.cancel")}: '
                            f'{ColorFormat.WHITE}{self.get_text(player, "create_land.message.fail_4")}')

    @event_handler
    def on_player_left(self, event: PlayerQuitEvent) -> None:
        if self.record_create_land_event.get(event.player.name):
            self.server.scheduler.cancel_task(self.record_create_land_event[event.player.name]['task'].task_id)
            del self.record_create_land_event[event.player.name]

    # My lands
    def my_land(self, player: Player) -> None:
        my_land_form =  ActionForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "my_land_form.title")}',
            content=f'{ColorFormat.GREEN}{self.get_text(player, "my_land_form.content")}',
            on_close=self.back_to_main_form
        )
        for land_owner, land in self.land_data.items():
            for land_name, land_info in land.items():
                dimension = land_info['dimension']
                range = land_info['range']
                area = land_info['area']
                land_expense = land_info['land_expense']
                land_buy_time = land_info['land_buy_time']
                land_tp = land_info['land_tp']
                permissions = land_info['permissions']
                if player.name == land_owner:
                    my_land_form.add_button(f'{land_name}\n{ColorFormat.YELLOW}[{self.get_text(player, "owner")}] {dimension}',
                                            icon='textures/ui/icon_spring',
                                            on_click=self.my_land_details(land_name, dimension, range, area, land_expense, land_buy_time, land_tp, permissions))
                if player.name in permissions:
                    my_land_form.add_button(f'{land_name}\n{ColorFormat.YELLOW}[{self.get_text(player, "member")}] {dimension}',
                                            icon='textures/ui/icon_spring',
                                            on_click=self.my_land_member_details(land_owner, land_name, dimension, range, area, land_expense, land_buy_time, land_tp, permissions))
        my_land_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}', icon='textures/ui/refresh_light', on_click=self.back_to_main_form)
        player.send_form(my_land_form)

    # Land details [Member]
    def my_land_member_details(self, land_owner, land_name, dimension, range, area, land_expense, land_buy_time, land_tp, permissions):
        def on_click(player: Player):
            my_land_member_details_form = ActionForm(
                title=land_name,
                content=f'{ColorFormat.YELLOW}{self.get_text(player, "owner")}: {ColorFormat.YELLOW}{land_owner}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "dimension")}: {ColorFormat.WHITE}{dimension}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "range")}: {ColorFormat.WHITE}{range}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "area")}: {ColorFormat.WHITE}{area}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "land_buy_expense")}: {ColorFormat.WHITE}{land_expense}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "creation_time")}: {ColorFormat.WHITE}{land_buy_time}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "teleport_point")}: {ColorFormat.WHITE}({land_tp[0]}, {land_tp[1]}, {land_tp[2]})\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "members")}: {ColorFormat.WHITE}',
                on_close=self.my_land
            )
            my_land_member_details_form.content += ', '.join(permissions)
            my_land_member_details_form.content += f'\n\n{ColorFormat.GREEN}{self.get_text(player, "my_land_detail_form.content")}'
            my_land_member_details_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_detail_form.button.tp")}',
                                                   icon='textures/ui/realmsIcon', on_click=self.tp_to_my_land(land_tp, dimension))
            my_land_member_details_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                                   icon='textures/ui/refresh_light', on_click=self.my_land)
            player.send_form(my_land_member_details_form)
        return on_click

    # Land details [Owner]
    def my_land_details(self, land_name, dimension, range, area, land_expense, land_but_time, land_tp, permissions):
        def on_click(player: Player):
            my_land_details_form = ActionForm(
                title=land_name,
                content=f'{ColorFormat.YELLOW}{self.get_text(player, "dimension")}: {ColorFormat.WHITE}{dimension}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "range")}: {ColorFormat.WHITE}{range}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "area")}: {ColorFormat.WHITE}{area}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "land_buy_expense")}: {ColorFormat.WHITE}{land_expense}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "creation_time")}: {ColorFormat.WHITE}{land_but_time}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "teleport_point")}: {ColorFormat.WHITE}({land_tp[0]}, {land_tp[1]}, {land_tp[2]})\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "members")}: {ColorFormat.WHITE}',
                on_close=self.my_land
            )
            if len(permissions) == 0:
                my_land_details_form.content += self.get_text(player, "none")
            else:
                my_land_details_form.content += ', '.join(permissions)
            my_land_details_form.content += f'\n\n{ColorFormat.GREEN}{self.get_text(player, "my_land_detail_form.content")}'
            my_land_details_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_detail_form.button.tp")}',
                                            icon='textures/ui/realmsIcon', on_click=self.tp_to_my_land(land_tp, dimension))
            my_land_details_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_detail_form.button.settings")}',
                                            icon='textures/ui/hammer_l', on_click=self.my_land_setting(land_name))
            my_land_details_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                            icon='textures/ui/refresh_light', on_click=self.my_land)
            player.send_form(my_land_details_form)
        return on_click

    # Land teleport
    def tp_to_my_land(self, land_tp, dimension):
        def on_click(player: Player):
            if dimension == 'Overworld':
                target_dimension = self.server.level.get_dimension('OVERWORLD')
            elif dimension == 'Nether':
                target_dimension = self.server.level.get_dimension('NETHER')
            else:
                target_dimension = self.server.level.get_dimension('THEEND')
            location = Location(
                target_dimension,
                x=float(land_tp[0]),
                y=float(land_tp[1]),
                z=float(land_tp[2])
            )
            player.teleport(location)
            player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "land_tp.message.success")}')
        return on_click

    # Land settings
    def my_land_setting(self, land_name):
        def on_click(player: Player):
            my_land_setting_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "my_land_setting_form.title")}',
                content=ColorFormat.GREEN + self.get_text(player, "my_land_setting_form.content_1").format(land_name) +
                        f'\n\n'
                        f'{ColorFormat.GREEN}{self.get_text(player, "my_land_setting_form.content_2")}',
                on_close=self.my_land
            )
            my_land_setting_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_setting_form.button.add_member")}',
                                            icon='textures/ui/sidebar_icons/profile_screen_icon', on_click=self.my_land_add_member(land_name))
            my_land_setting_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_setting_form.button.delete_member")}',
                                            icon='textures/ui/sidebar_icons/dressing_room_customization', on_click=self.my_land_delete_member(land_name))
            my_land_setting_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_setting_form.button.land_rename")}',
                                            icon='textures/ui/icon_book_writable', on_click=self.my_land_rename(land_name))
            my_land_setting_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_setting_form.button.land_security_setting")}',
                                            icon='textures/ui/recipe_book_icon', on_click=self.my_land_set_security(land_name))
            my_land_setting_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_setting_form.button.land_tp_setting")}',
                                            icon='textures/ui/realmsIcon', on_click=self.my_land_set_land_tp(land_name))
            my_land_setting_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_setting_form.button.land_sell")}',
                                            icon='textures/ui/trade_icon', on_click=self.my_land_sell(land_name))
            my_land_setting_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "my_land_setting_form.button.land_ownership_transfer")}',
                                            icon='textures/ui/switch_accounts', on_click=self.my_land_transfer_ownership(land_name))
            my_land_setting_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                            icon='textures/ui/refresh_light', on_click=self.my_land)
            player.send_form(my_land_setting_form)
        return on_click

    # Add a land number
    def my_land_add_member(self, land_name):
        def on_click(player: Player):
            player_name_list = []
            for player_name in self.land_data.keys():
                if (player_name != player.name
                        and player_name not in self.land_data[player.name][land_name]['permissions']):
                    player_name_list.append(player_name)
            if len(player_name_list) == 0:
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "land_add_member.message.fail")}: '
                                    f'{ColorFormat.WHITE}{self.get_text(player, "land_add_member.message.fail.reason")}')
                return
            player_name_list.sort(key=lambda x: x[0].lower(), reverse=False)
            dropdown = Dropdown(
                label=f'{ColorFormat.GREEN}{self.get_text(player, "land_add_member_form.dropdown.label")}',
                options=player_name_list
            )
            my_land_add_member_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "land_add_member_form.title")}',
                controls=[dropdown],
                submit_button=f'{ColorFormat.YELLOW}{self.get_text(player, "land_add_member_form.submit_button")}',
                on_close=self.my_land
            )
            def on_submit(player: Player, json_str: str):
                data = json.loads(json_str)
                player_name_to_add = player_name_list[data[0]]
                self.land_data[player.name][land_name]['permissions'].append(player_name_to_add)
                self.save_land_data()
                player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "land_add_member.message.success")}')
            my_land_add_member_form.on_submit = on_submit
            player.send_form(my_land_add_member_form)
        return on_click

    # Delete a land member
    def my_land_delete_member(self, land_name):
        def on_click(player: Player):
            player_name_list = self.land_data[player.name][land_name]['permissions']
            if len(player_name_list) == 0:
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "land_delete_member.message.fail")}: '
                                    f'{ColorFormat.WHITE}{self.get_text(player, "land_delete_member.message.fail.reason")}')
                return
            player_name_list.sort(key=lambda x: x[0].lower(), reverse=False)
            dropdown = Dropdown(
                label=f'{ColorFormat.GREEN}{self.get_text(player, "land_delete_member_form.dropdown.label")}',
                options=player_name_list,
            )
            my_land_delete_member_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "land_delete_member_form.title")}',
                controls=[dropdown],
                submit_button=f'{ColorFormat.YELLOW}{self.get_text(player, "land_delete_member_form.submit_button")}',
                on_close=self.my_land
            )
            def on_submit(player: Player, json_str: str):
                data = json.loads(json_str)
                player_name_to_delete = player_name_list[data[0]]
                self.land_data[player.name][land_name]['permissions'].remove(player_name_to_delete)
                self.save_land_data()
                player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "land_delete_member.message.success")}')
            my_land_delete_member_form.on_submit = on_submit
            player.send_form(my_land_delete_member_form)
        return on_click

    # Land rename
    def my_land_rename(self, land_name):
        def on_click(player: Player):
            textinput = TextInput(
                label=f'{ColorFormat.GREEN}{self.get_text(player, "land_rename_form.textinput.label")}',
                default_value=land_name,
                placeholder=f'{self.get_text(player, "land_rename_form.textinput.placeholder")}',
            )
            my_land_rename_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "land_rename_form.title")}',
                controls=[textinput],
                submit_button=f'{ColorFormat.YELLOW}{self.get_text(player, "land_rename_form.submit_button")}',
                on_close=self.my_land
            )
            def on_submit(player: Player, json_str: str):
                data = json.loads(json_str)
                if len(data[0]) == 0:
                    player.send_message(self.get_text(player, "message.type_error"))
                    return
                else:
                    new_land_name = data[0]
                if self.land_data[player.name].get(new_land_name):
                    player.send_message(f'{ColorFormat.RED}{self.get_text(player, "land_rename.message.fail")}: {ColorFormat.WHITE}'
                                        + self.get_text(player, "land_rename.message.fail.reason").format(new_land_name))
                    return
                self.land_data[player.name][new_land_name] = self.land_data[player.name][land_name]
                self.land_data[player.name].pop(land_name)
                self.save_land_data()
                player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "land_rename.message.success")}')
            my_land_rename_form.on_submit = on_submit
            player.send_form(my_land_rename_form)
        return on_click

    # Land security settings
    def my_land_set_security(self, land_name):
        def on_click(player: Player):
            toggle1 = Toggle(
                label=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.toggle_1.label")}'
            )
            if self.land_data[player.name][land_name]['fire_protect']:
                toggle1.default_value = True
            else:
                toggle1.default_value = False
            toggle2 = Toggle(
                label=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.toggle_2.label")}'
            )
            if self.land_data[player.name][land_name]['explode_protect']:
                toggle2.default_value = True
            else:
                toggle2.default_value = False
            toggle3 = Toggle(
                label=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.toggle_3.label")}'
            )
            if self.land_data[player.name][land_name]['anti_wither_enter']:
                toggle3.default_value = True
            else:
                toggle3.default_value = False
            toggle4 = Toggle(
                label=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.toggle_4.label")}'
            )
            if self.land_data[player.name][land_name]['anti_right_click_block']:
                toggle4.default_value = True
            else:
                toggle4.default_value = False
            toggle5 = Toggle(
                label=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.toggle_5.label")}'
            )
            if self.land_data[player.name][land_name]['anti_break_block']:
                toggle5.default_value = True
            else:
                toggle5.default_value = False
            toggle6 = Toggle(
                label=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.toggle_6.label")}'
            )
            if self.land_data[player.name][land_name]['anti_right_click_entity']:
                toggle6.default_value = True
            else:
                toggle6.default_value = False
            toggle7 = Toggle(
                label=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.toggle_7.label")}'
            )
            if self.land_data[player.name][land_name]['anti_player_attack']:
                toggle7.default_value = True
            else:
                toggle7.default_value = False
            toggle8 = Toggle(
                label=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.toggle_8.label")}'
            )
            if self.land_data[player.name][land_name]['public_land']:
                toggle8.default_value = True
            else:
                toggle8.default_value = False
            my_land_set_security_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "land_security_setting_form.title")}',
                controls=[toggle1, toggle2, toggle3, toggle4, toggle5, toggle6, toggle7, toggle8],
                submit_button=f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting_form.submit_button")}',
                on_close=self.my_land
            )
            def on_submit(player: Player, json_str):
                data = json.loads(json_str)
                if data[0]:
                    self.land_data[player.name][land_name]['fire_protect'] = True
                else:
                    self.land_data[player.name][land_name]['fire_protect'] = False
                if data[1]:
                    self.land_data[player.name][land_name]['explode_protect'] = True
                else:
                    self.land_data[player.name][land_name]['explode_protect'] = False
                if data[2]:
                    self.land_data[player.name][land_name]['anti_wither_enter'] = True
                else:
                    self.land_data[player.name][land_name]['anti_wither_enter'] = False
                if data[3]:
                    self.land_data[player.name][land_name]['anti_right_click_block'] = True
                else:
                    self.land_data[player.name][land_name]['anti_right_click_block'] = False
                if data[4]:
                    self.land_data[player.name][land_name]['anti_break_block'] = True
                else:
                    self.land_data[player.name][land_name]['anti_break_block'] = False
                if data[5]:
                    self.land_data[player.name][land_name]['anti_right_click_entity'] = True
                else:
                    self.land_data[player.name][land_name]['anti_right_click_entity'] = False
                if data[6]:
                    self.land_data[player.name][land_name]['anti_player_attack'] = True
                else:
                    self.land_data[player.name][land_name]['anti_player_attack'] = False
                if data[7]:
                    self.land_data[player.name][land_name]['public_land'] = True
                else:
                    self.land_data[player.name][land_name]['public_land'] = False
                player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "land_security_setting.message.success")}')
                self.save_land_data()
            my_land_set_security_form.on_submit = on_submit
            player.send_form(my_land_set_security_form)
        return on_click

    # Land teleport point setting
    def my_land_set_land_tp(self, land_name):
        def on_click(player: Player):
            new_land_tp = [math.floor(player.location.x), math.floor(player.location.y), math.floor(player.location.z)]
            confirm_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "land_teleport_point_setting_form.title")}',
                content=f'{ColorFormat.GREEN}{self.get_text(player, "land_teleport_point_setting_form.content")}: '
                        f'{ColorFormat.WHITE}({new_land_tp[0]}, {new_land_tp[1]}, {new_land_tp[2]})',
                on_close=self.my_land
            )
            confirm_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "land_teleport_point_setting_form.button.confirm")}',
                                    icon='textures/ui/realms_slot_check', on_click=self.my_land_set_land_tp_confirm(land_name, new_land_tp))
            confirm_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                    icon='textures/ui/refresh_light', on_click=self.my_land)
            player.send_form(confirm_form)
        return on_click

    def my_land_set_land_tp_confirm(self, land_name, new_land_tp):
        def on_click(player: Player):
            self.land_data[player.name][land_name]['land_tp'] = new_land_tp
            self.save_land_data()
            player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "land_teleport_point_setting.message.success")}')
        return on_click

    # Land sell
    def my_land_sell(self, land_name):
        def on_click(player: Player):
            confirm_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "land_sell_form.title")}',
                content=ColorFormat.GREEN + self.get_text(player, "land_sell_form.content_1").format(land_name)
                        + '\n\n',
                on_close=self.my_land
            )
            land_expense = self.land_data[player.name][land_name]['land_expense']
            land_buy_time = self.land_data[player.name][land_name]['land_buy_time']
            if not self.config_data['is_land_sell_rate_on']:
                land_sell_money = land_expense
                confirm_form.content += (f'{ColorFormat.YELLOW}{self.get_text(player, "creation_time")}: '
                                         f'{ColorFormat.WHITE}{land_buy_time}\n'
                                         f'{ColorFormat.YELLOW}{self.get_text(player, "land_buy_expense")}: '
                                         f'{ColorFormat.WHITE}{land_expense}\n'
                                         f'{ColorFormat.YELLOW}{self.get_text(player, "land_sell_expense")}'
                                         f'{ColorFormat.WHITE}{land_sell_money}\n'
                                         f'\n'
                                         f'{ColorFormat.AQUA}{self.get_text(player, "land_sell_form.content_2")}')
                confirm_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "land_sell_form.button.sell")}',
                                        icon='textures/ui/realms_slot_check', on_click=self.my_land_sell_confirm(land_name, land_sell_money))
            else:
                current_time = datetime.datetime.now()
                # Use the string of the current date as a random seed
                random.seed(str(current_time).split(' ')[0])
                land_sell_rate = round(random.uniform(0, 2), 2)
                land_sell_money = round(land_expense * land_sell_rate)
                pre_land_buy_time = land_buy_time.split('-')
                if ((current_time - datetime.datetime(int(pre_land_buy_time[0]), int(pre_land_buy_time[1]), int(pre_land_buy_time[2]))).days
                    >= self.config_data['land_sell_cool_down_timeout']):
                    confirm_form.content += (f'{ColorFormat.YELLOW}{self.get_text(player, "creation_time")}: '
                                             f'{ColorFormat.WHITE}{land_buy_time}\n'
                                             f'{ColorFormat.YELLOW}{self.get_text(player, "land_buy_expense")}: '
                                             f'{ColorFormat.WHITE}{land_expense}\n'
                                             f'{ColorFormat.YELLOW}{self.get_text(player, "land_sell_form.content_3")}: '
                                             f'{ColorFormat.WHITE}{land_sell_rate}\n'
                                             f'{ColorFormat.YELLOW}{self.get_text(player, "land_sell_expense")}: '
                                             f'{ColorFormat.WHITE}{land_sell_money}\n'
                                             f'\n'
                                             f'{ColorFormat.AQUA}{self.get_text(player, "land_sell_form.content_4")}\n'
                                             + ColorFormat.YELLOW
                                             + self.get_text(player, "land_sell_form.content_5").format(self.config_data["land_sell_cool_down_timeout"])
                                             + '\n' +
                                             f'{ColorFormat.GREEN}{self.get_text(player, "land_sell_form.content_6")}')
                    confirm_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "land_sell_form.button.sell")}',
                                            icon='textures/ui/realms_slot_check', on_click=self.my_land_sell_confirm(land_name, land_sell_money))
                else:
                    confirm_form.content += (f'{ColorFormat.YELLOW}{self.get_text(player, "creation_time")}: '
                                             f'{ColorFormat.WHITE}{land_buy_time}\n'
                                             f'{ColorFormat.YELLOW}{self.get_text(player, "land_buy_expense")}: '
                                             f'{ColorFormat.WHITE}{land_expense}\n'
                                             f'{ColorFormat.YELLOW}{self.get_text(player, "land_sell_form.content_3")}: '
                                             f'{ColorFormat.WHITE}{land_sell_rate}\n'
                                             f'{ColorFormat.YELLOW}{self.get_text(player, "land_sell_expense")}: '
                                             f'{ColorFormat.WHITE}{land_sell_money}\n'
                                             f'\n'
                                             f'{ColorFormat.AQUA}{self.get_text(player, "land_sell_form.content_4")}\n'
                                             + ColorFormat.YELLOW
                                             + self.get_text(player, "land_sell_form.content_7").format(self.config_data["land_sell_cool_down_timeout"])
                                             + '\n' +
                                             f'{ColorFormat.RED}{self.get_text(player, "land_sell_form.content_8")}')
            confirm_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                    icon='textures/ui/refresh_light', on_click=self.my_land)
            player.send_form(confirm_form)
        return on_click

    def my_land_sell_confirm(self, land_name, land_sell_money):
        def on_click(player: Player):
            self.land_data[player.name].pop(land_name)
            self.save_land_data()
            player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "land_sell.message.success")}')
            self.server.plugin_manager.get_plugin('umoney').api_change_player_money(player.name, land_sell_money)
        return on_click

    # Land ownership transfer
    def my_land_transfer_ownership(self, land_name):
        def on_click(player: Player):
            player_name_list = [player_name for player_name in self.land_data.keys() if player_name != player.name]
            if len(player_name_list) == 0:
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "land_ownership_transfer.message.fail")}: '
                                    f'{ColorFormat.WHITE}{self.get_text(player, "land_ownership_transfer.message.fail.reason")}')
                return
            player_name_list.sort(key=lambda x: x[0].lower(), reverse=False)
            dropdown = Dropdown(
                label=f'{ColorFormat.GREEN}{self.get_text(player, "land_ownership_transfer_form.dropdown.label")}',
                options=player_name_list
            )
            my_land_transfer_ownership_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "land_ownership_transfer_form.title")}',
                controls=[dropdown],
                submit_button=f'{ColorFormat.YELLOW}{self.get_text(player, "land_ownership_transfer_form.submit_button")}',
                on_close=self.my_land
            )
            def on_submit(player: Player, json_str: str):
                data = json.loads(json_str)
                player_to_transfer_ownership_name = player_name_list[data[0]]
                # Copy the land data and give it to the player who is the target of land ownership transfer
                self.land_data[player_to_transfer_ownership_name][land_name] = self.land_data[player.name][land_name]
                # Reset land settings to default values
                self.land_data[player_to_transfer_ownership_name][land_name]['permissions'] = []
                self.land_data[player_to_transfer_ownership_name][land_name]['public_land'] = False
                self.land_data[player_to_transfer_ownership_name][land_name]['fire_protect'] = True
                self.land_data[player_to_transfer_ownership_name][land_name]['explode_protect'] = True
                self.land_data[player_to_transfer_ownership_name][land_name]['anti_wither_enter'] = True
                self.land_data[player_to_transfer_ownership_name][land_name]['anti_right_click_block'] = True
                self.land_data[player_to_transfer_ownership_name][land_name]['anti_break_block'] = True
                self.land_data[player_to_transfer_ownership_name][land_name]['anti_right_click_entity'] = True
                self.land_data[player_to_transfer_ownership_name][land_name]['anti_player_attack'] = True
                self.land_data[player.name].pop(land_name)
                self.save_land_data()
                player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "land_ownership_transfer.message.success")}')
            my_land_transfer_ownership_form.on_submit = on_submit
            player.send_form(my_land_transfer_ownership_form)
        return on_click

    # Query the land under feet
    def land_info(self, player: Player) -> None:
        player_pos = [math.floor(player.location.x), math.floor(player.location.z)]
        player_dimension = player.dimension.name
        land_info_form = ActionForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "land_info_form.title")}',
            on_close=self.back_to_main_form
        )
        land_info_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                  icon='textures/ui/refresh_light', on_click=self.back_to_main_form)
        flag = True
        for land_owner, land in self.land_data.items():
            if not flag:
                break
            for land_name, land_info in land.items():
                if not flag:
                    break
                range = []
                it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                for i in it:
                    range.append(int(i.group()))
                if (min(range[0], range[2]) <= player_pos[0] <= max(range[0], range[2])
                        and min(range[1], range[3]) <= player_pos[1] <= max(range[1], range[3])
                        and player_dimension == land_info['dimension']):
                    land_info_form.content = (f'{ColorFormat.YELLOW}{self.get_text(player, "owner")}: '
                                              f'{ColorFormat.WHITE}{land_owner}\n'
                                                f'{ColorFormat.YELLOW}{self.get_text(player, "land_name")}: '
                                              f'{ColorFormat.WHITE}{land_name}\n'
                                               f'{ColorFormat.YELLOW}{self.get_text(player, "dimension")}: '
                                              f'{ColorFormat.WHITE}{land_info["dimension"]}\n'
                                               f'{ColorFormat.YELLOW}{self.get_text(player, "range")}: '
                                              f'{ColorFormat.WHITE}{land_info["range"]}\n'
                                               f'{ColorFormat.YELLOW}{self.get_text(player, "area")}: '
                                              f'{ColorFormat.WHITE}{land_info["area"]}\n'
                                               f'{ColorFormat.YELLOW}{self.get_text(player, "land_buy_expense")}: '
                                              f'{ColorFormat.WHITE}{land_info["land_expense"]}\n'
                                               f'{ColorFormat.YELLOW}{self.get_text(player, "creation_time")}: '
                                              f'{ColorFormat.WHITE}{land_info["land_buy_time"]}\n'
                                               f'{ColorFormat.YELLOW}{self.get_text(player, "teleport_point")}: '
                                              f'{ColorFormat.WHITE}({land_info["land_tp"][0]}, {land_info["land_tp"][1]}, {land_info["land_tp"][2]})\n'
                                               f'{ColorFormat.YELLOW}{self.get_text(player, "members")}: '
                                              f'{ColorFormat.WHITE}')
                    permissions = land_info['permissions']
                    if len(permissions) == 0:
                        land_info_form.content += self.get_text(player, "none")
                    else:
                        land_info_form.content += ', '.join(permissions)
                    player.send_form(land_info_form)
                    flag = False
                    break
        else:
            player.send_message(f'{ColorFormat.RED}{self.get_text(player, "land_info.message.fail")}: '
                                f'{ColorFormat.WHITE}{self.get_text(player, "land_info.message.fail.reason")}')

    # Server public lands
    def server_public_land(self, player: Player) -> None:
        server_public_land_form = ActionForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "server_public_land_form.title")}',
            content=f'{ColorFormat.GREEN}{self.get_text(player, "server_public_land_form.content")}',
            on_close=self.back_to_main_form
        )
        for land_owner, land in self.land_data.items():
            for land_name, land_info in land.items():
                range = []
                it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                for i in it:
                    range.append(int(i.group()))
                if land_info['public_land']:
                    server_public_land_form.add_button(f'{land_name}\n{ColorFormat.YELLOW}[{self.get_text(player, "owner")}] {land_owner}',
                                                       icon='textures/ui/icon_spring',
                                                       on_click=self.server_public_land_details(land_owner, land_name, land_info['dimension'], land_info['range'],
                                                                                                land_info['area'], land_info['land_tp'], land_info['permissions']))
        server_public_land_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                           icon='textures/ui/refresh_light', on_click=self.back_to_main_form)
        player.send_form(server_public_land_form)

    # Server public lands -- details
    def server_public_land_details(self, land_owner, land_name, land_dimension, land_range, land_area, land_tp, land_permissions):
        def on_click(player: Player):
            server_public_land_details_form = ActionForm(
                title=land_name,
                content=f'{ColorFormat.YELLOW}{self.get_text(player, "owner")}: '
                        f'{ColorFormat.WHITE}{land_owner}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "dimension")}: '
                        f'{ColorFormat.WHITE}{land_dimension}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "range")}: '
                        f'{ColorFormat.WHITE}{land_range}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "area")}: '
                        f'{ColorFormat.WHITE}{land_area}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "teleport_point")}: '
                        f'{ColorFormat.WHITE}({land_tp[0]}, {land_tp[1]}, {land_tp[2]})\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "members")}: '
                        f'{ColorFormat.WHITE}',
                on_close=self.server_public_land
            )
            if len(land_permissions) == 0:
                server_public_land_details_form.content += self.get_text(player, "none")
            else:
                server_public_land_details_form.content += ', '.join(land_permissions)
            server_public_land_details_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "server_public_land_form.button.tp")}',
                                                       icon='textures/ui/realmsIcon', on_click=self.tp_to_my_land(land_tp, land_dimension))
            server_public_land_details_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                                       icon='textures/ui/refresh_light', on_click=self.server_public_land)
            player.send_form(server_public_land_details_form)
        return on_click

    # save land.json
    def save_land_data(self) -> None:
        with open(land_data_file_path, 'w+', encoding='utf-8') as f:
            json_str = json.dumps(self.land_data, indent=4, ensure_ascii=False)
            f.write(json_str)

    # Reload configurations
    def reload_config_data(self, player: Player) -> None:
        land_system_config_form = ActionForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "reload_config_form.title")}',
            content=f'{ColorFormat.GREEN}{self.get_text(player, "reload_config_form.content")}',
            on_close=self.back_to_main_form
        )
        land_system_config_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "reload_config_form.button.reload_global_config")}',
                                           icon='textures/ui/settings_glyph_color_2x', on_click=self.reload_global_config)
        land_system_config_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "reload_config_form.button.reload_land_data")}',
                                           icon='textures/ui/settings_glyph_color_2x', on_click=self.reload_land_data)
        land_system_config_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                           icon='textures/ui/refresh_light', on_click=self.back_to_main_form)
        player.send_form(land_system_config_form)

    # Reload global configurations
    def reload_global_config(self, player: Player) -> None:
        textinput1 = TextInput(
            label=f'{ColorFormat.YELLOW}{self.get_text(player, "reload_global_config_form.textinput_1.label")}: '
                  f'{ColorFormat.WHITE}{self.config_data["land_buy_price"]}',
            placeholder=f'{self.get_text(player, "reload_global_config_form.textinput_1.placeholder")}',
            default_value=f'{self.config_data["land_buy_price"]}'
        )
        textinput2 = TextInput(
            label=f'{ColorFormat.YELLOW}{self.get_text(player, "reload_global_config_form.textinput_2.label")}: '
                  f'{ColorFormat.WHITE}{self.config_data["land_create_timeout"]} (s)',
            placeholder=f'{self.get_text(player, "reload_global_config_form.textinput_2.placeholder")}',
            default_value=f'{self.config_data["land_create_timeout"]}'
        )
        textinput3 = TextInput(
            label=f'{ColorFormat.YELLOW}{self.get_text(player, "reload_global_config_form.textinput_3.label")}: '
                  f'{ColorFormat.WHITE}{self.config_data["max_area"]}',
            placeholder=f'{self.get_text(player, "reload_global_config_form.textinput_3.placeholder")}',
            default_value=f'{self.config_data["max_area"]}'
        )
        textinput4 = TextInput(
            label=f'{ColorFormat.YELLOW}{self.get_text(player, "reload_global_config_form.textinput_4.label")}: '
                  f'{ColorFormat.WHITE}{self.config_data["max_land_per_player"]}',
            placeholder=f'{self.get_text(player, "reload_global_config_form.textinput_4.placeholder")}',
            default_value=f'{self.config_data["max_land_per_player"]}'
        )
        toggle = Toggle(
            label=f'{ColorFormat.YELLOW}{self.get_text(player, "reload_global_config_form.toggle.label")}'
        )
        if self.config_data['is_land_sell_rate_on']:
            toggle.default_value = True
        else:
            toggle.default_value = False
        textinput5 = TextInput(
            label=f'{ColorFormat.YELLOW}{self.get_text(player, "reload_global_config_form.textinput_5.label")}: '
                  f'{ColorFormat.WHITE}{self.config_data["land_sell_cool_down_timeout"]} (d)',
            placeholder=f'{self.get_text(player, "reload_global_config_form.textinput_5.placeholder")}',
            default_value=f'{self.config_data["land_sell_cool_down_timeout"]}'
        )
        reload_config_data_form = ModalForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "reload_global_config_form.title")}',
            controls=[textinput1, textinput2, textinput3, textinput4, toggle, textinput5],
            submit_button=f'{ColorFormat.YELLOW}{self.get_text(player, "reload_global_config_form.submit_button")}',
            on_close=self.back_to_main_form
        )
        def on_submit(player: Player, json_str: str):
            data = json.loads(json_str)
            try:
                update_land_buy_price = int(data[0])
                update_land_create_timeout = int(data[1])
                update_max_area = int(data[2])
                update_max_land_per_player = int(data[3])
                update_land_sell_cool_down_timeout = int(data[5])
            except ValueError:
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "message.type_error")}')
                return
            if (update_land_buy_price <= 0 or update_land_create_timeout < 30
                    or update_max_area < 4 or update_max_land_per_player <= 0
                    or update_land_sell_cool_down_timeout < 1):
                player.send_message(f'{ColorFormat.RED}{self.get_text(player, "message.type_error")}')
                return
            self.config_data['land_buy_price'] = update_land_buy_price
            self.config_data['land_create_timeout'] = update_land_create_timeout
            self.config_data['max_area'] = update_max_area
            self.config_data['max_land_per_player'] = update_max_land_per_player
            self.config_data['land_sell_cool_down_timeout'] = update_land_sell_cool_down_timeout
            if data[4]:
                self.config_data['is_land_sell_rate_on'] = True
            else:
                self.config_data['is_land_sell_rate_on'] = False
            with open(config_data_file_path, 'w+', encoding='utf-8') as f:
                json_str = json.dumps(self.config_data, indent=4, ensure_ascii=False)
                f.write(json_str)
            player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "reload_global_config.message.success")}')
        reload_config_data_form.on_submit = on_submit
        player.send_form(reload_config_data_form)

    # Reload land data
    def reload_land_data(self, player: Player) -> None:
        with open(land_data_file_path, 'r', encoding='utf-8') as f:
            self.land_data = json.loads(f.read())
        player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "reload_land_data.message.success")}')

    # Manage all lands (operators)
    def manage_all_lands(self, player: Player) -> None:
        manage_all_lands_form = ActionForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "manage_land_form.title")}',
            content=f'{ColorFormat.GREEN}{self.get_text(player, "manage_land_form.content")}',
            on_close=self.back_to_main_form
        )
        for land_owner, land in self.land_data.items():
            for land_name, land_info in land.items():
                dimension = land_info['dimension']
                range = land_info['range']
                area = land_info['area']
                land_expense = land_info['land_expense']
                land_buy_time = land_info['land_buy_time']
                land_tp = land_info['land_tp']
                permissions = land_info['permissions']
                manage_all_lands_form.add_button(f'{land_name}\n{ColorFormat.YELLOW}[{self.get_text(player, "owner")}] {land_owner}',
                                                 icon='textures/ui/icon_spring',
                                                 on_click=self.manage_land_detail(
                    land_owner, land_name, dimension, range, area, land_expense, land_buy_time, land_tp, permissions
                ))
        manage_all_lands_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                         icon='textures/ui/refresh_light', on_click=self.back_to_main_form)
        player.send_form(manage_all_lands_form)

    def manage_land_detail(self, land_owner, land_name, dimension, range, area, land_expense, land_buy_time, land_tp, permissions):
        def on_click(player: Player):
            manage_land_detail_form = ActionForm(
                title=land_name,
                content=f'{ColorFormat.YELLOW}{self.get_text(player, "owner")}: '
                        f'{ColorFormat.WHITE}{land_owner}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "dimension")}: '
                        f'{ColorFormat.WHITE}{dimension}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "range")}: '
                        f'{ColorFormat.WHITE}{range}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "area")}: '
                        f'{ColorFormat.WHITE}{area}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "land_buy_expense")}: '
                        f'{ColorFormat.WHITE}{land_expense}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "creation_time")}: '
                        f'{ColorFormat.WHITE}{land_buy_time}\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "teleport_point")}: '
                        f'{ColorFormat.WHITE}({land_tp[0]}, {land_tp[1]}, {land_tp[2]})\n'
                        f'{ColorFormat.YELLOW}{self.get_text(player, "members")}: '
                        f'{ColorFormat.WHITE}',
                on_close=self.manage_all_lands
            )
            if len(permissions) == 0:
                manage_land_detail_form.content += self.get_text(player, "none")
            else:
                manage_land_detail_form.content += ', '.join(permissions)
            manage_land_detail_form.content += f'\n\n{ColorFormat.GREEN}{self.get_text(player, "manage_land_detail_form.content")}'
            manage_land_detail_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "manage_land_detail_form.button.tp")}',
                                               icon='textures/ui/realmsIcon', on_click=self.tp_to_my_land(land_tp, dimension))
            manage_land_detail_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "manage_land_detail_form.button.land_delete")}',
                                               icon='textures/ui/cancel', on_click=self.manage_land_delete(land_owner, land_name))
            manage_land_detail_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                               icon='textures/ui/refresh_light', on_click=self.manage_all_lands)
            player.send_form(manage_land_detail_form)
        return on_click

    # Force to delte a land
    def manage_land_delete(self, land_owner, land_name):
        def on_click(player: Player):
            confirm_form= ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}{self.get_text(player, "manage_land_delete_form.title")}',
                content=f'{ColorFormat.GREEN}{self.get_text(player, "manage_land_delete_form.content")}\n'
                        f'{self.get_text(player, "owner")}: '
                        f'{ColorFormat.WHITE}{land_owner}\n'
                        f'{ColorFormat.GREEN}{self.get_text(player, "land_name")}: '
                        f'{ColorFormat.WHITE}{land_name}',
                on_close=self.manage_all_lands
            )
            confirm_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "manage_land_delete_form.button.confirm")}',
                                    icon='textures/ui/realms_slot_check', on_click=self.manage_land_delete_confirm(land_owner, land_name))
            confirm_form.add_button(f'{ColorFormat.YELLOW}{self.get_text(player, "button.back")}',
                                    icon='textures/ui/refresh_light', on_click=self.manage_all_lands)
            player.send_form(confirm_form)
        return on_click

    def manage_land_delete_confirm(self, land_owner, land_name):
        def on_click(player: Player):
            self.land_data[land_owner].pop(land_name)
            self.save_land_data()
            player.send_message(f'{ColorFormat.YELLOW}{self.get_text(player, "manage_land_delete.message.success")}')
        return on_click

    # Get text
    def get_text(self, player: Player, text_key: str) -> str:
        try:
            lang = player.locale
            if self.lang_data.get(lang) is None:
                text_value = self.lang_data['en_US'][text_key]
            else:
                if self.lang_data[lang].get(text_key) is None:
                    text_value = self.lang_data['en_US'][text_key]
                else:
                    text_value = self.lang_data[lang][text_key]
            return text_value
        except:
            return text_key

    # Monitor the player's position.
    def check_player_pos(self) -> None:
        if len(self.server.online_players) == 0:
            return
        for online_player in self.server.online_players:
            player_pos = [math.floor(online_player.location.x), math.floor(online_player.location.z)]
            player_dimension = online_player.dimension.name
            flag = True
            for land_owner, land in self.land_data.items():
                if not flag:
                    break
                for land_name, land_info in land.items():
                    range = []
                    it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                    for i in it:
                        range.append(int(i.group()))
                    if (min(range[0], range[2]) <= player_pos[0] <= max(range[0], range[2])
                            and min(range[1], range[3]) <= player_pos[1] <= max(range[1], range[3])
                            and player_dimension == land_info['dimension']):
                        online_player.send_tip(ColorFormat.YELLOW +
                                               self.get_text(online_player, "tip").format(land_name, land_owner))
                        flag = False
                        break

    def back_to_main_form(self, player: Player) -> None:
        player.perform_command('ul')

    def back_to_menu(self, player: Player) -> None:
        player.perform_command('cd')

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        if not self.land_data.get(event.player.name):
            self.land_data[event.player.name] = {}
            self.save_land_data()

    # Monitor the player's breaking blocks.
    @event_handler
    def on_block_break(self, event: BlockBreakEvent):
        if event.player.is_op and event.player.game_mode.value == 1:
            return
        block_pos = [math.floor(event.block.location.x), math.floor(event.block.location.z)]
        block_dimension = event.block.dimension.name
        source_player = event.player
        for land_owner, land in self.land_data.items():
            for land_info in land.values():
                range = []
                it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                for i in it:
                    range.append(int(i.group()))
                if (min(range[0], range[2]) <= block_pos[0] <= max(range[0], range[2])
                        and min(range[1], range[3]) <= block_pos[1] <= max(range[1], range[3])
                        and block_dimension == land_info['dimension']
                        and land_info['anti_break_block']
                        and (source_player.name != land_owner and source_player.name not in land_info['permissions'])):
                    event.player.send_message(f'{ColorFormat.RED}{self.get_text(event.player, "message.on_block_break")}')
                    event.is_cancelled = True

    # Monitor the generation of lightning bolt.
    @event_handler
    def on_mob_spawn(self, event: ActorSpawnEvent):
        if event.actor.name == 'Lightning Bolt':
            actor_pos = [math.floor(event.actor.location.x), math.floor(event.actor.location.z)]
            actor_dimension = event.actor.dimension.name
            for land in self.land_data.values():
                for land_info in land.values():
                    range =[]
                    it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                    for i in it:
                        range.append(int(i.group()))
                    land_len_x = round(abs(range[0] - range[2]) / 2)
                    land_len_z = round(abs(range[1] - range[3]) / 2)
                    land_center_x = min(range[0], range[2]) + land_len_x
                    land_center_z = min(range[1], range[3]) + land_len_z
                    if land_info['fire_protect'] == True and event.actor.name == 'Lightning Bolt':
                        prevent_l_bolt_dx = land_len_x + 3
                        prevent_l_bolt_dz = land_len_z + 3
                        prevent_l_bolt_posa = [land_center_x + prevent_l_bolt_dx, land_center_z + prevent_l_bolt_dz]
                        prevent_l_bolt_posb = [land_center_x - prevent_l_bolt_dx, land_center_z - prevent_l_bolt_dz]
                        if (min(prevent_l_bolt_posa[0], prevent_l_bolt_posb[0]) <= actor_pos[0] <= max(prevent_l_bolt_posa[0], prevent_l_bolt_posb[0])
                                and min(prevent_l_bolt_posa[1], prevent_l_bolt_posb[1]) <= actor_pos[1] <= max(prevent_l_bolt_posa[1], prevent_l_bolt_posb[1])
                                and actor_dimension == land_info['dimension']):
                            event.is_cancelled = True

    # Monitor the player's attacks.
    @event_handler
    def on_player_attack(self, event: ActorDamageEvent):
        damage_source = event.damage_source.actor
        if not isinstance(damage_source, Player):
            return
        source_player = damage_source
        if source_player.is_op and source_player.game_mode.value == 1:
            return
        actor_under_attack_pos = [math.floor(event.actor.location.x), math.floor(event.actor.location.z)]
        actor_under_attack_dimension = event.actor.dimension.name
        for land_owner, land in self.land_data.items():
            for land_info in land.values():
                range = []
                it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                for i in it:
                    range.append(int(i.group()))
                if (min(range[0], range[2]) <= actor_under_attack_pos[0] <= max(range[0], range[2])
                        and min(range[1], range[3]) <= actor_under_attack_pos[1] <= max(range[1], range[3])
                        and actor_under_attack_dimension == land_info['dimension']
                        and land_info['anti_player_attack']
                        and (source_player.name != land_owner and source_player.name not in land_info['permissions'])):
                    source_player.send_message(f'{ColorFormat.RED}{self.get_text(source_player, "message.on_player_attack")}')
                    event.is_cancelled = True

    # Monitor the player's right-clicking on blocks.
    @event_handler
    def on_player_right_click_block(self, event: PlayerInteractEvent):
        if event.player.is_op and event.player.game_mode.value == 1:
            return
        block_pos = [math.floor(event.block.location.x),math.floor(event.block.location.z)]
        block_dimension = event.block.dimension.name
        source_player = event.player
        for land_owner, land in self.land_data.items():
            for land_info in land.values():
                range = []
                it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                for i in it:
                    range.append(int(i.group()))
                if (min(range[0], range[2]) <= block_pos[0] <= max(range[0], range[2])
                        and min(range[1], range[3]) <= block_pos[1] <= max(range[1], range[3])
                        and block_dimension == land_info['dimension']
                        and land_info['anti_right_click_block']
                        and (source_player.name != land_owner and source_player.name not in land_info['permissions'])):
                    source_player.send_message(f'{ColorFormat.RED}{self.get_text(source_player, "message.on_player_right_click_block")}')
                    event.is_cancelled = True

    # Monitor the player's right-clicking on entities.
    @event_handler
    def on_player_right_click_entity(self, event: PlayerInteractActorEvent):
        if event.player.is_op and event.player.game_mode.value == 1:
            return
        actor_pos = [math.floor(event.actor.location.x), math.floor(event.actor.location.z)]
        actor_dimension = event.actor.dimension.name
        source_player = event.player
        for land_owner, land in self.land_data.items():
            for land_info in land.values():
                range = []
                it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                for i in it:
                    range.append(int(i.group()))
                if (min(range[0], range[2]) <= actor_pos[0] <= max(range[0], range[2])
                        and min(range[1], range[3]) <= actor_pos[1] <= max(range[1], range[3])
                        and actor_dimension == land_info['dimension']
                        and land_info['anti_right_click_entity']
                        and (source_player.name != land_owner and source_player.name not in land_info['permissions'])):
                    source_player.send_message(f'{ColorFormat.RED}{self.get_text(source_player, "message.on_player_right_click_entity")}')
                    event.is_cancelled = True

    # Monitor the explosions.
    @event_handler
    def on_mob_explode(self, event: ActorExplodeEvent):
        for land in self.land_data.values():
            for land_info in land.values():
                range = []
                it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                for i in it:
                    range.append(int(i.group()))
                for block in event.block_list:
                    if (min(range[0], range[2]) <= math.floor(block.location.x) <= max(range[0], range[2])
                            and min(range[1], range[3]) <= math.floor(block.location.z) <= max(range[1], range[3])
                            and block.dimension.name == land_info['dimension']
                            and land_info['explode_protect']):
                        event.is_cancelled = True

    # Scheduled tasks
    # - Land fire protection
    # - Prevent withers from entering land
    def land_protect_task(self) -> None:
        if len(self.server.online_players) == 0:
            return
        for land in self.land_data.values():
            for land_info in land.values():
                range = []
                it = re.finditer(r'[-+]?\d+(?:\.\d+)?', land_info['range'])
                for i in it:
                    range.append(int(i.group()))
                land_dimension = land_info['dimension']
                if land_dimension == 'Overworld':
                    execute_dimension = 'overworld'
                elif land_dimension == 'Nether':
                    execute_dimension = 'nether'
                else:
                    execute_dimension = 'the_end'
                land_len_x = round(abs(range[0] - range[2]) / 2)
                land_len_z = round(abs(range[1] - range[3]) / 2)
                land_center_x = min(range[0], range[2]) + land_len_x
                land_center_z = min(range[1], range[3]) + land_len_z
                if land_info['fire_protect']:
                    fire_ball_protect_dx = land_len_x + 5
                    fire_ball_protect_dz = land_len_z + 5
                    fire_ball_protect_posa = [land_center_x + fire_ball_protect_dx, land_center_z + fire_ball_protect_dz]
                    self.server.dispatch_command(self.CommandSenderWrapper, f'execute in {execute_dimension} run '
                                                                            f'kill @e[type=small_fireball, x={fire_ball_protect_posa[0]}, y=320, z={fire_ball_protect_posa[1]}, '
                                                                            f'dx={-fire_ball_protect_dx*2}, dy=-384, dz={-fire_ball_protect_dz*2}]')
                    self.server.dispatch_command(self.CommandSenderWrapper, f'execute in {execute_dimension} run '
                                                                            f'kill @e[type=fireball, x={fire_ball_protect_posa[0]}, y=320, z={fire_ball_protect_posa[1]}, '
                                                                            f'dx={-fire_ball_protect_dx * 2}, dy=-384, dz={-fire_ball_protect_dz * 2}]')
                if land_info['anti_wither_enter']:
                    wither_protect_dx = land_len_x + 3
                    wither_protect_dz = land_len_z + 3
                    wither_protect_posa = [land_center_x + wither_protect_dx, land_center_z + wither_protect_dz]
                    self.server.dispatch_command(self.CommandSenderWrapper, f'execute in {execute_dimension} run '
                                                                            f'tp @e[type=wither, x={wither_protect_posa[0]}, y=320, z={wither_protect_posa[1]}, '
                                                                            f'dx={-wither_protect_dx*2}, dy=-384, dz={-wither_protect_dx*2}] 0 -100 0')
                    self.server.dispatch_command(self.CommandSenderWrapper, f'execute in {execute_dimension} run '
                                                                            f'kill @e[type=wither, x=0, y=-100, z=0, r=20]')