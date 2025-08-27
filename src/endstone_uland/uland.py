import os
import time
import json
import math
import hashlib
import datetime

from endstone import Player, ColorFormat
from endstone.event import *
from endstone.plugin import Plugin
from endstone.command import Command, CommandSender, CommandSenderWrapper
from endstone.form import ActionForm, ModalForm, TextInput, Dropdown, Toggle
from endstone.scheduler import Task
from endstone.level import Location

from endstone_uland.lang import load_lang_data


current_dir = os.getcwd()

first_dir = os.path.join(current_dir, 'plugins', 'uland')

if not os.path.exists(first_dir):
    os.mkdir(first_dir)

land_data_file_path = os.path.join(first_dir, 'land.json')

config_data_file_path = os.path.join(first_dir, 'config.json')

lang_dir = os.path.join(first_dir, 'lang')

if not os.path.exists(lang_dir):
    os.mkdir(lang_dir)


class uland(Plugin):
    api_version = '0.10'

    def __init__(self):
        super().__init__()

        if not os.path.exists(land_data_file_path):
            with open(land_data_file_path, 'w', encoding='utf-8') as f:
                land_data = {}
                json_str = json.dumps(land_data, indent=4, ensure_ascii=False)
                f.write(json_str)
        else:
            with open(land_data_file_path, 'r', encoding='utf-8') as f:
                land_data = json.loads(f.read())
        self.land_data = land_data

        # Load config data
        if not os.path.exists(config_data_file_path):
            with open(config_data_file_path, 'w', encoding='utf-8') as f:
                config_data = {
                    'max_land_num_can_per_player_has': 5,
                    'create_a_new_land_time_limit': 60,
                    'max_area_can_per_land_achieve': 10000,
                    'price_for_per_square_block': 10,
                    'selling_price_for_per_square_block': 5
                }
                json_str = json.dumps(config_data, indent=4, ensure_ascii=False)
                f.write(json_str)
        else:
            with open(config_data_file_path, 'r', encoding='utf-8') as f:
                config_data = json.loads(f.read())
        self.config_data = config_data

        # Load lang data
        self.lang_data = load_lang_data(lang_dir)

        # recorder of creating a new land
        self.create_a_new_land_recorder = {}

    def on_enable(self):
        if self.server.plugin_manager.get_plugin('umoney') is None:
            self.logger.error(
                f'{ColorFormat.RED}'
                f'Pre-plugin UMoney is required...'
            )

            self.server.plugin_manager.disable_plugin(self)

            return

        self.register_events(self)

        self.server.scheduler.run_task(self, self.show_land_tip, delay=0, period=20)

        self.command_sender = CommandSenderWrapper(
            sender=self.server.command_sender,
            on_message=None
        )

        self.server.scheduler.run_task(self, self.fuck_wither, delay=0, period=20)

        self.logger.info(
            f'{ColorFormat.YELLOW}'
            f'ULand is enabled...'
        )

    commands = {
        'ul': {
            'description': 'Call out the main form of ULand',
            'usages': ['/ul'],
            'permissions': ['uland.command.ul']
        },
        'posa': {
            'description': 'Select point A or update selected point A',
            'usages': ['/posa'],
            'permissions': ['uland.command.posa']
        },
        'posb': {
            'description': 'Select point B',
            'usages': ['/posb'],
            'permissions': ['uland.command.posb']
        }
    }

    permissions = {
        'uland.command.ul': {
            'description': 'Call out the main form of ULand',
            'default': True
        },
        'uland.command.posa': {
            'description': 'Select point A or update selected point A',
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
                sender.send_message(
                    f'{ColorFormat.RED}'
                    f'This command can only be executed by a player...'
                )

                return

            player_money = self.server.plugin_manager.get_plugin('umoney').api_get_player_money(sender.name)

            main_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(sender, "main_form.title")}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(sender, "player_money")}: '
                        f'{ColorFormat.WHITE}'
                        f'{player_money}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(sender, "main_form.content")}'
            )

            main_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(sender, "main_form.button.create_a_new_land")}',
                icon='textures/ui/color_plus',
                on_click=self.create_a_new_land
            )

            main_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(sender, "main_form.button.lands")}',
                icon='textures/ui/icon_new',
                on_click=self.lands
            )

            main_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(sender, "main_form.button.public_lands")}',
                icon='textures/ui/mashup_world',
                on_click=self.public_lands
            )

            if sender.is_op:
                main_form.add_button(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(sender, "main_form.button.manage_lands")}',
                    icon='textures/ui/op',
                    on_click=self.manage_lands
                )

                main_form.add_button(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(sender, "main_form.button.reload_config")}',
                    icon='textures/ui/icon_setting',
                    on_click=self.reload_configurations
                )

            if self.server.plugin_manager.get_plugin('zx_ui') is None:
                main_form.add_button(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(sender, "button.close")}',
                    icon='textures/ui/cancel',
                    on_click=None
                )

                main_form.on_close = None
            else:
                main_form.add_button(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(sender, "button.back")}',
                    icon='textures/ui/refresh_light',
                    on_click=self.back_to_zx_ui
                )

                main_form.on_close = self.back_to_zx_ui

            sender.send_form(main_form)

        if command.name == 'posa':
            if not isinstance(sender, Player):
                sender.send_message(
                    f'{ColorFormat.RED}'
                    f'This command can only be executed by a player...'
                )

                return

            if self.create_a_new_land_recorder.get(sender.name) is None:
                sender.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(sender, "select_a_point_a.message.fail")}: '
                    f'{ColorFormat.WHITE}'
                    f'{self.get_text(sender, "select_a_point.message.fail.reason1")}'
                )

                return

            posa = [
                math.floor(sender.location.x),
                math.floor(sender.location.y),
                math.floor(sender.location.z)
            ]

            if self.create_a_new_land_recorder[sender.name].get('posa') is not None:
                self.create_a_new_land_recorder[sender.name]['posa'] = posa

                sender.send_message(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(sender, "update_a_point.message.success")}\n'
                    f'({posa[0]}, ~, {posa[2]})'
                )
            else:
                self.create_a_new_land_recorder[sender.name]['posa'] = posa

                sender.send_message(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(sender, "select_a_point.message.success")}\n'
                    f'({posa[0]}, ~, {posa[2]})'
                )

            dim = sender.location.dimension.name

            self.create_a_new_land_recorder[sender.name]['dim'] = dim

        if command.name == 'posb':
            if not isinstance(sender, Player):
                sender.send_message(
                    f'{ColorFormat.RED}'
                    f'This command can only be executed by a player...'
                )

                return

            if self.create_a_new_land_recorder.get(sender.name) is None:
                sender.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(sender, "select_a_point_b.message.fail")}: '
                    f'{ColorFormat.WHITE}'
                    f'{self.get_text(sender, "select_a_point.message.fail.reason1")}'
                )

                return

            if self.create_a_new_land_recorder[sender.name].get('posa') is None:
                sender.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(sender, "select_a_point_b.message.fail")}: '
                    f'{ColorFormat.WHITE}'
                    f'{self.get_text(sender, "select_a_point.message.fail.reason2")}'
                )

                return

            dim = sender.location.dimension.name

            if dim != self.create_a_new_land_recorder[sender.name]['dim']:
                sender.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(sender, "select_a_point_b.message.fail")}: '
                    f'{ColorFormat.WHITE}'
                    f'{self.get_text(sender, "select_a_point.message.fail.reason3")}'
                )

                return

            posb = [
                math.floor(sender.location.x),
                math.floor(sender.location.z)
            ]

            posa = self.create_a_new_land_recorder[sender.name]['posa']

            if posa == posb:
                sender.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(sender, "select_a_point_b.message.fail")}: '
                    f'{ColorFormat.WHITE}'
                    f'{self.get_text(sender, "select_a_point.message.fail.reason4")}'
                )

                return

            self.create_a_new_land_recorder[sender.name]['posb'] = posb

    def create_a_new_land(self, player: Player):
        max_land_num_can_per_player_has = self.config_data['max_land_num_can_per_player_has']

        land_num_belong_to_this_player = len(self.land_data[player.name].keys())

        if land_num_belong_to_this_player >= max_land_num_can_per_player_has:
            player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(player, "create_a_new_land.message.fail")}: '
                f'{ColorFormat.WHITE}'
                f'{self.get_text(player, "create_a_new_land.message.fail.reason1").format(max_land_num_can_per_player_has)}'
            )

            return

        if self.create_a_new_land_recorder.get(player.name) is None:
            self.create_a_new_land_recorder[player.name] = {}

            start_time = round(time.time())

            self.create_a_new_land_recorder[player.name]['start_time'] = start_time

            task = self.server.scheduler.run_task(
                self,
                lambda x=player: self.create_a_new_land_task(player),
                delay=0,
                period=20
            )

            self.create_a_new_land_recorder[player.name]['task'] = task

            player.send_message(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "create_a_new_land.message.start.text1").format(self.config_data["create_a_new_land_time_limit"])}\n'
                f'\n'
                f'{self.get_text(player, "create_a_new_land.message.start.text2")}\n'
                f'{self.get_text(player, "create_a_new_land.message.start.text3")}\n'
                f'\n'
                f'{self.get_text(player, "create_a_new_land.message.start.text4")}'
            )
        else:
            player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(player, "create_a_new_land.message.fail")}: '
                f'{ColorFormat.WHITE}'
                f'{self.get_text(player, "create_a_new_land.message.fail.reason2")}'
            )

            return

    def create_a_new_land_task(self, player: Player):
        start_time: int = self.create_a_new_land_recorder[player.name]['start_time']

        current_time = round(time.time())

        expense_time = current_time - start_time

        if (
            expense_time > self.config_data['create_a_new_land_time_limit']
            and
            len(self.create_a_new_land_recorder[player.name]) < 5
        ):
            task: Task = self.create_a_new_land_recorder[player.name]['task']

            self.server.scheduler.cancel_task(task.task_id)

            self.create_a_new_land_recorder.pop(player.name)

            player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(player, "create_a_new_land.message.fail")}: '
                f'{ColorFormat.WHITE}'
                f'{self.get_text(player, "create_a_new_land_message.fail.reason3")}'
            )

            return

        if len(self.create_a_new_land_recorder[player.name]) == 5:
            task: Task = self.create_a_new_land_recorder[player.name]['task']

            self.server.scheduler.cancel_task(task.task_id)

            self.create_a_new_land_further(player)

    def create_a_new_land_further(self, player: Player):
        posa = self.create_a_new_land_recorder[player.name]['posa']

        posa_c = [posa[0], posa[2]]

        posb = self.create_a_new_land_recorder[player.name]['posb']

        dim = self.create_a_new_land_recorder[player.name]['dim']

        for lands in self.land_data.values():
            for land_info in lands.values():
                land_posa = land_info['posa']

                land_posb = land_info['posb']

                land_range = [land_posa, land_posb]

                land_dim = land_info['dim']

                if dim == land_dim:
                    if (
                            (
                                (
                                    min(land_range[0][0], land_range[1][0]) <= posa_c[0] <= max(land_range[0][0], land_range[1][0])
                                    and
                                    min(land_range[0][1], land_range[1][1]) <= posa_c[1] <= max(land_range[0][1], land_range[1][1])
                                )
                                or
                                (
                                    min(land_range[0][0], land_range[1][0]) <= posb[0] <= max(land_range[0][0], land_range[1][0])
                                    and
                                    min(land_range[0][1], land_range[1][1]) <= posb[1] <= max(land_range[0][1], land_range[1][1])
                                )

                            )
                            or
                            (
                                (
                                    min(posa_c[0], posb[0]) <= land_range[0][0] <= max(posa_c[0], posb[0])
                                    and
                                    min(posa_c[1], posb[1]) <= land_range[0][1] <= max(posa_c[1], posb[1])
                                )
                                and
                                (
                                    min(posa_c[0], posb[0]) <= land_range[1][0] <= max(posa_c[0], posb[0])
                                    and
                                    min(posa_c[1], posb[1]) <= land_range[1][1] <= max(posa_c[1], posb[1])
                                )
                            )

                    ):
                        self.create_a_new_land_recorder.pop(player.name)

                        player.send_message(
                            f'{ColorFormat.RED}'
                            f'{self.get_text(player, "create_a_new_land.message.fail")}: '
                            f'{ColorFormat.WHITE}'
                            f'{self.get_text(player, "create_a_new_land_message.fail.reason4")}'
                        )

                        return

        length = abs(posa[0] - posb[0])

        width = abs(posa[2] - posb[1])

        area = length * width

        if area < 4:
            self.create_a_new_land_recorder.pop(player.name)

            player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(player, "create_a_new_land.message.fail")}: '
                f'{ColorFormat.WHITE}'
                f'{self.get_text(player, "create_a_new_land_message.fail.reason5")}'
            )

            return

        max_area_can_per_land_achieve = self.config_data['max_area_can_per_land_achieve']

        if area > max_area_can_per_land_achieve:
            self.create_a_new_land_recorder.pop(player.name)

            player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(player, "create_a_new_land.message.fail")}: '
                f'{ColorFormat.WHITE}'
                f'{self.get_text(player, "create_a_new_land_message.fail.reason6").format(max_area_can_per_land_achieve)}'
            )

            return

        price = area * self.config_data['price_for_per_square_block']

        player_money = self.server.plugin_manager.get_plugin('umoney').api_get_player_money(player.name)

        over = price - player_money

        if player_money < price:
            player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(player, "create_a_new_land.message.fail")}: '
                f'{ColorFormat.WHITE}'
                f'{self.get_text(player, "create_a_new_land_message.fail.reason7").format(over)}'
            )

            return

        hash_object = hashlib.sha256(str(datetime.datetime.now()).encode())
        hex_dig = hash_object.hexdigest()

        textinput = TextInput(
            label=f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "dim")}: '
                  f'{ColorFormat.WHITE}'
                  f'{dim}\n'
                  f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "range")}: '
                  f'{ColorFormat.WHITE}'
                  f'({posa[0]}, ~, {posa[2]}) - ({posb[0]}, ~, {posb[1]})\n'
                  f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "area")}: '
                  f'{ColorFormat.WHITE}'
                  f'{area}\n'
                  f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "price")}: '
                  f'{ColorFormat.WHITE}'
                  f'{price}\n'
                  f'\n'
                  f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "create_a_new_land_further_form.textinput")}',
            placeholder=self.get_text(player, "create_a_new_land_further_form.textinput.placeholder"),
            default_value=self.get_text(player, "create_a_new_land_further_form.textinput.default_value").format(player.name)
        )

        create_a_new_land_further_form = ModalForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                  f'{self.get_text(player, "create_a_new_land_further_form.title")}',
            controls=[textinput],
            submit_button=f'{ColorFormat.YELLOW}'
                          f'{self.get_text(player, "create_a_new_land_further_form.submit_button")}',
            on_close=self.cancel_create_a_new_land
        )

        def on_submit(p: Player, json_str: str):
            data = json.loads(json_str)

            if len(data[0]) == 0:
                p.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(p, "message.error")}'
                )

                return

            name = data[0]

            creation_datetime = str(datetime.datetime.now()).split(' ')[0]

            self.land_data[p.name][hex_dig] = {
                'name': name,
                'creation_datetime': creation_datetime,
                'price': price,
                'dim': dim,
                'posa': posa_c,
                'posb': posb,
                'area': area,
                'tp_pos': posa,
                'members': [],
                'security_settings': {
                    'is_land_public': False,
                    'can_thunder_spawn': False,
                    'can_explosion_spawn': False,
                    'can_stranger_place_block': False,
                    'can_stranger_break_block': False,
                    'can_stranger_left_click_block': False,
                    'can_stranger_right_click_block': False,
                    'can_stranger_right_click_entity': False,
                    'can_stranger_damage_player_or_entity': False,
                    'can_fire_damage_player_or_entity': False,
                    'can_poison_effect_applied_to_player_or_entity': False,
                    'can_wither_effect_applied_to_player_or_entity': False,
                    'can_wither_enter_land': False
                }
            }

            self.create_a_new_land_recorder.pop(p.name)

            self.save_land_data()

            p.send_message(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(p, "create_a_new_land.message.success")}'
            )

            self.server.plugin_manager.get_plugin('umoney').api_change_player_money(p.name, -price)

        create_a_new_land_further_form.on_submit = on_submit

        player.send_form(create_a_new_land_further_form)

    def cancel_create_a_new_land(self, player: Player):
        self.create_a_new_land_recorder.pop(player.name)

        self.back_to_main_form(player)

    def lands(self, player: Player):
        lands_form = ActionForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                  f'{self.get_text(player, "lands_form.title")}',
            content=f'{ColorFormat.GREEN}'
                    f'{self.get_text(player, "lands_form.content")}',
            on_close=self.back_to_main_form
        )

        for land_owner, lands in self.land_data.items():
            for land_hex_dig, land_info in lands.items():
                land_members = land_info['members']

                if player.name == land_owner or player.name in land_members:
                    land_name = land_info['name']

                    land_creation_datetime = land_info['creation_datetime']

                    land_price = land_info['price']

                    land_dim = land_info['dim']

                    land_posa = land_info['posa']

                    land_posb = land_info['posb']

                    land_range = f'({land_posa[0]}, ~, {land_posa[1]}) - ({land_posb[0]}, ~, {land_posb[1]})'

                    land_area = land_info['area']

                    land_tp_pos = land_info['tp_pos']

                    button_text = (
                        f'{ColorFormat.YELLOW}'
                        f'{land_name} '
                    )

                    if land_dim == 'Overworld':
                        button_text += (
                            f'{ColorFormat.GREEN}'
                            f'#'
                        )
                    elif land_dim == 'Nether':
                        button_text += (
                            f'{ColorFormat.RED}'
                            f'#'
                        )
                    else:
                        button_text += (
                            f'{ColorFormat.LIGHT_PURPLE}'
                            f'#'
                        )

                    button_text += (
                        f'\n'
                        f'{ColorFormat.YELLOW}'
                        f'[{self.get_text(player, "owner")}] {land_owner}'
                    )

                    if player.name == land_owner:
                        land_type = 'owner'
                    else:
                        land_type = 'member'

                    lands_form.add_button(
                        text=button_text,
                        icon='textures/ui/icon_spring',
                        on_click=self.land(
                            land_owner,
                            land_hex_dig,
                            land_name,
                            land_creation_datetime,
                            land_price,
                            land_dim,
                            land_range,
                            land_area,
                            land_tp_pos,
                            land_members,
                            land_type
                        )
                    )

        lands_form.add_button(
            f'{ColorFormat.YELLOW}'
            f'{self.get_text(player, "button.back")}',
            icon='textures/ui/refresh_light',
            on_click=self.back_to_main_form
        )

        player.send_form(lands_form)

    def land(self, land_owner, land_hex_dig, land_name, land_creation_datetime, land_price, land_dim, land_range, land_area, land_tp_pos, land_members, land_type):
        def on_click(player: Player):
            members = ', '.join(land_members)

            dim = self.get_text(player, land_dim)

            land_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                f'{land_name}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "owner")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_owner}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "creation_datetime")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_creation_datetime}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "dim")}: '
                        f'{ColorFormat.WHITE}'
                        f'{dim}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "range")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_range}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "area")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_area}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "price")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_price}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "members")}: '
                        f'{ColorFormat.WHITE}'
                        f'{members}\n'
                        f'\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "land_form.content")}',
                on_close=self.lands
            )

            land_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_form.button.land_teleport")}',
                icon='textures/ui/realmsIcon',
                on_click=self.land_teleport(land_dim, land_tp_pos)
            )

            if land_type == 'owner':
                land_form.add_button(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(player, "land_form.button.land_settings")}',
                    icon='textures/ui/hammer_l',
                    on_click=self.land_settings(
                        land_hex_dig,
                        land_name,
                        land_price,
                        land_area,
                        land_tp_pos,
                        land_members
                    )
                )

            land_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "button.back")}',
                icon='textures/ui/refresh_light',
                on_click=self.lands
            )

            player.send_form(land_form)

        return on_click

    def land_teleport(self, land_dim, land_tp_pos):
        def on_click(player: Player):
            if land_dim == 'Overworld':
                dim = self.server.level.get_dimension('OVERWORLD')
            elif land_dim == 'Nether':
                dim = self.server.level.get_dimension('NETHER')
            else:
                dim = self.server.level.get_dimension('THEEND')

            location = Location(
                dimension=dim,
                x=float(land_tp_pos[0]),
                y=float(land_tp_pos[1]),
                z=float(land_tp_pos[2])
            )

            player.teleport(location)

            player.send_message(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_teleport.message.success")}'
            )

        return on_click

    def land_settings(self, land_hex_dig, land_name, land_price, land_area, land_tp_pos, land_members):
        def on_click(player: Player):
            land_settings_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "land_settings_form.title")}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "land_settings_form.content").format(land_name)}',
                on_close=self.lands
            )

            land_settings_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_settings_form.button.add_member")}',
                icon='textures/ui/color_plus',
                on_click=self.land_add_member(
                    land_hex_dig,
                    land_name,
                    land_members
                )
            )

            land_settings_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_settings_form.button.remove_member")}',
                icon='textures/ui/dark_minus',
                on_click=self.land_remove_member(
                    land_hex_dig,
                    land_name,
                    land_members
                )
            )

            land_settings_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_settings_form.button.land_rename")}',
                icon='textures/ui/icon_book_writable',
                on_click=self.land_rename(
                    land_hex_dig,
                    land_name
                )
            )

            land_settings_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_settings_form.button.update_teleport_point")}',
                icon='textures/ui/realmsIcon',
                on_click=self.update_teleport_point(
                    land_hex_dig,
                    land_tp_pos
                )
            )

            land_settings_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_settings_form.button.land_security_settings")}',
                icon='textures/ui/recipe_book_icon',
                on_click=self.land_security_settings(land_hex_dig)
            )

            land_settings_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_settings_form.button.land_sell")}',
                icon='textures/ui/trade_icon',
                on_click=self.land_sell(
                    land_hex_dig,
                    land_price,
                    land_area
                )
            )

            land_settings_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_settings_form.button.land_transfer_ownership")}',
                icon='textures/ui/switch_accounts',
                on_click=self.land_transfer_ownership(
                    land_hex_dig,
                    land_name
                )
            )

            land_settings_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "button.back")}',
                icon='textures/ui/refresh_light',
                on_click=self.lands
            )

            player.send_form(land_settings_form)

        return on_click

    def land_add_member(self, land_hex_dig, land_name, land_members):
        def on_click(player: Player):
            player_name_list = []

            for player_name in self.land_data.keys():
                if (
                    player.name != player_name
                    and
                    player_name not in land_members
                ):
                    player_name_list.append(player_name)

            if len(player_name_list) == 0:
                player.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(player, "land_add_member.message.fail")}: '
                    f'{ColorFormat.WHITE}'
                    f'{self.get_text(player, "land_add_member.message.fail.reason")}'
                )

                return

            player_name_list.sort(key=lambda x:x[0].lower(), reverse=False)

            dropdown = Dropdown(
                label=f'{ColorFormat.GREEN}'
                      f'{self.get_text(player, "land_add_member.form.dropdown.label")}',
                options=player_name_list
            )

            land_add_member_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "land_add_member.form.title")}',
                controls=[dropdown],
                submit_button=f'{ColorFormat.YELLOW}'
                              f'{self.get_text(player, "land_add_member.form.submit_button")}',
                on_close=self.lands
            )

            def on_submit(p: Player, json_str: str):
                data = json.loads(json_str)

                new_member_name = player_name_list[data[0]]

                self.land_data[p.name][land_hex_dig]['members'].append(new_member_name)

                self.save_land_data()

                p.send_message(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(p, "land_add_member.message.success")}'
                )

                if self.server.get_player(new_member_name) is not None:
                    new_member = self.server.get_player(new_member_name)

                    new_member.send_message(
                        f'{ColorFormat.YELLOW}'
                        f'{self.get_text(p, "land_add_member.message").format(p.name, land_name)}'
                    )

            land_add_member_form.on_submit = on_submit

            player.send_form(land_add_member_form)

        return on_click

    def land_remove_member(self, land_hex_dig, land_name, land_members):
        def on_click(player: Player):
            if len(land_members) == 0:
                player.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(player, "land_remove_member.message.fail")}: '
                    f'{ColorFormat.WHITE}'
                    f'{self.get_text(player, "land_remove_member.message.fail.reason")}'
                )

                return

            land_members.sort(key=lambda x:x[0].lower(), reverse=False)

            dropdown = Dropdown(
                label=f'{ColorFormat.GREEN}'
                      f'{self.get_text(player, "land_remove_member.form.dropdown.label")}',
                options=land_members
            )

            land_remove_member_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "land_remove_member.form.title")}',
                controls=[dropdown],
                submit_button=f'{ColorFormat.YELLOW}'
                              f'{self.get_text(player, "Remove")}',
                on_close=self.lands
            )

            def on_submit(p: Player, json_str: str):
                data = json.loads(json_str)

                member_name_to_remove = land_members[data[0]]

                self.land_data[p.name][land_hex_dig]['members'].remove(member_name_to_remove)

                self.save_land_data()

                p.send_message(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(p, "land_remove_member.message.success")}'
                )

                if self.server.get_player(member_name_to_remove) is not None:
                    member_to_remove = self.server.get_player(member_name_to_remove)

                    member_to_remove.send_message(
                        f'{ColorFormat.YELLOW}'
                        f'{self.get_text(p, "land_remove_member.message").format(p.name, land_name)}'
                    )

            land_remove_member_form.on_submit = on_submit

            player.send_form(land_remove_member_form)

        return on_click

    def land_rename(self, land_hex_dig, land_name):
        def on_click(player: Player):
            textinput = TextInput(
                label=f'{ColorFormat.GREEN}'
                      f'{self.get_text(player, "land_rename.form.textinput.label")}',
                placeholder=self.get_text(player, "land_rename.form.textinput.placeholder"),
                default_value=land_name
            )

            land_rename_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "land_rename.form.title")}',
                controls=[textinput],
                submit_button=f'{ColorFormat.YELLOW}'
                              f'{self.get_text(player, "land_rename.form.submit_button")}',
                on_close=self.lands
            )

            def on_submit(p: Player, json_str: str):
                data = json.loads(json_str)

                if len(data[0]) == 0:
                    p.send_message(
                        f'{ColorFormat.RED}'
                        f'{self.get_text(p, "message.error")}'
                    )

                    return

                new_land_name = data[0]

                self.land_data[p.name][land_hex_dig]['name'] = new_land_name

                self.save_land_data()

                p.send_message(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(p, "land_rename.message.success")}'
                )

            land_rename_form.on_submit = on_submit

            player.send_form(land_rename_form)

        return on_click

    def update_teleport_point(self, land_hex_dig, land_tp_pos):
        def on_click(player: Player):
            new_land_tp_pos = [
                math.floor(player.location.x),
                math.floor(player.location.y),
                math.floor(player.location.z)
            ]

            update_teleport_point_confirm_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "update_teleport_point_confirm_form.title")}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "old_teleport_point")}: '
                        f'{ColorFormat.WHITE}'
                        f'({land_tp_pos[0]}, {land_tp_pos[1]}, {land_tp_pos[2]})\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "new_teleport_point")}: '
                        f'{ColorFormat.WHITE}'
                        f'({new_land_tp_pos[0]}, {new_land_tp_pos[1]}, {new_land_tp_pos[2]})\n'
                        f'\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "update_teleport_point_confirm_form.content")}',
                on_close=self.lands
            )

            update_teleport_point_confirm_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "update_teleport_point_confirm_form.button.confirm")}',
                icon='textures/ui/check',
                on_click=self.update_teleport_point_confirm(
                    land_hex_dig,
                    new_land_tp_pos
                )
            )

            update_teleport_point_confirm_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "button.back")}',
                icon='textures/ui/refresh_light',
                on_click=self.lands
            )

            player.send_form(update_teleport_point_confirm_form)

        return on_click

    def update_teleport_point_confirm(self, land_hex_dig, new_land_tp_pos):
        def on_click(player: Player):
            self.land_data[player.name][land_hex_dig]['tp_pos'] = new_land_tp_pos

            self.save_land_data()

            player.send_message(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "update_teleport_point_confirm.message.success")}'
            )

        return on_click

    def land_security_settings(self, land_hex_dig):
        def on_click(player: Player):
            land_security_settings: dict = self.land_data[player.name][land_hex_dig]['security_settings']

            toggles = []

            for key, value in land_security_settings.items():
                toggle = Toggle(
                    label=f'{ColorFormat.YELLOW}'
                          f'{self.get_text(player, key)}',
                    default_value=value
                )

                toggles.append(toggle)

            land_security_settings_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "land_security_settings_form.title")}',
                controls=toggles,
                submit_button=f'{ColorFormat.YELLOW}'
                              f'{self.get_text(player, "land_security_settings_form.submit_button")}',
                on_close=self.lands
            )

            def on_submit(p: Player, json_str: str):
                data = json.loads(json_str)

                index = 0

                for k in land_security_settings.keys():
                    self.land_data[p.name][land_hex_dig]['security_settings'][k] = data[index]

                    index += 1

                self.save_land_data()

                p.send_message(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(p, "land_security_settings.message.success")}'
                )

            land_security_settings_form.on_submit = on_submit

            player.send_form(land_security_settings_form)

        return on_click

    def land_sell(self, land_hex_dig, land_price, land_area):
        def on_clcik(player: Player):
            land_selling_price = self.config_data['selling_price_for_per_square_block'] * land_area

            land_sell_confirm_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "land_sell_confirm_form.title")}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "price")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_price}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "selling_price")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_selling_price}\n'
                        f'\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "land_sell_confirm_form.content")}',
                on_close=self.lands
            )

            land_sell_confirm_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_sell_confirm_form.button.confirm")}',
                icon='textures/ui/check',
                on_click=self.land_sell_confirm(
                    land_hex_dig,
                    land_selling_price
                )
            )

            land_sell_confirm_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "button.back")}',
                icon='textures/ui/refresh_light',
                on_click=self.lands
            )

            player.send_form(land_sell_confirm_form)

        return on_clcik

    def land_sell_confirm(self, land_hex_dig, land_selling_price):
        def on_click(player: Player):
            self.land_data[player.name].pop(land_hex_dig)

            self.save_land_data()

            player.send_message(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_sell_confirm.message.success")}'
            )

            self.server.plugin_manager.get_plugin('umoney').api_change_player_money(player.name, land_selling_price)

        return on_click

    def land_transfer_ownership(self, land_hex_dig, land_name):
        def on_click(player: Player):
            player_name_list = []

            for player_name in self.land_data.keys():
                if player.name != player_name:
                    player_name_list.append(player_name)

            if len(player_name_list) == 0:
                player.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(player, "land_transfer_ownership.message.fail")}: '
                    f'{ColorFormat.WHITE}'
                    f'{self.get_text(player, "land_transfer_ownership.message.fail.reason")}'
                )

                return

            player_name_list.sort(key=lambda x:x[0].lower(), reverse=False)

            dropdown = Dropdown(
                label=f'{ColorFormat.GREEN}'
                      f'{self.get_text(player, "land_transfer_ownership_form.dropdown.label")}',
                options=player_name_list,
            )

            land_transfer_ownership_form = ModalForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "land_transfer_ownership_form.title")}',
                controls=[dropdown],
                submit_button=f'{ColorFormat.YELLOW}'
                              f'{self.get_text(player, "land_transfer_ownership_form.submit_button")}',
                on_close=self.lands
            )

            def on_submit(p: Player, json_str: str):
                data = json.loads(json_str)

                player_name_to_transfer = player_name_list[data[0]]

                land_transfer_ownership_confirm_form = ActionForm(
                    title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                          f'{self.get_text(p, "land_transfer_ownership_confirm_form.title")}',
                    content=f'{ColorFormat.GREEN}'
                            f'{self.get_text(p, "land_transfer_ownership_confirm_form.content")}',
                    on_close=self.lands
                )

                land_transfer_ownership_confirm_form.add_button(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(p, "land_transfer_ownership_confirm_form.button.confirm")}',
                    icon='textures/ui/check',
                    on_click=self.land_transfer_ownership_confirm(
                        land_hex_dig,
                        land_name,
                        player_name_to_transfer
                    )
                )

                land_transfer_ownership_confirm_form.add_button(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(p, "button.back")}',
                    icon='textures/ui/refresh_light',
                    on_click=self.lands
                )

                p.send_form(land_transfer_ownership_confirm_form)

            land_transfer_ownership_form.on_submit = on_submit

            player.send_form(land_transfer_ownership_form)

        return on_click

    def land_transfer_ownership_confirm(self, land_hex_dig, land_name, player_name_to_transfer):
        def on_click(player: Player):
            self.land_data[player_name_to_transfer][land_hex_dig] = self.land_data[player.name][land_hex_dig]

            land_security_settings: dict = self.land_data[player_name_to_transfer][land_hex_dig]['security_settings']

            for key in land_security_settings.keys():
                self.land_data[player_name_to_transfer][land_hex_dig]['security_settings'][key] = False

            self.save_land_data()

            player.send_message(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_transfer_ownership_confirm.message.success")}'
            )

            if self.server.get_player(player_name_to_transfer) is not None:
                player_to_transfer = self.server.get_player(player_name_to_transfer)

                player_to_transfer.send_message(
                    f'{ColorFormat.YELLOW}'
                    f'{self.get_text(player, "land_transfer_ownership_confirm.message").format(player.name, land_name)}'
                )

        return on_click

    def public_lands(self, player: Player):
        public_lands_form = ActionForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                  f'{self.get_text(player, "public_lands_form.title")}',
            content=f'{ColorFormat.GREEN}'
                    f'{self.get_text(player, "public_lands_form.content")}',
            on_close=self.back_to_main_form
        )

        for land_owner, lands in self.land_data.items():
            for land_info in lands.values():
                if land_info['security_settings']['is_land_public']:
                    land_members = land_info['members']

                    land_name = land_info['name']

                    land_creation_datetime = land_info['creation_datetime']

                    land_price = land_info['price']

                    land_dim = land_info['dim']

                    land_posa = land_info['posa']

                    land_posb = land_info['posb']

                    land_range = f'({land_posa[0]}, ~, {land_posa[1]}) - ({land_posb[0]}, ~, {land_posb[1]})'

                    land_area = land_info['area']

                    land_tp_pos = land_info['tp_pos']

                    button_text = (
                        f'{ColorFormat.YELLOW}'
                        f'{land_name} '
                    )

                    if land_dim == 'Overworld':
                        button_text += (
                            f'{ColorFormat.GREEN}'
                            f'#'
                        )
                    elif land_dim == 'Nether':
                        button_text += (
                            f'{ColorFormat.RED}'
                            f'#'
                        )
                    else:
                        button_text += (
                            f'{ColorFormat.LIGHT_PURPLE}'
                            f'#'
                        )

                    button_text += (
                        f'\n'
                        f'{ColorFormat.YELLOW}'
                        f'[{self.get_text(player, "owner")}] {land_owner}'
                    )

                    public_lands_form.add_button(
                        text=button_text,
                        icon='textures/ui/icon_spring',
                        on_click=self.public_land(
                            land_owner,
                            land_name,
                            land_creation_datetime,
                            land_price,
                            land_dim,
                            land_range,
                            land_area,
                            land_tp_pos,
                            land_members
                        )
                    )

        public_lands_form.add_button(
            f'{ColorFormat.YELLOW}'
            f'{self.get_text(player, "button.back")}',
            icon='textures/ui/refresh_light',
            on_click=self.back_to_main_form
        )

        player.send_form(public_lands_form)

    def public_land(self, land_owner, land_name, land_creation_datetime, land_price, land_dim, land_range, land_area, land_tp_pos, land_members):
        def on_click(player: Player):
            members = ', '.join(land_members)

            dim = self.get_text(player, land_dim)

            public_land_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{land_name}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "owner")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_owner}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "creation_datetime")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_creation_datetime}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "dim")}: '
                        f'{ColorFormat.WHITE}'
                        f'{dim}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "range")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_range}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "area")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_area}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "price")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_price}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "members")}: '
                        f'{ColorFormat.WHITE}'
                        f'{members}\n'
                        f'\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "public_land_form.content")}',
                on_close=self.public_lands
            )

            public_land_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "public_land_form.button.land_teleport")}',
                icon='textures/ui/realmsIcon',
                on_click=self.land_teleport(
                    land_dim,
                    land_tp_pos
                )
            )

            public_land_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "button.back")}',
                icon='textures/ui/refresh_light',
                on_click=self.public_lands
            )

            player.send_form(public_land_form)

        return on_click

    def manage_lands(self, player: Player):
        options = []

        for land_owner, lands in self.land_data.items():
            land_num_belong_to_this_player = len(lands)

            if land_num_belong_to_this_player != 0:
                options.append(
                    f'{land_owner} - '
                    f'{ColorFormat.GREEN}'
                    f'{self.get_text(player, "manage_lands_form.dropdown.option").format(land_num_belong_to_this_player)}'
                )

        options.sort(key=lambda x:x[0].lower(), reverse=False)

        dropdown = Dropdown(
            label=f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "manage_lands_form.dropdown.label")}',
            options=options
        )

        manage_lands_form = ModalForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                  f'{self.get_text(player, "manage_lands_form.title")}',
            controls=[dropdown],
            submit_button=f'{ColorFormat.YELLOW}'
                          f'{self.get_text(player, "manage_lands_form.submit_button")}',
            on_close=self.back_to_main_form
        )

        def on_submit(p: Player, json_str: str):
            data = json.loads(json_str)

            player_name_to_manage = options[data[0]].split(' - ')[0]

            manage_lands_further_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "manage_lands_further_form.title")}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "manage_lands_further_form.content").format(player_name_to_manage)}: ',
                on_close=self.manage_lands
            )

            for land_hex_dig, land_info in self.land_data[player_name_to_manage].items():
                land_name = land_info['name']

                land_creation_datetime = land_info['creation_datetime']

                land_dim = land_info['dim']

                land_posa = land_info['posa']

                land_posb = land_info['posb']

                land_range = f'({land_posa[0]}, ~, {land_posa[1]}) - ({land_posb[0]}, ~, {land_posb[1]})'

                land_area = land_info['area']

                land_price = land_info['price']

                land_tp_pos = land_info['tp_pos']

                land_members = land_info['members']

                button_text = (
                    f'{ColorFormat.YELLOW}'
                    f'{land_name} '
                )

                if land_dim == 'Overworld':
                    button_text += (
                        f'{ColorFormat.GREEN}'
                        f'#'
                    )
                elif land_dim == 'Nether':
                    button_text += (
                        f'{ColorFormat.RED}'
                        f'#'
                    )
                else:
                    button_text += (
                        f'{ColorFormat.LIGHT_PURPLE}'
                        f'#'
                    )

                manage_lands_further_form.add_button(
                    text=button_text,
                    icon='textures/ui/icon_spring',
                    on_click=self.manage_land(
                        player_name_to_manage,
                        land_hex_dig,
                        land_name,
                        land_creation_datetime,
                        land_range,
                        land_area,
                        land_price,
                        land_dim,
                        land_tp_pos,
                        land_members
                    )
                )

            manage_lands_further_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "button.back")}',
                icon='textures/ui/refresh_light',
                on_click=self.manage_lands
            )

            p.send_form(manage_lands_further_form)

        manage_lands_form.on_submit = on_submit

        player.send_form(manage_lands_form)

    def manage_land(self, land_owner, land_hex_dig, land_name, land_creation_datetime, land_range, land_area, land_price, land_dim, land_tp_pos, land_members):
        def on_click(player: Player):
            dim = self.get_text(player, land_dim)

            members = ', '.join(land_members)

            manage_land_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{land_name}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "owner")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_owner}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "creation_datetime")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_creation_datetime}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "dim")}: '
                        f'{ColorFormat.WHITE}'
                        f'{dim}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "range")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_range}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "area")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_area}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "price")}: '
                        f'{ColorFormat.WHITE}'
                        f'{land_price}\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "members")}: '
                        f'{ColorFormat.WHITE}'
                        f'{members}\n'
                        f'\n'
                        f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "manage_land_further_form.content")}',
                on_close=self.manage_lands
            )

            manage_land_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "manage_land_further_form.button.land_teleport")}',
                icon='textures/ui/realmsIcon',
                on_click=self.land_teleport(
                    land_dim,
                    land_tp_pos
                )
            )

            manage_land_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "manage_land_further_form.button.land_delete")}',
                icon='textures/ui/icon_trash',
                on_click=self.land_delete(
                    land_owner,
                    land_hex_dig
                )
            )

            manage_land_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "button.back")}',
                icon='textures/ui/refresh_light',
                on_click=self.manage_lands
            )

            player.send_form(manage_land_form)

        return on_click

    def land_delete(self, land_owner, land_hex_dig):
        def on_click(player: Player):
            land_delete_confirm_form = ActionForm(
                title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                      f'{self.get_text(player, "land_delete_form.title")}',
                content=f'{ColorFormat.GREEN}'
                        f'{self.get_text(player, "land_delete_form.content")}',
                on_close=self.manage_lands
            )

            land_delete_confirm_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_delete_form.button.confirm")}',
                icon='textures/ui/confirm',
                on_click=self.land_delete_confirm(
                    land_owner,
                    land_hex_dig
                )
            )

            land_delete_confirm_form.add_button(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "button.back")}',
                icon='textures/ui/refresh_light',
                on_click=self.manage_lands
            )

            player.send_form(land_delete_confirm_form)

        return on_click

    def land_delete_confirm(self, land_owner, land_hex_dig):
        def on_click(player: Player):
            self.land_data[land_owner].pop(land_hex_dig)

            self.save_land_data()

            player.send_message(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(player, "land_delete.message.success")}'
            )

        return on_click

    def reload_configurations(self, player: Player):
        max_land_num_can_per_player_has = self.config_data['max_land_num_can_per_player_has']

        create_a_new_land_time_limit = self.config_data['create_a_new_land_time_limit']

        max_area_can_per_land_achieve = self.config_data['max_area_can_per_land_achieve']

        price_for_per_square_block = self.config_data['price_for_per_square_block']

        selling_price_for_per_square_block = self.config_data['selling_price_for_per_square_block']

        textinput1 = TextInput(
            label=f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "reload_config_form.textinput1.label")}: '
                  f'{ColorFormat.WHITE}'
                  f'{max_land_num_can_per_player_has}',
            default_value=f'{max_land_num_can_per_player_has}',
            placeholder=self.get_text(player, "reload_config_form.textinput.placeholder")
        )

        textinput2 = TextInput(
            label=f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "reload_config_form.textinput2.label")}: '
                  f'{ColorFormat.WHITE}'
                  f'{create_a_new_land_time_limit}',
            default_value=f'{create_a_new_land_time_limit}',
            placeholder=self.get_text(player, "reload_config_form.textinput.placeholder")
        )

        textinput3 = TextInput(
            label=f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "reload_config_form.textinput3.label")}: '
                  f'{ColorFormat.WHITE}'
                  f'{max_area_can_per_land_achieve}',
            default_value=f'{max_area_can_per_land_achieve}',
            placeholder=self.get_text(player, "reload_config_form.textinput.placeholder")
        )

        textinput4 = TextInput(
            label=f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "reload_config_form.textinput4.label")}: '
                  f'{ColorFormat.WHITE}'
                  f'{price_for_per_square_block}',
            default_value=f'{price_for_per_square_block}',
            placeholder=self.get_text(player, "reload_config_form.textinput.placeholder")
        )

        textinput5 = TextInput(
            label=f'{ColorFormat.GREEN}'
                  f'{self.get_text(player, "reload_config_form.textinput5.label")}: '
                  f'{ColorFormat.WHITE}'
                  f'{selling_price_for_per_square_block}',
            default_value=f'{selling_price_for_per_square_block}',
            placeholder=self.get_text(player, "reload_config_form.textinput.placeholder")
        )

        reload_configurations_form = ModalForm(
            title=f'{ColorFormat.BOLD}{ColorFormat.LIGHT_PURPLE}'
                  f'{self.get_text(player, "reload_config_form.title")}',
            controls=[
                textinput1,
                textinput2,
                textinput3,
                textinput4,
                textinput5
            ],
            submit_button=f'{ColorFormat.YELLOW}'
                          f'{self.get_text(player, "reload_config_form.submit_button")}',
            on_close=self.back_to_main_form
        )

        def on_submit(p: Player, json_str: str):
            data = json.loads(json_str)

            try:
                update_max_land_num_can_per_player_has = int(data[0])

                update_create_a_new_land_time_limit = int(data[1])

                update_max_area_can_per_land_achieve = int(data[2])

                update_price_for_per_square_block = int(data[3])

                update_selling_price_for_per_square_block = int(data[4])
            except:
                p.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(p, "message.type_error")}'
                )

                return

            if (
                update_max_land_num_can_per_player_has <= 0
                and
                update_create_a_new_land_time_limit <= 0
                and
                update_max_area_can_per_land_achieve <= 0
                and
                update_price_for_per_square_block <= 0
                and
                update_selling_price_for_per_square_block <= 0
            ):
                p.send_message(
                    f'{ColorFormat.RED}'
                    f'{self.get_text(p, "message.type_error")}'
                )

                return

            self.config_data['max_land_num_can_per_player_has'] = update_max_land_num_can_per_player_has

            self.config_data['create_a_new_land_time_limit'] = update_create_a_new_land_time_limit

            self.config_data['max_area_can_per_land_achieve'] = update_max_area_can_per_land_achieve

            self.config_data['price_for_per_square_block'] = update_price_for_per_square_block

            self.config_data['selling_price_for_per_square_block'] = update_selling_price_for_per_square_block

            with open(config_data_file_path, 'w', encoding='utf-8') as f:
                json_str = json.dumps(self.config_data, indent=4, ensure_ascii=False)

                f.write(json_str)

            p.send_message(
                f'{ColorFormat.YELLOW}'
                f'{self.get_text(p, "reload_config.message.success")}'
            )

        reload_configurations_form.on_submit = on_submit

        player.send_form(reload_configurations_form)

    def show_land_tip(self):
        online_player_list = self.server.online_players

        if len(online_player_list) == 0:
            return

        for online_player in online_player_list:
            player_dim = online_player.dimension.name

            player_pos = [
                math.floor(online_player.location.x),
                math.floor(online_player.location.z)
            ]

            check_flag = True

            for land_owner, lands in self.land_data.items():
                if not check_flag:
                    break

                for land_info in lands.values():
                    land_dim = land_info['dim']

                    if player_dim == land_dim:
                        land_posa = land_info['posa']

                        land_posb = land_info['posb']

                        if (
                            min(land_posa[0], land_posb[0]) <= player_pos[0] <= max(land_posa[0], land_posb[0])
                            and
                            min(land_posa[1], land_posb[1]) <= player_pos[1] <= max(land_posa[1], land_posb[1])
                        ):
                            land_name = land_info['name']

                            online_player.send_tip(
                                f'{ColorFormat.YELLOW}'
                                f'{self.get_text(online_player, "land_tip").format(land_owner, land_name)}'
                            )

                            check_flag = False

                            break

    @event_handler
    def on_thunder_spawn(self, event: ActorSpawnEvent):
        if event.actor.type == 'minecraft:lightning_bolt':
            check_type = 'can_thunder_spawn'

            actor_dim = event.actor.dimension.name

            actor_pos = [
                math.floor(event.actor.location.x),
                math.floor(event.actor.location.z)
            ]

            check_result = self.check2(
                actor_dim,
                actor_pos,
                check_type
            )

            if check_result:
                event.cancel()

    @event_handler
    def on_explosion(self, event: ActorExplodeEvent):
        explosion_dim = event.actor.dimension.name

        for lands in self.land_data.values():
            for land_info in lands.values():
                if not land_info['security_settings']['can_explosion_spawn']:
                    land_dim = land_info['dim']

                    if explosion_dim == land_dim:
                        land_posa = land_info['posa']

                        land_posb = land_info['posb']

                        for block in event.block_list:
                            block_pos = [
                                math.floor(block.location.x),
                                math.floor(block.location.z)
                            ]

                            if (
                                min(land_posa[0], land_posb[0]) <= block_pos[0] <= max(land_posa[0], land_posb[0])
                                and
                                min(land_posa[1], land_posb[1]) <= block_pos[1] <= max(land_posa[1], land_posb[1])
                            ):
                                event.cancel()

                                return

    @event_handler
    def on_player_place_block(self, event: BlockPlaceEvent):
        if (
            event.player.is_op
            and
            event.player.game_mode.value == 1
        ):
            return

        check_type = 'can_stranger_place_block'

        block_dim = event.block.dimension.name

        block_pos = [
            math.floor(event.block.location.x),
            math.floor(event.block.location.z)
        ]

        check_result = self.check(
            block_dim,
            block_pos,
            event.player.name,
            check_type
        )

        if check_result is not None:
            event.cancel()

            land_owner = check_result[0]

            land_name = check_result[1]

            event.player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(event.player, "place_block.message").format(land_owner, land_name)}'
            )

    @event_handler
    def on_player_break_block(self, event: BlockBreakEvent):
        if (
            event.player.is_op
            and
            event.player.game_mode.value == 1
        ):
            return

        check_type = 'can_stranger_break_block'

        block_dim = event.block.dimension.name

        block_pos = [
            math.floor(event.block.location.x),
            math.floor(event.block.location.z)
        ]

        check_result = self.check(
            block_dim,
            block_pos,
            event.player.name,
            check_type
        )

        if check_result is not None:
            event.cancel()

            land_owner = check_result[0]

            land_name = check_result[1]

            event.player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(event.player, "break_block.message").format(land_owner, land_name)}'
            )

    @event_handler
    def on_player_click_block(self, event: PlayerInteractEvent):
        if (
            event.player.is_op
            and
            event.player.game_mode.value == 1
        ):
            return

        if (
            event.action.name == 'LEFT_CLICK_BLOCK'
            or
            event.action.name == 'RIGHT_CLICK_BLOCK'
        ):
            if event.action.name == 'LEFT_CLICK_BLOCK':
                check_type = 'can_stranger_left_click_block'
            else:
                check_type = 'can_stranger_right_click_block'

            block_dim = event.block.dimension.name

            block_pos = [
                math.floor(event.block.location.x),
                math.floor(event.block.location.z)
            ]

            check_result = self.check(
                block_dim,
                block_pos,
                event.player.name,
                check_type
            )

            if check_result is not None:
                event.cancel()

                land_owner = check_result[0]

                land_name = check_result[1]

                if event.action.name == 'LEFT_CLICK_BLOCK':
                    event.player.send_message(
                        f'{ColorFormat.RED}'
                        f'{self.get_text(event.player, "left_click_block.message").format(land_owner, land_name)}'
                    )
                else:
                    event.player.send_message(
                        f'{ColorFormat.RED}'
                        f'{self.get_text(event.player, "right_click_block.message").format(land_owner, land_name)}'
                    )

    @event_handler
    def on_player_click_entity(self, event: PlayerInteractActorEvent):
        if (
            event.player.is_op
            and
            event.player.game_mode.value == 1
        ):
            return

        check_type = 'can_stranger_right_click_entity'

        actor_dim = event.actor.dimension.name

        actor_pos = [
            math.floor(event.actor.location.x),
            math.floor(event.actor.location.z)
        ]

        check_result = self.check(
            actor_dim,
            actor_pos,
            event.player.name,
            check_type
        )

        if check_result is not None:
            event.cancel()

            land_owner = check_result[0]

            land_name = check_result[1]

            event.player.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(event.player, "right_click_entity.message").format(land_owner, land_name)}'
            )

    @event_handler
    def on_player_damage(self, event: ActorDamageEvent):
        if not isinstance(event.damage_source.actor, Player):
            return

        attacker = event.damage_source.actor

        if (
            attacker.is_op
            and
            attacker.game_mode.value == 1
        ):
            return

        check_type = 'can_stranger_damage_player_or_entity'

        victim_dim = event.actor.dimension.name

        victim_pos = [
            math.floor(event.actor.location.x),
            math.floor(event.actor.location.z)
        ]

        check_result = self.check(
            victim_dim,
            victim_pos,
            attacker.name,
            check_type
        )

        if check_result is not None:
            event.cancel()

            land_owner = check_result[0]

            land_name = check_result[1]

            attacker.send_message(
                f'{ColorFormat.RED}'
                f'{self.get_text(attacker, "damage_player_or_entity.message").format(land_owner, land_name)}'
            )

    @event_handler
    def on_fire_or_explosion_damage(self, event: ActorDamageEvent):
        damage_source_type = event.damage_source.type

        if (
            damage_source_type == 'fire'
            or
            damage_source_type == 'fire_tick'
            or
            damage_source_type == 'block_explosion'
        ):
            if (
                damage_source_type == 'fire'
                or
                damage_source_type == 'fire_tick'
            ):
                check_type = 'can_fire_damage_player_or_entity'
            else:
                check_type = 'can_explosion_spawn'

            victim_dim = event.actor.dimension.name

            victim_pos = [
                math.floor(event.actor.location.x),
                math.floor(event.actor.location.z)
            ]

            check_result = self.check2(
                victim_dim,
                victim_pos,
                check_type
            )

            if check_result:
                event.cancel()

    @event_handler
    def on_poison_or_wither_effect_damage(self, event: ActorDamageEvent):
        damage_source_type = event.damage_source.type

        if (
            damage_source_type == 'magic'
            or
            damage_source_type == 'wither'
        ):
            if damage_source_type == 'magic':
                check_type = 'can_poison_effect_applied_to_player_or_entity'
            else:
                check_type = 'can_wither_effect_applied_to_player_or_entity'

            victim_dim = event.actor.dimension.name

            victim_pos = [
                math.floor(event.actor.location.x),
                math.floor(event.actor.location.y),
                math.floor(event.actor.location.z)
            ]

            victim_pos_c = [
                victim_pos[0],
                victim_pos[2]
            ]

            check_result = self.check2(
                victim_dim,
                victim_pos_c,
                check_type
            )

            if check_result:
                event.cancel()

                if victim_dim == 'Overworld':
                    execute_dim = 'overworld'
                elif victim_dim == 'Nether':
                    execute_dim = 'nether'
                else:
                    execute_dim = 'the_end'

                if damage_source_type == 'magic':
                    effect = 'poison'
                else:
                    effect = 'wither'

                self.server.dispatch_command(
                    self.command_sender,
                    command_line=f'execute in {execute_dim} run '
                    f'effect @e[x={victim_pos[0]}, y={victim_pos[1]}, z={victim_pos[2]}, '
                    f'dx=0, dy=5, dz=0] clear {effect}'
                )

    def fuck_wither(self):
        if len(self.server.online_players) == 0:
            return

        for lands in self.land_data.values():
            for land_info in lands.values():
                if not land_info['security_settings']['can_wither_enter_land']:
                    land_dim = land_info['dim']

                    if land_dim == 'Overworld':
                        execute_dim = 'overworld'
                    elif land_dim == 'Nether':
                        execute_dim = 'nether'
                    else:
                        execute_dim = 'the_end'

                    land_posa = land_info['posa']

                    land_posb = land_info['posb']

                    land_half_length = math.floor(
                        abs(land_posa[0] - land_posb[0]) / 2
                    )

                    land_half_width = math.floor(
                        abs(land_posa[1] - land_posb[1]) / 2
                    )

                    land_center_x = min(land_posa[0], land_posb[0]) + land_half_length

                    land_center_z = min(land_posa[1], land_posb[1]) + land_half_width

                    dx = land_half_length

                    dz = land_half_width

                    land_posa_rs = [
                        land_center_x + dx,
                        land_center_z + dz
                    ]

                    self.server.dispatch_command(
                        self.command_sender,
                        command_line=f'execute in {execute_dim} run '
                                     f'tp @e[type=wither, x={land_posa_rs[0]}, y=320, z={land_posa_rs[1]}, '
                                     f'dx={-dx * 2}, dy=-384, dz={-dz * 2}] 0 -100 0'
                    )

                    self.server.dispatch_command(
                        self.command_sender,
                        command_line=f'execute in {execute_dim} run '
                                     f'kill @e[type=wither, x=0, y=-100, z=0, r=20]'
                    )

    def check(self, check_dim: str, check_pos: list, player_name: str, check_type: str):
        for land_owner, lands in self.land_data.items():
            for land_info in lands.values():
                if not land_info['security_settings'][check_type]:
                    land_dim = land_info['dim']

                    if check_dim == land_dim:
                        land_posa = land_info['posa']

                        land_posb = land_info['posb']

                        if (
                            min(land_posa[0], land_posb[0]) <= check_pos[0] <= max(land_posa[0], land_posb[0])
                            and
                            min(land_posa[1], land_posb[1]) <= check_pos[1] <= max(land_posa[1], land_posb[1])
                        ):
                            land_members = land_info['members']

                            if not (
                                player_name == land_owner
                                or
                                player_name in land_members
                            ):
                                land_name = land_info['name']

                                return [land_owner, land_name]
        else:
            return None

    def check2(self, check_dim: str, check_pos: list, check_type: str):
        for lands in self.land_data.values():
            for land_info in lands.values():
                if not land_info['security_settings'][check_type]:
                    land_dim = land_info['dim']

                    if check_dim == land_dim:
                        land_posa = land_info['posa']

                        land_posb = land_info['posb']

                        if (
                            min(land_posa[0], land_posb[0]) <= check_pos[0] <= max(land_posa[0], land_posb[0])
                            and
                            min(land_posa[1], land_posb[1]) <= check_pos[1] <= max(land_posa[1], land_posb[1])
                        ):
                            return True

        else:
            return False

    def save_land_data(self):
        with open(land_data_file_path, 'w', encoding='utf-8') as f:
            json_str = json.dumps(self.land_data, indent=4, ensure_ascii=False)
            f.write(json_str)

    def get_text(self, player: Player, text_key: str) -> str:
        player_lang = player.locale

        try:
            if self.lang_data.get(player_lang) is None:
                text_value = self.lang_data['en_US'][text_key]
            else:
                if self.lang_data[player_lang].get(text_key) is None:
                    text_value = self.lang_data['en_US'][text_key]
                else:
                    text_value = self.lang_data[player_lang][text_key]

            return text_value
        except Exception as e:
            self.logger.error(
                f'{ColorFormat.RED}'
                f'{e}'
            )

            return text_key

    def back_to_zx_ui(self, player: Player):
        player.perform_command('cd')

    def back_to_main_form(self, player: Player):
        player.perform_command('ul')

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        if self.land_data.get(event.player.name) is None:
            self.land_data[event.player.name] = {}

            self.save_land_data()

    @event_handler
    def on_player_left(self, event: PlayerQuitEvent):
        if self.create_a_new_land_recorder.get(event.player.name) is not None:
            task: Task = self.create_a_new_land_recorder[event.player.name]['task']

            self.server.scheduler.cancel_task(task.task_id)

            self.create_a_new_land_recorder.pop(event.player.name)