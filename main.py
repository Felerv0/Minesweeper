from random import randrange
import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QDialogButtonBox, QVBoxLayout, \
    QLabel, QPushButton, QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import QRegExp, Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QRegExpValidator, QIcon, QFontDatabase, QFont

BOMB = -1
COLORS = ['#0000ff', '#007c00', '#ff0000', '#00007c', '#7c0000', '#007c7c', '#000000', '#7c7c7c']
MODES = {"Начинающий": (9, 9, 10), "Продвинутый": (16, 16, 40), "Эксперт": (16, 30, 99)}
DIFFICULTIES = {"Начинающий": "beginner", "Продвинутый": "intermediate", "Эксперт": "expert"}

STATUS_DEFAULT = "🙂"
STATUS_WIN = "😎"
STATUS_LOSE = "😵"
STATUS_OPENING = "😯"
# assets
IMAGE_BOMB = 'assets/images/bomb.png'
IMAGE_FLAG = 'assets/images/flag.png'
IMAGE_CROSSED_FLAG = 'assets/images/flag_crossed.png'
IMAGE_SETTINGS = 'assets/images/settings.png'
IMAGE_LOGOUT = 'assets/images/logout.png'
FONT_NUMBERS = 'assets/fonts/Anton-Regular.ttf'
APP_ICON = 'assets/images/icon.ico'


class Minesweeper:  # класс с самой игрой, где хранится поле, настройки и статус игры
    def __init__(self, width, height, mines):
        self.touched = False
        self.game_status = 0  # -1 - поражение  0 - идёт игра  1 - победа
        self.width = width
        self.height = height
        self.flags = mines
        self.mines = 0
        self.field = []

        self.createField()

    def createField(self):  # создание поля
        self.mines = 0
        self.field = []
        for row in range(self.height):
            self.field.append([Cell((row, col), 0) for col in range(self.width)])

        mine_cords = []
        while self.mines < self.flags:
            row, col = randrange(self.height), randrange(self.width)
            if self.field[row][col].isBomb():
                continue
            self.mines += 1
            self.field[row][col].n = BOMB
            mine_cords.append((row, col))
        for cords in mine_cords:
            for row in (-1, 0, 1):
                for col in (-1, 0, 1):
                    if 0 <= cords[0] + row < self.height and 0 <= cords[1] + col < self.width:
                        if not self.field[cords[0] + row][cords[1] + col].isBomb():
                            self.field[cords[0] + row][cords[1] + col] += 1

    def openCell(self, row, col):  # открытие клетки
        if not self.touched:
            self.touched = True  # флажок того, что игра не начиналась

        if not self.field[row][col].flagged and self.game_status == 0:  # рекурсия
            self.field[row][col].open(False)
            if self.field[row][col] == 0:
                for r in (-1, 0, 1):
                    for c in (-1, 0, 1):
                        if 0 <= r + row < self.height and 0 <= c + col < self.width:
                            if not self.field[r + row][c + col].opened and not self.field[row + r][col + c].flagged:
                                self.openCell(row + r, col + c)
            elif self.field[row][col].isBomb():
                self.boom()
        self.checkWin()

    def boom(self):  # проигрыш
        self.game_status = -1

    def win(self):  # выигрыш
        self.game_status = 1

    def isWin(self):  # проверка на выигрыш
        return self.game_status == 1

    def isLose(self):  # проверка на проигрыш
        return self.game_status == -1

    def placeFlag(self, row, col):  # установка флага
        if (self.flags > 0 or self.field[row][col].flagged) and self.game_status == 0:
            self.field[row][col].flag()
        self.flags = self.mines - len([1 for i in self.field for j in i if j.flagged])  # обновление количества флагов

    def checkWin(self):  # проверка победы
        if len([j for i in self.field for j in i if not j.opened]) == self.mines:
            self.win()

    def debug_printField(self):  # вывод поля в консоль
        print('\n'.join([' '.join([str(j.n).replace('-1', '*') for j in i]) for i in self.field]), end='\n\n')


