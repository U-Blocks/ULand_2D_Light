import os
import json


def load_lang_data(lang_dir: str) -> dict:
    zh_CN_data_file_path = os.path.join(lang_dir, 'zh_CN.json')
    en_US_data_file_path = os.path.join(lang_dir, 'en_US.json')

    if not os.path.exists(zh_CN_data_file_path):
        with open(zh_CN_data_file_path, 'w', encoding='utf-8') as f:
            zh_CN = {
                'owner': '领主',
                'player_money': '你的余额',
                'dim': '维度',
                'range': '范围',
                'area': '面积',
                'price': '价格',
                'selling_price': '出售价格',
                'members': '成员',
                'creation_datetime': '创建日期',

                'old_teleport_point': '旧传送点',
                'new_teleport_point': '新传送点',

                'Overworld': '主世界',
                'Nether': '地狱',
                'TheEnd': '末地',

                'is_land_public': '公开领地',
                'can_thunder_spawn': '闪电是否能在领地内生成?',
                'can_explosion_spawn': '爆炸是否能在领地内生成?',
                'can_stranger_place_block': '陌生人是否能放置方块?',
                'can_stranger_break_block': '陌生人是否能破坏方块?',
                'can_stranger_left_click_block': '陌生人是否能左键方块?',
                'can_stranger_right_click_block': '陌生人是否能右键方块?',
                'can_stranger_right_click_entity': '陌生人是否能右键实体?',
                'can_stranger_damage_player_or_entity': '陌生人是否能伤害玩家或实体?',
                'can_fire_damage_player_or_entity': '火焰是否能伤害玩家或实体?',
                'can_poison_effect_applied_to_player_or_entity': '中毒效果是否能被施加到玩家或实体上?',
                'can_wither_effect_applied_to_player_or_entity': '凋零效果是否能被施加到玩家或实体上?',
                'can_wither_enter_land': '凋零是否能进入领地?',

                'button.close': '关闭',
                'button.back_to_zx_ui': '返回',
                'button.back': '返回上一级',

                'message.error': '表单解析错误, 请按提示正确填写...',

                'main_form.title': 'UShop - 主表单',
                'main_form.content': '请选择操作...',
                'main_form.button.create_a_new_land': '创建新领地',
                'main_form.button.lands': '我的领地',
                'main_form.button.public_lands': '公开领地',
                'main_form.button.manage_lands': '管理领地',
                'main_form.button.reload_config': '重载配置文件',

                'create_a_new_land.message.fail': '创建新领地失败',
                'create_a_new_land.message.fail.reason1': '你已经创建了 {0} 个领地了...',
                'create_a_new_land.message.fail.reason2': '你已经有一个创建新领地的任务正在进行中...',
                'create_a_new_land_message.fail.reason3': '超时...',
                'create_a_new_land_message.fail.reason4': '你想创建的新领地和一个已经存在的领地重叠了...',
                'create_a_new_land_message.fail.reason5': '你想创建的新领地的面积小于 4 平方方块, 太小了...',
                'create_a_new_land_message.fail.reason6': '你想创建的新领地的面积大于 {0}, 超出了此服务器的单个领地面积最大限制...',
                'create_a_new_land_message.fail.reason7': '你的余额不足以支付你想创建的新领地, 你需要额外 {0} 来支付它...',
                'create_a_new_land.message.start.text1': '你开启了创建新领地的任务, 请在 {0}s 内完成选点...',
                'create_a_new_land.message.start.text2': '输入命令 /posa 来选择 A点',
                'create_a_new_land.message.start.text3': '输入命令 /posb 来选择 B点',
                'create_a_new_land.message.start.text4': '警告: 你不能跨维度选点, 并且选择的 A点 和 B点 不能完全相同...',
                'select_a_point_a.message.fail': '选择 A点 失败',
                'select_a_point.message.success': '选择 A点 成功...',
                'update_a_point.message.success': '更新 A点 成功...',
                'select_a_point_b.message.fail': '选择 B点 失败',
                'select_a_point.message.fail.reason1': '你没有创建新领地的任务正在进行中...',
                'select_a_point.message.fail.reason2': '你还没有选择 A点...',
                'select_a_point.message.fail.reason3': '你不能跨维度选点...',
                'select_a_point.message.fail.reason4': '你不能选择和 A点 完全相同的点...',
                'create_a_new_land.message.success': '创建新领地成功...',

                'create_a_new_land_further_form.title': "创建新领地",
                'create_a_new_land_further_form.textinput': '输入新领地的名称...',
                'create_a_new_land_further_form.textinput.placeholder': "输入任意字符串但不能留空...",
                'create_a_new_land_further_form.textinput.default_value': "{0} 的领地",
                'create_a_new_land_further_form.submit_button': "创建",

                'lands_form.title': '我的领地',
                'lands_form.content': '请选择一个领地...',

                'land_form.content': '请选择操作...',
                'land_form.button.land_teleport': '传送领地',
                'land_form.button.land_settings': '领地设置',

                'land_teleport.message.success': '传送领地成功...',

                'land_settings_form.title': '领地设置',
                'land_settings_form.content': '你正在对领地 {0} 进行操作...',
                'land_settings_form.button.add_member': '添加成员',
                'land_settings_form.button.remove_member': '移除成员',
                'land_settings_form.button.land_rename': '重命名领地',
                'land_settings_form.button.update_teleport_point': '更新领地传送点',
                'land_settings_form.button.land_security_settings': '领地安全设置',
                'land_settings_form.button.land_sell': '出售领地',
                'land_settings_form.button.land_transfer_ownership': '转让所有权',

                'land_add_member.form.title': '添加成员',
                'land_add_member.form.dropdown.label': '选择一个玩家...',
                'land_add_member.form.submit_button': '添加',
                'land_add_member.message.fail': '添加成员失败',
                'land_add_member.message.fail.reason': '没有可添加为成员的玩家...',
                'land_add_member.message.success': '添加成员成功...',
                'land_add_member.message': '{0} 已经将你添加为 领地({1}) 的成员...',

                'land_remove_member.form.title': '移除成员',
                'land_remove_member.form.dropdown.label': '选择一个玩家...',
                'land_remove_member.form.submit_button': '移除',
                'land_remove_member.message.fail': '移除成员失败',
                'land_remove_member.message.fail.reason': '该领地没有任何成员...',
                'land_remove_member.message.success': '移除成员成功...',
                'land_remove_member.message': '{0} 已经将你从 领地({1}) 的成员中移除...',

                'land_rename.form.title': '重命名领地',
                'land_rename.form.textinput.label': '输入领地的新名称...',
                'land_rename.form.textinput.placeholder': '输入任意字符串但不能留空...',
                'land_rename.form.submit_button': '重命名',
                'land_rename.message.success': '重命名领地成功...',

                'update_teleport_point_confirm_form.title': '确认表单',
                'update_teleport_point_confirm_form.content': '你确认将领地传送点更新为这样吗?',
                'update_teleport_point_confirm_form.button.confirm': '确认',
                'update_teleport_point_confirm.message.success': '更新领地传送点成功...',

                'land_security_settings_form.title': '领地安全设置',
                'land_security_settings_form.submit_button': '更新',
                'land_security_settings.message.success': '更新领地安全设置成功...',

                'land_sell_confirm_form.title': '确认表单',
                'land_sell_confirm_form.content': '你确认出售该领地吗?',
                'land_sell_confirm_form.button.confirm': '确认',
                'land_sell_confirm.message.success': '出售领地成功...',

                'land_transfer_ownership_form.title': '转让所有权',
                'land_transfer_ownership_form.dropdown.label': '选择一个玩家...',
                'land_transfer_ownership_form.submit_button': '转让',
                'land_transfer_ownership.message.fail': '转让所有权失败',
                'land_transfer_ownership.message.fail.reason': '没有可转让所有权的玩家...',

                'land_transfer_ownership_confirm_form.title': '确认表单',
                'land_transfer_ownership_confirm_form.content': "你确认将该领地的所有权转让给 {0} 吗?",
                'land_transfer_ownership_confirm_form.button.confirm': '确认',
                'land_transfer_ownership_confirm.message.success': '转让所有权成功...',
                'land_transfer_ownership_confirm.message': "{0} 已经将 领地({1}) 的所有权转让给你...",

                'public_lands_form.title': "公开领地",
                'public_lands_form.content': "请选择一个领地...",

                'public_land_form.content': "请选择操作...",
                'public_land_form.button.land_teleport': "传送领地",

                'manage_lands_form.title': "管理领地",
                'manage_lands_form.dropdown.option': "{0} 个领地",
                'manage_lands_form.dropdown.label': "选择一个玩家...",
                'manage_lands_form.submit_button': "查询",

                'manage_lands_further_form.title': "管理领地",
                'manage_lands_further_form.content': "{0} 的领地",

                'manage_land_further_form.content': "请选择操作...",
                'manage_land_further_form.button.land_teleport': "传送领地",
                'manage_land_further_form.button.land_delete': "删除领地",

                'land_delete_form.title': "确认表单",
                'land_delete_form.content': "你确认删除该领地吗?",
                'land_delete_form.button.confirm': "确认",
                'land_delete.message.success': "删除领地成功...",

                'reload_config_form.title': "重载配置文件",
                'reload_config_form.textinput1.label': "每个玩家最多可拥有的领地数量",
                'reload_config_form.textinput2.label': "创建新领地的时间限制",
                'reload_config_form.textinput3.label': "每个领地最大可达到的面积",
                'reload_config_form.textinput4.label': "每平方方块的价格",
                'reload_config_form.textinput5.label': "每平方方块的出售价格",
                'reload_config_form.textinput.placeholder': "输入一个正整数...",
                'reload_config_form.submit_button': "重载",
                'reload_config.message.success': "重载配置文件成功...",

                'land_tip': "你正在位于 {0} 的 领地({1})",

                'place_block.message': "你无权在 {0} 的 领地({1}) 放置方块...",
                'break_block.message': "你无权在 {0} 的 领地({1}) 破坏方块...",
                'left_click_block.message': "你无权在 {0} 的 领地({1}) 左键方块...",
                'right_click_block.message': "你无权在 {0} 的 领地({1}) 右键方块...",
                'right_click_entity.message': "你无权在 {0} 的 领地({1}) 右键实体",
                'damage_player_or_entity.message': "你无权在 {0} 的 领地({1}) 伤害玩家或实体...",
            }
            json_str = json.dumps(zh_CN, indent=4, ensure_ascii=False)
            f.write(json_str)

    if not os.path.exists(en_US_data_file_path):
        with open(en_US_data_file_path, 'w', encoding='utf-8') as f:
            en_US = {
                'owner': 'Owner',
                'player_money': 'Your money',
                'dim': 'Dimension',
                'range': 'Range',
                'area': 'Area',
                'price': 'Price',
                'selling_price': 'Selling price',
                'members': 'Members',
                'creation_datetime': 'Creation datetime',

                'old_teleport_point': 'Old teleport point',
                'new_teleport_point': 'New teleport point',

                'Overworld': 'Overworld',
                'Nether': 'Nether',
                'TheEnd': 'The end',

                'is_land_public': 'Make this land public',
                'can_thunder_spawn': 'Can thunder spawn in this land?',
                'can_explosion_spawn': 'Can explosions spawn in this land?',
                'can_stranger_place_block': 'Can strangers place blocks?',
                'can_stranger_break_block': 'Can strangers break blocks?',
                'can_stranger_left_click_block': 'Can strangers left click blocks?',
                'can_stranger_right_click_block': 'Can strangers right click blocks?',
                'can_stranger_right_click_entity': 'Can strangers right click entities?',
                'can_stranger_damage_player_or_entity': 'Can strangers to damage players or entities?',
                'can_fire_damage_player_or_entity': 'Can fire damage players or entities?',
                'can_poison_effect_applied_to_player_or_entity': 'Can poison effect be applied to players or entities?',
                'can_wither_effect_applied_to_player_or_entity': 'Can wither effect be applied to players or entities?',
                'can_wither_enter_land': 'Can wither enter this land?',

                'button.close': 'Close',
                'button.back_to_zx_ui': 'Back',
                'button.back': 'Back to previous',

                'message.error': 'The form is parsed incorrectly, please follow the prompts to fill in correctly...',

                'main_form.title': 'UShop - main form',
                'main_form.content': 'Please select a function...',
                'main_form.button.create_a_new_land': 'Create a new land',
                'main_form.button.lands': 'My land(s)',
                'main_form.button.public_lands': 'Public land(s)',
                'main_form.button.manage_lands': 'Manage land(s)',
                'main_form.button.reload_config': 'Reload configurations',

                'create_a_new_land.message.fail': 'Failed to create a new land',
                'create_a_new_land.message.fail.reason1': 'you have already created {0} lands...',
                'create_a_new_land.message.fail.reason2': 'you already have a ongoing task of creating a new land...',
                'create_a_new_land_message.fail.reason3': 'overtime...',
                'create_a_new_land_message.fail.reason4': 'the new land you tend to create overlaps with an existing land...',
                'create_a_new_land_message.fail.reason5': 'the area of the new land you tend is less than 4 square blocks, which is too small...',
                'create_a_new_land_message.fail.reason6': 'the area of the new land you tend is larger than {0} square blocks, which exceeds the max area per land limited by this server...',
                'create_a_new_land_message.fail.reason7': 'your money is not enough to afford the new land you tend to create, you need {0} more to cover it...',
                'create_a_new_land.message.start.text1': 'You have started the task of creating a new land, please complete points selection within {0}s...',
                'create_a_new_land.message.start.text2': 'Enter the command /posa to select point A',
                'create_a_new_land.message.start.text3': 'Enter the command /posb to select point B',
                'create_a_new_land.message.start.text4': 'Warning: you cannot select points across dimensions, and the selected point A and point B cannot be the same...',
                'select_a_point_a.message.fail': 'Failed to select point A',
                'select_a_point.message.success': 'Successfully select point A...',
                'update_a_point.message.success': 'Successfully update point A...',
                'select_a_point_b.message.fail': 'Failed to select point B',
                'select_a_point.message.fail.reason1': 'you do not have any ongoing task of creating a new land...',
                'select_a_point.message.fail.reason2': 'you have not selected point A...',
                'select_a_point.message.fail.reason3': 'you cannot select points across dimensions...',
                'select_a_point.message.fail.reason4': 'you cannot select a point that is the same as selected point A...',
                'create_a_new_land.message.success': 'Successfully create a new land...',

                'create_a_new_land_further_form.title': "Create a new land",
                'create_a_new_land_further_form.textinput': 'Input the name of new land...',
                'create_a_new_land_further_form.textinput.placeholder': "Input any string but cannot be blank...",
                'create_a_new_land_further_form.textinput.default_value': "{0}'s land",
                'create_a_new_land_further_form.submit_button': "Create",

                'lands_form.title': 'My land(s)',
                'lands_form.content': 'Please select a land...',

                'land_form.content': 'Please select a function...',
                'land_form.button.land_teleport': 'Teleport to this land',
                'land_form.button.land_settings': 'Land settings',

                'land_teleport.message.success': 'Successfully teleport to this land...',

                'land_settings_form.title': 'Land settings',
                'land_settings_form.content': 'You are operating on the land: {0}...',
                'land_settings_form.button.add_member': 'Add a member',
                'land_settings_form.button.remove_member': 'Remove a member',
                'land_settings_form.button.land_rename': 'Rename this land',
                'land_settings_form.button.update_teleport_point': 'Update teleport point',
                'land_settings_form.button.land_security_settings': 'Land security settings',
                'land_settings_form.button.land_sell': 'Sell this land',
                'land_settings_form.button.land_transfer_ownership': 'Transfer ownership',

                'land_add_member.form.title': 'Add a member',
                'land_add_member.form.dropdown.label': 'Select a player...',
                'land_add_member.form.submit_button': 'Add',
                'land_add_member.message.fail': 'Failed to add a member',
                'land_add_member.message.fail.reason': 'there are no players available to add as a member...',
                'land_add_member.message.success': 'Successfully add a member...',
                'land_add_member.message': '{0} has added you as a member of the land({1})...',

                'land_remove_member.form.title': 'Remove a member',
                'land_remove_member.form.dropdown.label': 'Select a player...',
                'land_remove_member.form.submit_button': 'Remove',
                'land_remove_member.message.fail': 'Failed to remove a member',
                'land_remove_member.message.fail.reason': 'there are no members belong to this land...',
                'land_remove_member.message.success': 'Successfully remove a member...',
                'land_remove_member.message': '{0} has removed you as a member of the land({1})...',

                'land_rename.form.title': 'Rename this land',
                'land_rename.form.textinput.label': 'Input new name of this land...',
                'land_rename.form.textinput.placeholder': 'Input any string but cannot be blank...',
                'land_rename.form.submit_button': 'Rename',
                'land_rename.message.success': 'Successfully rename this land...',

                'update_teleport_point_confirm_form.title': 'Confirm form',
                'update_teleport_point_confirm_form.content': 'Are you sure to update teleport point like the above?',
                'update_teleport_point_confirm_form.button.confirm': 'Confirm',
                'update_teleport_point_confirm.message.success': 'Successfully update teleport point...',

                'land_security_settings_form.title': 'Land security settings',
                'land_security_settings_form.submit_button': 'Update',
                'land_security_settings.message.success': 'Successfully update land security settings...',

                'land_sell_confirm_form.title': 'Confirm form',
                'land_sell_confirm_form.content': 'Are you sure to sell this land?',
                'land_sell_confirm_form.button.confirm': 'Confirm',
                'land_sell_confirm.message.success': 'Successfully sell this land...',

                'land_transfer_ownership_form.title': 'Transfer ownership',
                'land_transfer_ownership_form.dropdown.label': 'Select a player...',
                'land_transfer_ownership_form.submit_button': 'Transfer',
                'land_transfer_ownership.message.fail': 'Failed to transfer ownership',
                'land_transfer_ownership.message.fail.reason': 'there are no players available to transfer ownership...',

                'land_transfer_ownership_confirm_form.title': 'Confirm form',
                'land_transfer_ownership_confirm_form.content': "Are you sure to transfer this land's ownership to {0}?",
                'land_transfer_ownership_confirm_form.button.confirm': 'Confirm',
                'land_transfer_ownership_confirm.message.success': 'Successfully transfer ownership...',
                'land_transfer_ownership_confirm.message': "{0} has transferred the land({1})'s ownership to you...",

                'public_lands_form.title': "Public lands",
                'public_lands_form.content': "Please select a land...",

                'public_land_form.content': "Please select a function...",
                'public_land_form.button.land_teleport': "Teleport to this land",

                'manage_lands_form.title': "Manage land(s)",
                'manage_lands_form.dropdown.option': "{0} lands",
                'manage_lands_form.dropdown.label': "Select a player...",
                'manage_lands_form.submit_button': "Query",

                'manage_lands_further_form.title': "Manage land(s)",
                'manage_lands_further_form.content': "{0}'s lands",

                'manage_land_further_form.content': "Please select a functon...",
                'manage_land_further_form.button.land_teleport': "Teleport to this land",
                'manage_land_further_form.button.land_delete': "Delete this land",

                'land_delete_form.title': "Confirm form",
                'land_delete_form.content': "Are you sure to delete this land?",
                'land_delete_form.button.confirm': "Confirm",
                'land_delete.message.success': "Successfully delete this land...",

                'reload_config_form.title': "Reload configurations",
                'reload_config_form.textinput1.label': "The max number of lands can per player has",
                'reload_config_form.textinput2.label': "The time limit of creating a new land",
                'reload_config_form.textinput3.label': "The max area of per land can achieve",
                'reload_config_form.textinput4.label': "The price for per square block",
                'reload_config_form.textinput5.label': "The selling price for per square block",
                'reload_config_form.textinput.placeholder': "Input a positive integer...",
                'reload_config_form.submit_button': "Reload",
                'reload_config.message.success': "Successfully reload configurations...",

                'land_tip': "You are now on the {0}'s land({1})",

                'place_block.message': "You are not allowed to place blocks in {0}'s land({1})...",
                'break_block.message': "You are not allowed to break blocks in {0}'s land({1})...",
                'left_click_block.message': "You are not allowed to left click blocks in {0}'s land({1})...",
                'right_click_block.message': "You are not allowed to right click blocks in {0}'s land({1})...",
                'right_click_entity.message': "You are not allowed to right click entities in {0}'s land({1})...",
                'damage_player_or_entity.message': "You are not allowed to damage players or entities in {0}'s land({1})...",
            }
            json_str = json.dumps(en_US, indent=4, ensure_ascii=False)
            f.write(json_str)

    lang_data = {}

    for lang in os.listdir(lang_dir):
        lang_name = lang.strip('.json')

        lang_file_path = os.path.join(lang_dir, lang)

        with open(lang_file_path, 'r', encoding='utf-8') as f:
            lang_data[lang_name] = json.loads(f.read())

    return lang_data

