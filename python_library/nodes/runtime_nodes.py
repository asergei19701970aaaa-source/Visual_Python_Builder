"""Универсальные runtime-ноды: память, события, поток, сетка и рисование."""
from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, lst, num, txt


def p(name, ptype="value", default=None, label="", hint="", choices=None,
      kind=""):
    data = {"name": name, "type": ptype, "default": default,
            "label": label or name, "hint": hint}
    if choices:
        data["choices"] = choices
    if kind:
        data["kind"] = kind
    return data


def h(purpose, howto, connect_from="", connect_to="", example="",
      mistakes="", see_also=""):
    return dict(purpose=purpose, howto=howto, connect_from=connect_from,
                connect_to=connect_to, example=example, mistakes=mistakes,
                see_also=see_also)


def collect_actions(value):
    return [a for a in lst(value)
            if isinstance(a, dict) and a.get("kind") == "action"]


def imports_of(*values):
    out = []
    for value in values:
        if isinstance(value, dict):
            out.extend(value.get("imports") or [])
    return sorted(set(out))


def name_of(widget, fallback="canvas"):
    return widget.get("name", fallback) if isinstance(widget, dict) else u.ident(widget, fallback)


memory = library("RuntimeMemory", "25. Runtime: Память", "#506b9b")
values = library("RuntimeValue", "26. Runtime: Значения", "#586f49")
events = library("RuntimeEvent", "27. Runtime: События", "#8a5845")
flow = library("RuntimeFlow", "28. Runtime: Поток", "#7b568d")
grid = library("RuntimeGrid", "29. Runtime: 2D-сетка", "#397b75")
paint = library("RuntimePaint", "30. Runtime: Рисование", "#9a603c")


@memory("Память: создать значение",
        inputs=[p("name", "text", "score", "Имя"),
                p("initial", "value", 0, "Начальное значение")],
        outputs=[p("setup", "binding", None, "Подключение к окну"),
                 p("value", "expression", None, "Текущее значение")],
        tags=["переменная", "состояние", "хранилище"],
        **h("Создаёт значение, которое сохраняется между событиями.",
            "1. Дайте короткое имя латиницей.\n2. Подключите «Подключение к окну» ко входу «Связи» окна.\n3. Выход «Текущее значение» используйте в runtime-действиях.",
            "Начальное значение или runtime-выражение.",
            "setup → список связей окна; value → сравнение, формула, показ значения.",
            "score = 0; таймер прибавляет 10 и выводит score на надпись.",
            "Без подключения setup память не будет создана. Не используйте одно имя для разных значений.",
            "Память: изменить; Событие: таймер"))
def memory_create(name, initial):
    key = u.ident(txt(name), "value")
    return (u.runtime("state", name=key, initial=u.code_of(initial)),
            u.expression(f"self.nf_get({key!r})", label=key))


@memory("Память: прочитать",
        inputs=[p("name", "text", "score", "Имя"),
                p("default", "value", 0, "Если значения нет")],
        outputs=[p("value", "expression", None, "Значение")],
        tags=["переменная", "прочитать"],
        **h("Читает сохранённое значение по имени во время события.",
            "Укажите то же имя, что в ноде создания. Подключите выход к runtime-формуле или действию.",
            "Имя должно совпадать с созданной памятью.",
            "Только к фиолетовым/Runtime-нодам, принимающим выражение.",
            "Прочитать lives и показать его в надписи.",
            "Обычные старые действия воспринимают выражение как текст; используйте Runtime: Поток.",
            "Память: создать значение; Память: изменить"))
def memory_read(name, default):
    key = u.ident(txt(name), "value")
    return u.expression(f"self.nf_get({key!r}, {u.code_of(default)})", label=key)


@memory("Память: изменить",
        inputs=[p("name", "text", "score", "Имя"),
                p("operation", "text", "записать", "Операция", choices=[
                    "записать", "прибавить", "вычесть", "умножить",
                    "переключить", "добавить в список", "очистить список"]),
                p("value", "value", 1, "Значение")],
        outputs=[p("action", "action", None, "Действие")],
        tags=["переменная", "счётчик", "список"],
        **h("Изменяет память при наступлении события.",
            "Выберите операцию и подключите действие к событию напрямую или через «Собрать действия».",
            "value может быть числом, текстом или runtime-выражением.",
            "К входу действий таймера, клавиши, старта, мыши.",
            "При каждом тике: score → прибавить → 10.",
            "Нода ничего не делает без события. Для списка сначала создайте начальное значение [].",
            "Память: создать значение; Событие: таймер"))