class Cell(QPushButton):  # класс клетки, хранит в себе координаты и значение
    rightClicked = pyqtSignal()  # добавление своих сигналов
    revealed = pyqtSignal()

    def __init__(self, cords, n):
        super().__init__()
        self.n = n
        self.cords = cords
        self.opened = False
        self.flagged = False

        self.initUI()

    def initUI(self):
        self.setFixedSize(25, 25)
        self.setIconSize(QSize(20, 20))
        self.setStyleSheet("border-right: 2px solid #7c7c7c; background-color: #bebebe; text-align: center;"
                           "border-bottom: 2px solid #7c7c7c; border-top: 2px solid #fff;"
                           "border-left: 2px solid #fff; overflow: hidden; outline: none;")

    def __ne__(self, other):
        return self.n != other

    def __eq__(self, other):
        return self.n == other

    def __iadd__(self, other):
        return Cell(self.cords, self.n + other)

    def isBomb(self):  # проверка на мину
        return self.n == -1

    def open(self, lose):  # визуальное открытие клетки
        self.opened = True
        self.setStyleSheet("border: 1px solid #7c7c7c; background-color: #bebebe; text-align: center;"
                           f"overflow: hidden; outline: none; font-size: 20px; color: {COLORS[self.n - 1]}")
        if self.flagged and lose:
            if not self.isBomb():
                self.setIcon(QIcon(IMAGE_CROSSED_FLAG))
        elif self.n > 0:
            self.setText(str(self.n))
        elif self.isBomb():
            self.setStyleSheet("border: 1px solid #7c7c7c; background-color: red; text-align: center;")
            self.setIcon(QIcon(IMAGE_BOMB))

    def flag(self):  # постановка флага
        if not self.opened:
            self.flagged = not self.flagged
            if self.flagged:
                self.setIcon(QIcon(IMAGE_FLAG))
            else:
                self.setIcon(QIcon())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)  # вызов базового события нажатия мыши, чтобы не забыть сигнал clicked
        if event.button() == Qt.RightButton:
            self.rightClicked.emit()  # эмитация своего сигнала при ПКМ
        elif event.button() == Qt.LeftButton and not self.opened and not self.flagged:
            self.setStyleSheet("border: 1px solid #7c7c7c; background-color: #bebebe; text-align: center;")

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not self.opened and event.button() == Qt.LeftButton:  # при отпускании мыши возвращает кнопке стиль
            self.setStyleSheet("border-right: 2px solid #7c7c7c; background-color: #bebebe; text-align: center;"
                               "border-bottom: 2px solid #7c7c7c; border-top: 2px solid #fff;"
                               "border-left: 2px solid #fff; overflow: hidden; outline: none;")
        self.revealed.emit()


