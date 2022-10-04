GOD_ID = 1020624735
ADMINS = []

# webhook settings
WEBHOOK_HOST = ''
WEBHOOK_PATH = ''
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '127.0.0.1'  # or ip
WEBAPP_PORT = 5000

array_times = {'check_replacement': ["00:00",
                                     "9:00",
                                     "9:30",
                                     "10:00",
                                     "10:15",
                                     "10:30",
                                     "10:45",
                                     "11:00",
                                     "11:15",
                                     "11:30",
                                     "11:45",
                                     "12:00",
                                     "12:15",
                                     "12:30",
                                     "12:45",
                                     "13:00",
                                     "13:15",
                                     "13:30",
                                     "13:45",
                                     "14:00",
                                     "14:15",
                                     "14:30",
                                     "14:45",
                                     "15:00",
                                     "15:15",
                                     "15:30",
                                     "15:45",
                                     "16:00",
                                     "00:00"]
               }

ANSWER_TEXT = {'new_user': {
    'welcome_message_private': lambda user_name: f"Привет {user_name} (^_^)\nЯ бот колледжа ЯПЭК\nДавай определим твой статус 👀",
    'welcome_message_group': lambda user_name: f"Приветствую всех в группе {user_name} (^_^)\nЯ бот колледжа ЯПЭК\nВыберите профиль",
    'choise_type_name': "Выберите профиль",
    'choise_name': lambda type_name: f"Выберите {'группу' if type_name == 'group_' else 'преподавателя'}"
},
    'error': {
        'choise_type_name': "Выберите профиль!",
        'choise_name': "Я не буду реагировать на сообщения до тех пор, пока не будет сделан выбор группы или преподавателя",
        'not_msg_pin': "У бота нет прав на закрепление сообщений"
    },
    'settings': "Настройки",
    'no_main_subscription': "Вы не подписались ни на группу, ни на преподавателя",
    'main_settings': "Основные настройки",
    'support': "Способы поддержки и связи",
    'group__card': "Карточка группы",
    'teacher_card': "Карточка преподавателя",
    'week_days_main_timetable': "Дни недели",
    'help': "В меню /settings вы сможете настроить работу бота под себя:\n"
            "\n"
            "<b>Основная подписка</b> - это группа, отмеченная ⭐\n"
            "По команде /timetable именно для этой группы будет выводиться расписание\n"
            "\n"
            "<b>Подписка</b> - создана для удобства, все группы, на которые вы подписаны будут отмечены в меню Настроек\n"
            "\n"
            "<b>Рассылка</b> - в меню настроек группы с активным параметром Рассылка отмечены 📍\n"
            "\n"
            "Все кнопки кликабельны, поэтому чтобы получить информацию о каком-либо параметре в настройках - просто нажмите на него)\n",
    'show_keyboard': "Клавиатура",
    'months_history_ready_timetable': "Выберите месяц",
    'dates_ready_timetable': lambda month: f"Расписание на <b>{month}</b> месяц"
}

ANSWER_CALLBACK = {'new_user': {
    'choise_group__name_finish': lambda name_: f"Вы выбрали группу {name_}",
    'choise_teacher_name_finish': lambda name_: f"Вы выбрали преподавателя {name_}"
},
    'settings_info': {
        'spamming': "Получение ежедневной рассылки расписания",
        'pin_msg': "Закрепление присланного расписания в диалоге (только той группы/преподавателя, для которых оформлена основная подписка)",
        'view_name': "Добавление информации в сообщение о группе/преподавателя, для которых составлено расписание",
        'view_add': "Отображение ФИО преподавателя, ведущего пару, или названия группы",
        'view_time': "Отображать время начала и окончания занятий",
        'subscribe': "Подписка"},
    'not_timetable_by_week_day': lambda week_day: f"Расписания для {week_day} нет",
    'spam_or_subscribe_name_id': lambda action_type, result: f"{'Рассылка' if action_type == 'sp' else 'Подписка'} {'активирована' if result else 'удалена'}",
    'main_subscribe_name_id': lambda result: f"Основная подписка {'активирована' if result else 'удалена'}"
}