def memory_change(name, operation, value):
    key = u.ident(txt(name), "value")
    return u.action(
        f"self.nf_change({key!r}, {txt(operation)!r}, {u.code_of(value)})",
        imports=imports_of(value), label="изменить память")


@values("Значение виджета",
        inputs=[p("widget", "widget", None, "Виджет"),
                p("mode", "text", "auto", "Что прочитать",
                  choices=["auto", "text", "number", "checked", "index"])],
        outputs=[p("value", "expression", None, "Значение")],
        tags=["поле", "флажок", "текст", "число"],
        **h("Читает актуальное значение элемента интерфейса, а не значение при сборке схемы.",
            "Подключите виджет, выберите режим и передайте выход в runtime-действие.",
            "Поле ввода, числовое поле, флажок, список.",
            "Формула, сравнение, память: изменить, показать значение.",
            "Поле ввода → Значение виджета(text) → Показать значение.",
            "Режим number подходит только виджетам с методом value()."))
def widget_value(widget, mode):
    name = name_of(widget, "widget")
    return u.expression(f"nf_widget_value(self.{name}, {txt(mode)!r})", label=name)


@values("Формула во время работы",
        inputs=[p("formula", "text", "a + b", "Формула"),
                p("a", "value", 0, "A"), p("b", "value", 0, "B"),
                p("c", "value", 0, "C")],
        outputs=[p("value", "expression", None, "Результат")],
        tags=["выражение", "расчёт"],
        **h("Вычисляет формулу заново при каждом событии.",
            "Напишите формулу через a, b, c и подключите к ним память или значения виджетов.",
            "Числа, память и значения виджетов.",
            "К сравнению, памяти или показу значения.",
            "a + b * 2",
            "Это арифметическая формула, а не место для произвольного Python-кода."))
def runtime_formula(formula, a, b, c):
    return u.expression(
        f"nf_formula({txt(formula)!r}, {u.code_of(a)}, {u.code_of(b)}, {u.code_of(c)})",
        imports=imports_of(a, b, c), label="формула")


@values("Сравнение во время работы",
        inputs=[p("a", "value", 0, "Левое значение"),
                p("operation", "text", "равно", "Условие", choices=[
                    "равно", "не равно", "больше", "меньше",
                    "больше или равно", "меньше или равно", "содержит", "И", "ИЛИ"]),
                p("b", "value", 0, "Правое значение")],
        outputs=[p("result", "expression", None, "Да/нет")],
        tags=["условие", "логика"],
        **h("Проверяет условие в момент события.",
            "Подключите два значения, выберите сравнение, затем передайте результат в «Если выполнить».",
            "Обычные значения или runtime-выражения.",
            "Runtime: Если выполнить.",
            "Текущее score больше 100 → показать победу.",
            "Для «содержит» левое значение должно быть списком или текстом."))
def runtime_compare(a, operation, b):
    return u.expression(
        f"nf_compare({u.code_of(a)}, {txt(operation)!r}, {u.code_of(b)})",
        imports=imports_of(a, b), label="условие")


@values("Случайное целое во время работы",
        inputs=[p("minimum", "value", 0, "От"),
                p("maximum", "value", 10, "До")],
        outputs=[p("value", "expression", None, "Случайное число")],
        tags=["random", "случайное"],
        **h("Получает новое случайное целое при каждом выполнении события.",
            "Задайте границы и подключите к действию записи в память.",
            "Числа или runtime-выражения.",
            "Память: изменить; Формула.",
            "При старте выбрать случайный столбец для фигуры.",
            "Нижняя граница не должна быть больше верхней."))
def runtime_random(minimum, maximum):
    return u.expression(
        f"__import__('random').randint(int({u.code_of(minimum)}), int({u.code_of(maximum)}))",
        label="случайное целое")