class Game(QMainWindow):  # основной класс игры с интерфейсом, настройками и т.д.
    def __init__(self, nickname):
        super().__init__()
        self.nickname = nickname
        self.field = []
        self.game = 0
        self.currentTime = 0
        self.recorded = False
        self.timerID = QTimer(self)
        self.timerID.timeout.connect(self.updateTimer)

        self.width, self.height, self.mines = MODES['Продвинутый']
        self.status = STATUS_DEFAULT

        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon(APP_ICON))
        font_id = QFontDatabase.addApplicationFont(FONT_NUMBERS)
        self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        uic.loadUi('main.ui', self)
        self.leaderboard_btn.setText(self.nickname)
        self.leaderboard_btn.resize(self.leaderboard_btn.sizeHint())
        self.setWindowTitle(f"Сапёр ({self.nickname})")
        self.logout_btn.setIcon(QIcon(IMAGE_LOGOUT))
        self.settings_btn.setIcon(QIcon(IMAGE_SETTINGS))
        self.play_btn.setText(STATUS_DEFAULT)
        self.logout_btn.clicked.connect(self.logout)

        self.play_btn.clicked.connect(self.newGame)
        self.settings_btn.clicked.connect(self.settings_window)
        self.leaderboard_btn.clicked.connect(self.leaderboard_window)

    def newGame(self):  # создание нового поля
        self.initGame(self.width, self.height, self.mines)
        self.paintField(self.width, self.height, self.mines)

    def initGame(self, width, height, mines):  # инициализация нового объекта игры
        self.game = Minesweeper(width, height, mines)

    def paintField(self, width, height, mines):  # отображение поля
        self.recorded = False
        self.status = STATUS_DEFAULT
        self.setCurrentStatus()
        for i in reversed(range(self.grid.count())):  # очистить сетку
            self.grid.itemAt(i).widget().close()
        self.flags_count.display(self.game.flags)
        for row in range(height):  # добавление элементов в таблицу и добавление сигналов к ним
            for col in range(width):
                self.grid.addWidget(self.game.field[row][col], row, col)
                self.game.field[row][col].clicked.connect(self.clickedCell)
                self.game.field[row][col].rightClicked.connect(self.rightClickedCell)
                self.game.field[row][col].pressed.connect(self.changeStatusOpening)
                self.game.field[row][col].revealed.connect(self.revealedCell)
                self.game.field[row][col].setFont(QFont('Anton'))
        self.resetTimer()

        # self.game.debug_printField()

    def clickedCell(self):  # нажатие на клетку
        if not self.game.touched:  # проверка на мину или число на первом ходу => пересоздание поля
            is_new_field = False
            while self.game.field[self.sender().cords[0]][self.sender().cords[1]].isBomb() or \
                    self.game.field[self.sender().cords[0]][self.sender().cords[1]] != 0:
                is_new_field = True
                self.initGame(self.game.width, self.game.height, self.game.mines)
            if is_new_field:
                self.paintField(self.game.width, self.game.height, self.game.mines)

            self.currentTime = 0
            self.timerID.start(1000)
        self.game.openCell(*self.sender().cords)

        if not self.recorded:  # если результат записан в рекорды, то он не перезаписывается ещё раз при нажатии
            if self.game.isWin():
                self.recorded = True
                self.stopTimer()
                self.status = STATUS_WIN
                for row in range(self.game.height):
                    for col in range(self.game.width):
                        if not self.game.field[row][col].flagged:
                            self.game.field[row][col].flag()
                self.flags_count.display(0)
                self.saveRecord(self.currentTime)
            elif self.game.isLose():
                self.recorded = True
                self.stopTimer()
                self.status = STATUS_LOSE
                for row in range(self.game.height):
                    for col in range(self.game.width):
                        self.game.field[row][col].open(True)
                self.addStats(False)

    def saveRecord(self, record_time):  # сохранение рекорда
        if (self.game.width, self.game.height, self.game.mines) not in MODES.values():
            return
        dif = DIFFICULTIES[list(MODES.keys())[list(MODES.values()).index((self.game.width, self.game.height, self.game.mines))]]
        con = sqlite3.connect('users.db')
        cur = con.cursor()
        res = cur.execute("""SELECT * FROM results WHERE 
                                id = (SELECT id FROM users WHERE nickname = ?)""",
                          (self.nickname,)).fetchall()
        if len(res) == 0:
            cur.execute("""INSERT INTO results VALUES((SELECT id FROM users 
                        WHERE nickname = ?), NULL, NULL, NULL)""", (self.nickname,))
            cur.execute(f"""UPDATE results SET {dif} = {record_time} 
                    WHERE id = (SELECT id FROM users WHERE nickname = '{self.nickname}')""")
        else:
            last_record = cur.execute(f"""SELECT {dif} FROM results WHERE
                    id = (SELECT id FROM users WHERE nickname = '{self.nickname}')""").fetchall()
            if last_record[0][0] is None:
                cur.execute(f"""UPDATE results SET {dif} = {record_time} WHERE
                    id = (SELECT id FROM users WHERE nickname = '{self.nickname}')""")
            elif last_record[0][0] > record_time:
                cur.execute(f"""UPDATE results SET {dif} = {record_time} WHERE 
                    id = (SELECT id FROM users WHERE nickname = '{self.nickname}')""")
        con.commit()
        self.addStats(True)

    def addStats(self, win):  # добавляет значения в статистику
        con = sqlite3.connect('users.db')
        cur = con.cursor()
        res = cur.execute(f"""SELECT * FROM stats WHERE 
                id = (SELECT id FROM users WHERE nickname = '{self.nickname}')""").fetchall()
        if len(res) == 0:
            pass
        else:
            if win:
                cur.execute(f"""UPDATE stats SET wins = {res[0][1] + 1} WHERE 
                    id = (SELECT id FROM users WHERE nickname = '{self.nickname}')""")
            else:
                cur.execute(f"""UPDATE stats SET loses = {res[0][2] + 1} WHERE 
                    id = (SELECT id FROM users WHERE nickname = '{self.nickname}')""")
        con.commit()
        con.close()

    def changeStatusOpening(self):  # изменение смайлика на кнопке при нажатии
        if self.status == STATUS_DEFAULT:
            self.status = STATUS_OPENING
            self.setCurrentStatus()

    def stopTimer(self):  # остановка таймера
        self.timerID.stop()

    def updateTimer(self):  # обновление таймера
        self.currentTime += 1
        self.timer.display(self.currentTime)

    def resetTimer(self):  # сброс таймера
        self.timerID.stop()
        self.currentTime = 0
        self.timer.display(0)

    def rightClickedCell(self):  # при ПКМ по клетке
        self.game.placeFlag(*self.sender().cords)
        self.flags_count.display(self.game.flags)

    def settings_window(self):  # вызов окна настроек
        self.settings_popup = Settings(self.width, self.height, self.mines)
        self.settings_popup.show()
        self.settings_popup.accepted.connect(self.acceptSettings)

    def leaderboard_window(self):  # вызов окна рекордов
        self.leaderboard = Leaderboard(self.nickname)
        self.leaderboard.show()

    def acceptSettings(self):  # применение настроек
        self.height, self.width, self.mines = self.settings_popup.getSettings()

    def logout(self):  # выход
        popup = PopupDialog()
        if popup.exec():
            self.login_window = Login()
            self.login_window.show()
            self.close()

    def revealedCell(self):  # отпускание мыши от клетки
        if self.status == STATUS_OPENING:
            self.status = STATUS_DEFAULT
        self.setCurrentStatus()

    def setCurrentStatus(self):  # обновление смайлика
        self.play_btn.setText(self.status)


