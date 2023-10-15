class Ui:
    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    def __del__(self):
        Ui.__instance = None

    def __init__(self, curses, stdscr):
        self.crs = curses
        self.scr = stdscr
        self.crs.noecho() # отключить отображение клавиш на экране
        self.crs.cbreak() # немедленно получать нажатия клавиш без буферизации (нажатия Enter)
        self.crs.curs_set(False) # скрыть/показать курсор
        self.crs.use_default_colors()
        self.crs.start_color()
        self.crs.init_pair(1, self.crs.COLOR_RED, -1)
        self.crs.init_pair(2, self.crs.COLOR_YELLOW, -1)
        self.crs.init_pair(3, self.crs.COLOR_GREEN, -1)
        self.crs.init_pair(4, self.crs.COLOR_BLUE, -1)
        self.crs.init_pair(9, 8, -1)
        self.r, self.y, self.g, self.b, self.c, self.d = \
            self.crs.color_pair(1), self.crs.color_pair(2), self.crs.color_pair(3), \
            self.crs.color_pair(4), self.crs.color_pair(0), self.crs.color_pair(9)
        self.cm = {'r':self.r, 'y':self.y, 'g':self.g, 'b':self.b, 'c':self.c, 'd':self.d}
        self.scr.keypad(True) # интерпретировать специальные клавиши как одиночные символы
        self.scr.clear()
        self.scr.refresh()