@values("Состояние ввода",
        inputs=[p("what", "text", "последняя колонка мыши", "Что узнать",
                  choices=["клавиша удерживается", "последняя X мыши",
                           "последняя Y мыши", "последняя колонка мыши",
                           "последняя строка мыши", "кнопка мыши"]),
                p("key", "text", "SPACE", "Клавиша")],
        outputs=[p("value", "expression", None, "Значение")],
        tags=["клавиатура", "мышь", "input"],
        **h("Даёт событиям текущее состояние клавиатуры или мыши.",
            "Выберите показатель. Для удерживаемой клавиши укажите её имя.",
            "Данные появляются после событий клавиатуры/мыши.",
            "К условию, формуле, памяти.",
            "Клавиша LEFT удерживается → двигать объект.",
            "Имена специальных клавиш: LEFT, RIGHT, UP, DOWN, SPACE, ENTER, ESC."))
def input_state(what, key):
    table = {
        "последняя X мыши": "self._nf_mouse.get('x', 0)",
        "последняя Y мыши": "self._nf_mouse.get('y', 0)",
        "последняя колонка мыши": "self._nf_mouse.get('col', 0)",
        "последняя строка мыши": "self._nf_mouse.get('row', 0)",
        "кнопка мыши": "self._nf_mouse.get('button', '')",
    }
    code = table.get(txt(what), f"{txt(key).upper()!r} in self._nf_keys")
    return u.expression(code, label=txt(what))


@events("Событие: запуск приложения",
        inputs=[p("actions", "actions", None, "Действия")],
        outputs=[p("event", "binding", None, "Событие")],
        tags=["start", "инициализация"],
        **h("Выполняет действия один раз после появления окна.",
            "Соберите нужные действия и подключите выход события к связям окна.",
            "Runtime-действия.",
            "К «Связи» окна через сборщик.",
            "При запуске записать начальные координаты.",
            "Не путайте со значениями памяти: их setup тоже подключается к окну."))
def event_start(actions):
    return u.runtime("event", actions=collect_actions(actions), event="start")


@events("Событие: закрытие окна",
        inputs=[p("actions", "actions", None, "Действия")],
        outputs=[p("event", "binding", None, "Событие")],
        tags=["close", "выход"],
        **h("Выполняет действия перед закрытием приложения.",
            "Подключите действия сохранения, затем событие к окну.",
            "Действия, которые должны завершиться быстро.",
            "К связям окна.",
            "Сохранить рекорд в файл перед выходом.",
            "Долгая операция задержит закрытие окна."))
def event_close(actions):
    return u.runtime("event", actions=collect_actions(actions), event="close")


@events("Событие: таймер",
        inputs=[p("name", "text", "game", "Имя таймера"),
                p("interval", "number", 250, "Интервал, мс"),
                p("autostart", "bool", True, "Запустить сразу"),
                p("actions", "actions", None, "Действия")],
        outputs=[p("event", "binding", None, "Событие")],
        tags=["timer", "tick", "кадр"],
        **h("Повторяет действия через заданный интервал.",
            "Назовите таймер, задайте миллисекунды, подключите действия и событие к окну.",
            "Runtime-действия.",
            "К связям окна.",
            "game, 250 мс → сдвинуть фигуру → перерисовать.",
            "Слишком малый интервал может загрузить процессор. Обычно начинайте с 16–1000 мс.",
            "Управление таймером; Перерисовать холст"))
def event_timer(name, interval, autostart, actions):
    return u.runtime("event", actions=collect_actions(actions), event="timer",
                     name=u.ident(txt(name), "timer"),
                     interval=max(1, int(num(interval, 250))),
                     autostart=flag(autostart, True))


@events("Событие: клавиша",
        inputs=[p("keys", "text", "LEFT, RIGHT", "Клавиши"),
                p("mode", "text", "press", "Момент",
                  choices=["press", "release"]),
                p("actions", "actions", None, "Действия")],
        outputs=[p("event", "binding", None, "Событие")],
        tags=["keyboard", "клавиатура"],
        **h("Запускает действия при нажатии или отпускании выбранных клавиш.",
            "Перечислите клавиши через запятую, выберите press/release и подключите к окну.",
            "Runtime-действия.",
            "К связям окна.",
            "LEFT, A → уменьшить x на 1 → перерисовать.",
            "Фокус должен быть внутри окна. Имена специальных клавиш пишутся по-английски."))
def event_key(keys, mode, actions):
    names = [k.strip().upper() for k in txt(keys).split(",") if k.strip()]
    return u.runtime("event", actions=collect_actions(actions), event="key",
                     keys=names, mode=txt(mode) or "press")