class PopupDialog(QDialog):  # класс диалога выхода из аккаунта
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выход из аккаунта")

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel("Вы действительно хотите выйти из аккаунта?")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class Settings(QDialog):  # класс окна настроек
    def __init__(self, width, height, mines):
        super().__init__()
        uic.loadUi('settings.ui', self)
        self.setWindowTitle("Настройки")

        self.width_input.setValue(width)
        self.height_input.setValue(height)
        self.mines.setValue(mines)
        self.setToCustom()

        self.combo.activated.connect(self.changeNumbers)
        self.height_input.valueChanged.connect(self.setToCustom)
        self.width_input.valueChanged.connect(self.setToCustom)
        self.mines.valueChanged.connect(self.setToCustom)
        self.pushButton.clicked.connect(self.acceptSettings)

    def getSettings(self):  # получение кортежа настроек
        return self.height_input.value(), self.width_input.value(), self.mines.value()

    def acceptSettings(self):  # принятие настроек по нажатию на кнопку
        if 0.09 < self.mines.value() / (self.width_input.value() * self.height_input.value()) < 0.26:
            self.accept()
        else:
            self.error.setText('Некорректное количество мин')

    def setToCustom(self):  # переводит список выбора на режим "свой"
        if self.getSettings() not in MODES.values():
            self.combo.setCurrentIndex(3)
        else:
            self.combo.setCurrentIndex(list(MODES.values()).index(self.getSettings()))

    def changeNumbers(self):  # вызывается для изменения чисел в настройках при переключении режимов
        if self.sender().currentText() != 'Свой':
            s = MODES[self.sender().currentText()]
            self.height_input.setValue(s[0])
            self.width_input.setValue(s[1])
            self.mines.setValue(s[2])


class Leaderboard(QMainWindow):  # окно таблицы лидеров
    def __init__(self, nickname):
        self.nickname = nickname

        self.con = sqlite3.connect('users.db')
        self.cur = self.con.cursor()
        stats = self.cur.execute(f"""SELECT * FROM stats WHERE 
                id = (SELECT id FROM users WHERE nickname = '{self.nickname}')""").fetchall()

        super().__init__()
        uic.loadUi('leaderboard.ui', self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Ник', 'Время'])
        self.setWindowTitle('Таблица лидеров')
        self.stat_label.setText(f"Статистика {self.nickname}")
        self.boom_count.setText(str(stats[0][2]))
        self.wins_count.setText(str(stats[0][1]))
        count = stats[0][1] + stats[0][2]
        if count == 0:
            count = 1
        self.percent.setText(str(round(stats[0][1] / count * 100, 2)) + '%')
        self.combo.activated.connect(self.updateTable)
        self.updateTable()

    def updateTable(self):  # обновление таблицы рекордов
        dif = DIFFICULTIES[self.combo.currentText()]
        results = self.cur.execute(f"""SELECT users.nickname, results.{dif} FROM results INNER JOIN users 
            ON users.id = results.id WHERE {dif} NOT NULL ORDER BY {dif}""").fetchall()
        if len(results) == 0:
            self.msg.setText('Нет рекордов!')
            return
        else:
            self.msg.setText(f"Вы на позиции {[i[0] for i in results].index(self.nickname) + 1}")
            self.table.setRowCount(len(results))
            for i, elem in enumerate(results):
                for j, s in enumerate(elem):
                    item = QTableWidgetItem(str(s))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.table.setItem(i, j, item)


class Registration(QMainWindow):  # окно регистрации
    def __init__(self):
        super().__init__()
        uic.loadUi('registration.ui', self)
        self.setWindowTitle("Регистрация")
        self.reg_btn.clicked.connect(self.registrate)
        self.nickname.setValidator(QRegExpValidator(QRegExp("^[a-zA-Z0-9]{0,20}$")))
        self.login_btn.clicked.connect(self.login)
        self.password.returnPressed.connect(self.registrate)
        self.verify_pw.returnPressed.connect(self.registrate)

    def login(self):  # открывает окно входа
        self.login_window = Login()
        self.login_window.show()
        self.close()

    def registrate(self):  # зарегистрироваться
        if len(self.nickname.text()) < 4:
            self.error.setText('Слишком короткий ник!')
        elif len(self.password.text()) < 7:
            self.error.setText('Слишком короткий пароль!')
        elif len(self.nickname.text()) > 20 or len(self.password.text()) > 20:
            self.error.setText('Слишком длинный ник или пароль!')
        elif self.password.text() != self.verify_pw.text():
            self.error.setText('Пароли не совпадают!')
        else:
            con = sqlite3.connect('users.db')
            cur = con.cursor()
            nicknames = [str(i[0]) for i in cur.execute("""SELECT nickname FROM users""").fetchall()]
            if self.nickname.text() in nicknames:
                self.error.setText('Такой ник уже занят!')
            else:
                self.error.setText('Регистрация прошла успешно!')
                cur.execute("""INSERT INTO users(nickname, password) VALUES(?, ?)""",
                            (self.nickname.text(), self.password.text()))
                cur.execute("""INSERT INTO stats VALUES((SELECT id FROM users WHERE nickname = ?), 0, 0)""",
                            (self.nickname.text(),))
                con.commit()
                con.close()


class Login(QMainWindow):  # окно входа
    def __init__(self):
        super().__init__()
        uic.loadUi('login.ui', self)
        self.setWindowTitle("Вход")
        self.login_btn.clicked.connect(self.login_system)
        self.reg_btn.clicked.connect(self.reg_system)
        self.nickname.setValidator(QRegExpValidator(QRegExp("^[a-zA-Z0-9\n]{0,20}$")))
        self.nickname.returnPressed.connect(self.login_system)
        self.password.returnPressed.connect(self.login_system)

    def reg_system(self):  # открытие окна регистрации
        self.reg = Registration()
        self.reg.show()
        self.close()

    def login_system(self):  # вход
        if len(self.nickname.text()) > 20 or len(self.password.text()) > 20:
            self.error.setText('Слишком длинный логин или пароль')
        else:
            con = sqlite3.connect('users.db')
            cur = con.cursor()
            result = cur.execute("""SELECT * FROM users WHERE nickname = ? AND password = ?""",
                                 (self.nickname.text(), self.password.text())).fetchall()
            if len(result) == 0:
                self.error.setText('Неправильный логин или пароль!')
            else:
                con.close()
                self.main = Game(self.nickname.text())
                self.main.show()
                self.close()
            con.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = Login()
    gui.show()
    sys.exit(app.exec_())