@events("Событие: мышь на холсте",
        inputs=[p("canvas", "widget", None, "Живой холст"),
                p("mode", "text", "press", "Момент",
                  choices=["press", "move", "release"]),
                p("actions", "actions", None, "Действия")],
        outputs=[p("event", "binding", None, "Событие")],
        tags=["mouse", "мышь", "canvas"],
        **h("Запускает действия при работе мышью на динамическом холсте.",
            "Подключите «Живой холст», выберите событие и подключите результат к окну.",
            "Только нода «Живой холст».",
            "К связям окна.",
            "press → взять колонку мыши → записать клетку.",
            "Обычный статичный холст не передаёт runtime-события."))
def event_mouse(canvas, mode, actions):
    return u.runtime("event", actions=collect_actions(actions), event="mouse",
                     canvas=name_of(canvas), mode=txt(mode) or "press")


@events("Событие: рисование холста",
        inputs=[p("canvas", "widget", None, "Живой холст"),
                p("actions", "actions", None, "Команды рисования")],
        outputs=[p("event", "binding", None, "Событие")],
        tags=["draw", "paint", "отрисовка"],
        **h("Выполняет команды рисования каждый раз, когда холст обновляется.",
            "Подключите холст и команды из раздела Runtime: Рисование, затем событие к окну.",
            "Команды «Нарисовать…».",
            "К связям окна.",
            "Очистить → нарисовать 2D-сетку → нарисовать счёт.",
            "Не изменяйте память внутри рисования: рисование может вызываться часто."))
def event_draw(canvas, actions):
    return u.runtime("event", actions=collect_actions(actions), event="draw",
                     canvas=name_of(canvas))


@flow("Если выполнить",
      inputs=[p("condition", "value", False, "Условие"),
              p("yes", "actions", None, "Если да"),
              p("no", "actions", None, "Если нет")],
      outputs=[p("action", "action", None, "Действие")],
      tags=["if", "ветвление"],
      **h("Выбирает один из двух наборов действий во время события.",
          "Подключите runtime-сравнение и действия двух ветвей.",
          "Условие из Runtime: Значения; действия из памяти, сетки, рисования.",
          "К любому runtime-событию.",
          "Если клетка свободна → записать; иначе → показать сообщение.",
          "Обычная логическая нода вычисляется при сборке, а эта — во время работы."))
def flow_if(condition, yes, no):
    lines = [f"if nf_flag({u.code_of(condition)}):"]
    yes_actions, no_actions = collect_actions(yes), collect_actions(no)
    lines.extend("    " + line for a in yes_actions
                 for line in str(a.get("expression") or "pass").splitlines())
    if not yes_actions:
        lines.append("    pass")
    if no_actions:
        lines.append("else:")
        lines.extend("    " + line for a in no_actions
                     for line in str(a.get("expression") or "pass").splitlines())
    return u.action("\n".join(lines),
                    imports=imports_of(condition, *yes_actions, *no_actions),
                    label="условие")


@flow("Повторить",
      inputs=[p("mode", "text", "N раз", "Режим",
                choices=["N раз", "для каждого", "пока"]),
              p("value", "value", 10, "Количество / список / условие"),
              p("actions", "actions", None, "Действия"),
              p("safety_limit", "number", 10000, "Предел безопасности")],
      outputs=[p("action", "action", None, "Действие")],
      tags=["loop", "цикл", "повтор"],
      **h("Повторяет действия без написания цикла.",
          "Выберите режим. Внутри цикла текущее значение доступно через ноду «Значение цикла».",
          "Число, список или условие; затем список действий.",
          "К событию запуска, таймера, клавиши.",
          "Для каждого ряда сетки → проверить заполнение.",
          "Режим «пока» ограничен пределом безопасности, чтобы приложение не зависло.",
          "Значение цикла"))
def flow_repeat(mode, value, actions, safety_limit):
    acts = collect_actions(actions)
    body = [line for a in acts for line in str(a.get("expression") or "pass").splitlines()] or ["pass"]
    limit = max(1, int(num(safety_limit, 10000)))
    if txt(mode) == "для каждого":
        head = f"for _nf_i, _nf_item in enumerate({u.code_of(value)} or []):"
        prefix = ["    self._nf_state['_loop_index'] = _nf_i",
                  "    self._nf_state['_loop_item'] = _nf_item"]
    elif txt(mode) == "пока":
        head = f"for _nf_i in range({limit}):"
        prefix = [f"    if not nf_flag({u.code_of(value)}): break",
                  "    self._nf_state['_loop_index'] = _nf_i"]
    else:
        head = f"for _nf_i in range(max(0, min(int({u.code_of(value)}), {limit}))):"
        prefix = ["    self._nf_state['_loop_index'] = _nf_i",
                  "    self._nf_state['_loop_item'] = _nf_i"]
    code = [head] + prefix + ["    " + line for line in body]
    return u.action("\n".join(code), imports=imports_of(value, *acts), label="повтор")


@flow("Значение цикла",
      inputs=[p("what", "text", "элемент", "Что взять",
                choices=["элемент", "номер"])],
      outputs=[p("value", "expression", None, "Значение")],
      tags=["loop", "index", "item"],
      **h("Возвращает текущий элемент или номер повтора внутри ноды «Повторить».",
          "Выберите элемент/номер и подключите к действиям, выполняемым внутри цикла.",
          "Работает только во время выполнения цикла.",
          "К формулам, памяти, сетке, рисованию.",
          "Номер цикла → колонка сетки.",
          "Вне цикла значение равно 0 или отсутствует."))
def loop_value(what):
    key = "_loop_item" if txt(what) == "элемент" else "_loop_index"
    return u.expression(f"self._nf_state.get({key!r}, 0)", label=txt(what))


@flow("Показать значение",
      inputs=[p("target", "widget", None, "Куда"),
              p("value", "value", "", "Значение"),
              p("prefix", "text", "", "Префикс")],
      outputs=[p("action", "action", None, "Действие")],
      tags=["display", "вывод"],
      **h("Показывает актуальное runtime-значение в виджете.",
          "Подключите надпись/поле, значение и затем действие к событию.",
          "Любой виджет с текстом и любое runtime-значение.",
          "К таймеру, клавише, старту.",
          "Надпись + score + «Счёт: ».",
          "Если виджет не подключён, текст уйдёт в строку состояния окна."))
def show_value(target, value, prefix):
    return u.action(
        f"self.nf_show({name_of(target, '')!r}, {u.code_of(value)}, {txt(prefix)!r})",
        imports=imports_of(value), label="показать")


@flow("Управление таймером",
      inputs=[p("name", "text", "game", "Имя"),
              p("operation", "text", "запустить", "Команда",
                choices=["запустить", "остановить", "переключить"]),
              p("interval", "value", None, "Новый интервал")],
      outputs=[p("action", "action", None, "Действие")],
      tags=["timer", "start", "stop"],
      **h("Запускает, останавливает или переключает созданный таймер.",
          "Укажите ровно то же имя, что у события таймера, и подключите действие к кнопке/клавише.",
          "Имя таймера и необязательный новый интервал.",
          "К событию клавиши, кнопки или старта.",
          "SPACE → переключить game.",
          "Несовпадающее имя ничего не изменит."))
def timer_control(name, operation, interval):
    interval_code = "None" if interval is None else u.code_of(interval)
    return u.action(
        f"self.nf_timer({u.ident(txt(name), 'timer')!r}, {txt(operation)!r}, {interval_code})",
        imports=imports_of(interval), label="таймер")


@flow("Перерисовать холст",
      inputs=[p("canvas", "widget", None, "Живой холст")],
      outputs=[p("action", "action", None, "Действие")],
      tags=["repaint", "update", "canvas"],
      **h("Просит динамический холст заново выполнить событие рисования.",
          "Подключите живой холст, затем действие после изменения памяти.",
          "Только «Живой холст».",
          "К таймеру, клавише, мыши после изменения данных.",
          "Изменить x → Перерисовать холст.",
          "Не ставьте перерисовку внутрь события рисования."))
def repaint_canvas(canvas):
    return u.action(f"self.{name_of(canvas)}.update()", label="перерисовать")


@grid("2D-сетка: создать",
      inputs=[p("name", "text", "field", "Имя"),
              p("columns", "number", 10, "Колонки"),
              p("rows", "number", 20, "Строки"),
              p("fill", "value", 0, "Заполнение")],
      outputs=[p("setup", "binding", None, "Подключение к окну"),
               p("grid", "grid2d", None, "Сетка")],
      tags=["matrix", "поле", "таблица"],
      **h("Создаёт изменяемое прямоугольное поле — для игр, карт, таблиц и автоматов.",
          "Задайте размер и имя. setup подключите к окну, grid — к запросам и рисованию.",
          "Размеры и начальное значение ячейки.",
          "setup → окно; grid → нарисовать сетку.",
          "field: 10×20, заполнение 0.",
          "Очень большая сетка замедляет рисование. Индексы начинаются с нуля."))
def grid_create(name, columns, rows, fill):
    key = u.ident(txt(name), "field")
    initial = f"nf_grid({int(num(columns, 10))}, {int(num(rows, 20))}, {u.code_of(fill)})"
    return (u.runtime("state", name=key, initial=initial),
            u.expression(f"self.nf_get({key!r}, [])", label=key))


@grid("2D-сетка: изменить",
      inputs=[p("name", "text", "field", "Имя сетки"),
              p("operation", "text", "записать ячейку", "Операция",
                choices=["записать ячейку", "очистить ячейку",
                         "удалить строку", "очистить поле"]),
              p("column", "value", 0, "Колонка"),
              p("row", "value", 0, "Строка"),
              p("value", "value", 1, "Значение")],
      outputs=[p("action", "action", None, "Действие")],
      tags=["cell", "row", "матрица"],
      **h("Меняет ячейку, строку или всю 2D-сетку во время события.",
          "Укажите имя созданной сетки, операцию и координаты. Подключите действие к событию.",
          "Координаты могут приходить от мыши, цикла или памяти.",
          "К событиям таймера, мыши, клавиши.",
          "Клик мыши → записать ячейку field[col,row] = 1.",
          "Координаты вне поля игнорируются; первая строка и колонка имеют номер 0."))
def grid_change(name, operation, column, row, value):
    code = (f"self.nf_grid_change({u.ident(txt(name), 'field')!r}, "
            f"{txt(operation)!r}, {u.code_of(column)}, {u.code_of(row)}, "
            f"{u.code_of(value)})")
    return u.action(code, imports=imports_of(column, row, value), label="изменить сетку")


@grid("2D-сетка: узнать",
      inputs=[p("name", "text", "field", "Имя сетки"),
              p("question", "text", "значение ячейки", "Что узнать",
                choices=["значение ячейки", "ячейка существует",
                         "строка заполнена", "число колонок", "число строк"]),
              p("column", "value", 0, "Колонка"),
              p("row", "value", 0, "Строка"),
              p("empty", "value", 0, "Пустое значение")],
      outputs=[p("value", "expression", None, "Ответ")],
      tags=["query", "cell", "row"],
      **h("Читает данные 2D-сетки без её изменения.",
          "Выберите вопрос, задайте координаты и используйте ответ в условии или формуле.",
          "Имя сетки и при необходимости координаты.",
          "К «Если выполнить», формуле, показу значения.",
          "Строка 19 заполнена → удалить строку.",
          "«Строка заполнена» считает пустым значение из входа «Пустое значение»."))
def grid_query(name, question, column, row, empty):
    key = u.ident(txt(name), "field")
    base = f"self.nf_get({key!r}, [])"
    q = txt(question)
    if q == "ячейка существует":
        code = f"nf_grid_inside({base}, {u.code_of(column)}, {u.code_of(row)})"
    elif q == "строка заполнена":
        code = (f"(0 <= int({u.code_of(row)}) < len({base}) and "
                f"all(_v != {u.code_of(empty)} for _v in {base}[int({u.code_of(row)})]))")
    elif q == "число колонок":
        code = f"(len({base}[0]) if {base} else 0)"
    elif q == "число строк":
        code = f"len({base})"
    else:
        code = f"nf_grid_get({base}, {u.code_of(column)}, {u.code_of(row)}, {u.code_of(empty)})"
    return u.expression(code, imports=imports_of(column, row, empty), label=q)


@paint("Живой холст",
       inputs=[p("name", "text", "game_canvas", "Имя"),
               p("columns", "number", 20, "Колонки"),
               p("rows", "number", 20, "Строки"),
               p("cell_size", "number", 24, "Размер клетки"),
               p("background", "color", "#1c1f26", "Фон")],
       outputs=[p("widget", "widget", None, "Холст")],
       tags=["canvas", "dynamic", "игра"],
       **h("Динамический холст для рисования и событий мыши во время работы.",
           "Добавьте его в компоновку, подключите к событиям мыши/рисования и к перерисовке.",
           "Размер сетки, клетки и цвет фона.",
           "К компоновке, событию рисования, событию мыши, перерисовке.",
           "10×20 клеток по 24 px для игрового поля.",
           "Это не старый статичный «Холст рисования»; команды фигур подключаются через событие.",
           "Событие: рисование холста; Нарисовать фигуру"))
def live_canvas(name, columns, rows, cell_size, background):
    return u.widget("LiveCanvas", name=txt(name) or "game_canvas",
                    helper="LiveCanvas",
                    extra={"columns": max(1, int(num(columns, 20))),
                           "rows": max(1, int(num(rows, 20))),
                           "cell_size": max(1, int(num(cell_size, 24))),
                           "background": txt(background) or "#1c1f26"})


@paint("Нарисовать фигуру",
       inputs=[p("shape", "text", "cell", "Фигура",
                 choices=["cell", "rect", "ellipse", "line", "text", "clear"]),
               p("x", "value", 0, "X / колонка"),
               p("y", "value", 0, "Y / строка"),
               p("width", "value", 20, "Ширина / X2"),
               p("height", "value", 20, "Высота / Y2"),
               p("color", "value", "#4ecca3", "Цвет"),
               p("text", "value", "", "Текст"),
               p("size", "value", 20, "Клетка / шрифт / линия")],
       outputs=[p("action", "action", None, "Команда рисования")],
       tags=["paint", "shape", "cell"],
       **h("Рисует одну универсальную фигуру на живом холсте.",
           "Выберите вид, заполните используемые координаты и подключите к событию рисования.",
           "Координаты и значения могут приходить из памяти/цикла.",
           "Только к «Событие: рисование холста».",
           "cell: x=колонка, y=строка, size=размер клетки.",
           "Команда использует переменную draw и вне события рисования работать не будет."))
def draw_shape(shape, x, y, width, height, color, text, size):
    vals = (x, y, width, height, color, text, size)
    c = [u.code_of(v) for v in vals]
    kind = txt(shape)
    if kind == "rect":
        code = f"draw.rect({c[0]}, {c[1]}, {c[2]}, {c[3]}, {c[4]})"
    elif kind == "ellipse":
        code = f"draw.ellipse({c[0]}, {c[1]}, {c[2]}, {c[3]}, {c[4]})"
    elif kind == "line":
        code = f"draw.line({c[0]}, {c[1]}, {c[2]}, {c[3]}, {c[4]}, {c[6]})"
    elif kind == "text":
        code = f"draw.text({c[0]}, {c[1]}, {c[5]}, {c[4]}, {c[6]})"
    elif kind == "clear":
        code = f"draw.clear({c[4]})"
    else:
        code = f"draw.cell({c[0]}, {c[1]}, {c[6]}, {c[4]})"
    return u.action(code, imports=imports_of(*vals), label="рисование")


@paint("Нарисовать 2D-сетку",
       inputs=[p("grid", "grid2d", None, "Сетка"),
               p("cell_size", "value", 24, "Размер клетки"),
               p("colors", "dict", None, "Цвета"),
               p("gap", "value", 1, "Зазор")],
       outputs=[p("action", "action", None, "Команда рисования")],
       tags=["grid", "matrix", "paint"],
       **h("Рисует все непустые ячейки 2D-сетки одной нодой.",
           "Подключите выход созданной сетки, размер клетки и при желании словарь цветов.",
           "2D-сетка; colors вида {1:'#ff0000', 2:'#00ff00'}.",
           "К событию рисования.",
           "field → Нарисовать 2D-сетку → Событие рисования.",
           "Значения 0, False, None и пустая строка считаются пустыми."))
def draw_grid(grid, cell_size, colors, gap):
    return u.action(
        f"draw.grid({u.code_of(grid)}, {u.code_of(cell_size)}, {u.code_of(colors)}, {u.code_of(gap)})",
        imports=imports_of(grid, cell_size, colors, gap), label="рисовать сетку")
