import random
from socket import *
from threading import Thread
from customtkinter import *

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(("127.0.0.1", 7070))

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
game_mode = "LOCAL"
room_id = "Global"
current_turn = "X"
board_state = [""] * 9
ttt_buttons = []
ttt_status = None
game_active = True
public_rooms = []
rooms_listbox_frame = None

# --- ТЕМЫ И СТИЛИ ИНТЕРФЕЙСА ---
THEMES = {
    "Неоновый": {
        "bg": "#0d0f18", "panel": "#16192b", "chat_bg": "#101322",
        "msg_in": "#1c213b", "msg_out": "#2e1065",
        "accent": "#00f0ff", "secondary": "#ff007f", "win": "#00ff66",
        "text": "#e2e8f0", "btn_text": "#ffffff", "font": "Arial"
    },
    "Aero": {
        "bg": "#e0f2fe", "panel": "#bae6fd", "chat_bg": "#f0f9ff",
        "msg_in": "#ffffff", "msg_out": "#38bdf8",
        "accent": "#0284c7", "secondary": "#f43f5e", "win": "#10b981",
        "text": "#0f172a", "btn_text": "#ffffff", "font": "Segoe UI"
    },
    "Ретро 8-Бит": {
        "bg": "#181818", "panel": "#282828", "chat_bg": "#121212",
        "msg_in": "#3c3836", "msg_out": "#b8bb26",
        "accent": "#fabd2f", "secondary": "#fb4934", "win": "#b8bb26",
        "text": "#ebdbb2", "btn_text": "#282828", "font": "Courier"
    },
    "Тёмный Минимализм": {
        "bg": "#121212", "panel": "#1e1e1e", "chat_bg": "#181818",
        "msg_in": "#252525", "msg_out": "#333333",
        "accent": "#ffffff", "secondary": "#888888", "win": "#4caf50",
        "text": "#ffffff", "btn_text": "#000000", "font": "Arial"
    }
}

current_theme_name = "Неоновый"
T = THEMES[current_theme_name]


# --- СЕТЕВОЕ ВЗАИМОДЕЙСТВИЕ ---
def send_msg():
    message = h.get()
    if message:
        try:
            client_socket.send(f"MSG:{message}".encode('utf-8'))
            h.delete(0, "end")
        except Exception as e:
            print(e)


def recv_message():
    global current_turn, game_active, public_rooms
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            # Получение списка публичных комнат
            if message.startswith("GAME:TTT:ROOMS_LIST:"):
                raw_rooms = message.split(":")[3]
                if raw_rooms == "EMPTY" or not raw_rooms:
                    public_rooms = []
                else:
                    public_rooms = raw_rooms.split(",")
                update_rooms_ui(public_rooms)

            # Ходы в сетевых Крестиках-Ноликах
            elif message.startswith("GAME:TTT:MOVE:"):
                parts = message.split(":")
                recv_room, idx_str, symbol = parts[3], parts[4], parts[5]
                idx = int(idx_str)
                if game_mode == "NET" and room_id == recv_room and ttt_buttons and idx < len(ttt_buttons):
                    apply_move(idx, symbol)

            elif message.startswith("GAME:TTT:RESET:"):
                recv_room = message.split(":")[3]
                if game_mode == "NET" and room_id == recv_room:
                    reset_board_ui()

            # Чат
            elif message.startswith("MSG:"):
                text = message[4:]
                g.configure(state="normal")
                g.insert("end", f"💬 {text}\n")
                g.configure(state="disabled")
                g.see("end")
            else:
                g.configure(state="normal")
                g.insert("end", f"{message}\n")
                g.configure(state="disabled")
                g.see("end")
        except:
            break


# --- СМЕНА СТИЛЕЙ ---
def apply_theme(theme_name):
    global current_theme_name, T
    current_theme_name = theme_name
    T = THEMES[theme_name]

    window.configure(fg_color=T["bg"])
    left_panel.configure(fg_color=T["panel"])
    chat_frame.configure(fg_color=T["chat_bg"])
    g.configure(fg_color=T["chat_bg"], text_color=T["text"], font=(T["font"], 13))
    h.configure(fg_color=T["panel"], text_color=T["text"], border_color=T["accent"], font=(T["font"], 13))

    btn_send.configure(fg_color=T["accent"], text_color=T["btn_text"], font=(T["font"], 12, "bold"))
    btn_games.configure(fg_color=T["secondary"], text_color=T["btn_text"], font=(T["font"], 12, "bold"))
    theme_selector.configure(fg_color=T["panel"], text_color=T["text"], button_color=T["accent"])


# --- ОКНО ИГР ---
def open_games_window():
    games_win = CTkToplevel(window)
    games_win.title("🎮 ИГРОВОЙ ЦЕНТР")
    games_win.geometry("360x320")
    games_win.configure(fg_color=T["bg"])
    games_win.attributes("-topmost", True)

    label = CTkLabel(games_win, text="ВЫБЕРИТЕ ИГРУ", font=(T["font"], 18, "bold"), text_color=T["accent"])
    label.pack(pady=15)

    btn_ttt = CTkButton(
        games_win, text="❌⭕ Крестики-Нолики", command=open_ttt_mode_select,
        fg_color=T["panel"], border_width=2, border_color=T["secondary"],
        text_color=T["text"], font=(T["font"], 14, "bold"), height=45
    )
    btn_ttt.pack(pady=10, fill="x", padx=30)

    btn_clicker = CTkButton(
        games_win, text="⚡ Неоновый Кликер", command=open_clicker,
        fg_color=T["panel"], border_width=2, border_color=T["accent"],
        text_color=T["text"], font=(T["font"], 14, "bold"), height=45
    )
    btn_clicker.pack(pady=10, fill="x", padx=30)


# --- РЕЖИМЫ КРЕСТИКОВ-НОЛИКОВ ---
def open_ttt_mode_select():
    select_win = CTkToplevel(window)
    select_win.title("Режим Игры")
    select_win.geometry("340x320")
    select_win.configure(fg_color=T["bg"])
    select_win.attributes("-topmost", True)

    lbl = CTkLabel(select_win, text="ВЫБЕРИТЕ РЕЖИМ", font=(T["font"], 16, "bold"), text_color=T["accent"])
    lbl.pack(pady=15)

    CTkButton(
        select_win, text="🤖 Игра с Ботом",
        command=lambda: start_ttt("BOT", select_win),
        fg_color=T["panel"], border_width=1, border_color=T["accent"], height=38
    ).pack(pady=6, fill="x", padx=30)

    CTkButton(
        select_win, text="👥 На одном ПК",
        command=lambda: start_ttt("LOCAL", select_win),
        fg_color=T["panel"], border_width=1, border_color=T["accent"], height=38
    ).pack(pady=6, fill="x", padx=30)

    CTkButton(
        select_win, text="🌐 Публичные Сервера",
        command=lambda: open_net_room_select(select_win),
        fg_color=T["panel"], border_width=1, border_color=T["secondary"], height=38
    ).pack(pady=6, fill="x", padx=30)


# --- ПОИСК И СПИСОК ПУБЛИЧНЫХ СЕРВЕРОВ ---
def open_net_room_select(parent):
    global rooms_listbox_frame
    parent.destroy()

    room_win = CTkToplevel(window)
    room_win.title("Публичные Сервера")
    room_win.geometry("420x480")
    room_win.configure(fg_color=T["bg"])
    room_win.attributes("-topmost", True)

    CTkLabel(room_win, text="🌐 СЕРВЕРА КРЕСТИКОВ-НОЛИКОВ", font=(T["font"], 15, "bold"), text_color=T["accent"]).pack(
        pady=10)

    # Поле поиска и кнопка обновления
    search_frame = CTkFrame(room_win, fg_color="transparent")
    search_frame.pack(fill="x", padx=20, pady=5)

    search_entry = CTkEntry(search_frame, placeholder_text="🔍 Поиск сервера...", font=(T["font"], 12))
    search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

    def on_search():
        query = search_entry.get().lower()
        filtered = [r for r in public_rooms if query in r.lower()]
        update_rooms_ui(filtered, room_win)

    CTkButton(search_frame, text="Найти", width=60, command=on_search, fg_color=T["accent"]).pack(side="left")

    # Контейнер списка серверов
    rooms_listbox_frame = CTkScrollableFrame(room_win, fg_color=T["panel"], height=200)
    rooms_listbox_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Создание своего сервера
    create_frame = CTkFrame(room_win, fg_color="transparent")
    create_frame.pack(fill="x", padx=20, pady=10)

    new_room_entry = CTkEntry(create_frame, placeholder_text="Имя нового сервера...", font=(T["font"], 12))
    new_room_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

    def create_server():
        global room_id
        r_name = new_room_entry.get()
        if r_name:
            room_id = r_name
            client_socket.send(f"GAME:TTT:CREATE_ROOM:{r_name}".encode('utf-8'))
            room_win.destroy()
            start_ttt("NET", None)

    CTkButton(create_frame, text="➕ Создать", width=80, command=create_server, fg_color=T["secondary"]).pack(
        side="left")

    # Запрос актуального списка при открытии
    client_socket.send("GAME:TTT:GET_ROOMS".encode('utf-8'))


def update_rooms_ui(rooms, parent_win=None):
    global rooms_listbox_frame
    if rooms_listbox_frame and rooms_listbox_frame.winfo_exists():
        for widget in rooms_listbox_frame.winfo_children():
            widget.destroy()

        if not rooms:
            CTkLabel(rooms_listbox_frame, text="Серверов пока нет. Создайте первый!", text_color=T["secondary"]).pack(
                pady=20)
            return

        for r in rooms:
            item = CTkFrame(rooms_listbox_frame, fg_color=T["bg"], height=40)
            item.pack(fill="x", pady=4, padx=5)

            CTkLabel(item, text=f"🎮 {r}", font=(T["font"], 13, "bold"), text_color=T["text"]).pack(side="left", padx=10)

            def join_selected(room_name=r):
                global room_id
                room_id = room_name
                if parent_win and parent_win.winfo_exists():
                    parent_win.destroy()
                start_ttt("NET", None)

            CTkButton(item, text="Войти", width=70, height=28, command=join_selected, fg_color=T["accent"]).pack(
                side="right", padx=10)


def start_ttt(mode, parent_win):
    global game_mode
    game_mode = mode
    if parent_win and parent_win.winfo_exists():
        parent_win.destroy()
    open_tic_tac_toe()


# --- ИГРОВОЕ ПОЛЕ КРЕСТИКИ-НОЛИКИ ---
def open_tic_tac_toe():
    global ttt_buttons, ttt_status, current_turn, game_active, board_state

    current_turn = "X"
    game_active = True
    board_state = [""] * 9

    ttt_win = CTkToplevel(window)
    ttt_win.title(f"Крестики-Нолики ({game_mode} - {room_id})")
    ttt_win.geometry("380x480")
    ttt_win.configure(fg_color=T["bg"])
    ttt_win.attributes("-topmost", True)

    title_map = {"BOT": "ИГРА С БОТОМ", "LOCAL": "ИГРА НА ОДНОМ ПК", "NET": f"СЕРВЕР: {room_id}"}

    CTkLabel(ttt_win, text=title_map[game_mode], font=(T["font"], 14, "bold"), text_color=T["accent"]).pack(
        pady=(10, 0))

    ttt_status = CTkLabel(ttt_win, text=f"Ход: {current_turn}", font=(T["font"], 16, "bold"), text_color=T["text"])
    ttt_status.pack(pady=5)

    board_frame = CTkFrame(ttt_win, fg_color=T["panel"], border_width=2, border_color=T["accent"])
    board_frame.pack(pady=5)

    ttt_buttons = []
    for i in range(9):
        btn = CTkButton(
            board_frame, text="", width=95, height=95,
            font=(T["font"], 32, "bold"),
            fg_color=T["bg"], hover_color=T["panel"],
            border_width=1, border_color=T["panel"],
            command=lambda idx=i: on_cell_click(idx)
        )
        btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)
        ttt_buttons.append(btn)

    CTkButton(
        ttt_win, text="🔄 ПЕРЕЗАПУСК", command=reset_game_request,
        fg_color=T["panel"], border_width=1, border_color=T["secondary"],
        text_color=T["text"], font=(T["font"], 12, "bold")
    ).pack(pady=15)


def on_cell_click(index):
    if not game_active or board_state[index] != "":
        return

    if game_mode == "NET":
        client_socket.send(f"GAME:TTT:MOVE:{room_id}:{index}:{current_turn}".encode('utf-8'))
    elif game_mode == "LOCAL":
        apply_move(index, current_turn)
    elif game_mode == "BOT":
        apply_move(index, "X")
        if game_active and "" in board_state:
            window.after(400, bot_make_move)


def bot_make_move():
    if not game_active:
        return
    empty_cells = [i for i, val in enumerate(board_state) if val == ""]
    if empty_cells:
        apply_move(random.choice(empty_cells), "O")


def apply_move(index, symbol):
    global current_turn, board_state

    board_state[index] = symbol
    color = T["accent"] if symbol == "X" else T["secondary"]
    ttt_buttons[index].configure(text=symbol, text_color=color)

    current_turn = "O" if symbol == "X" else "X"

    if ttt_status and game_active:
        ttt_status.configure(text=f"Ход: {current_turn}")

    check_ttt_winner()


def reset_game_request():
    if game_mode == "NET":
        client_socket.send(f"GAME:TTT:RESET:{room_id}".encode('utf-8'))
    else:
        reset_board_ui()


def reset_board_ui():
    global current_turn, game_active, board_state
    current_turn = "X"
    game_active = True
    board_state = [""] * 9
    if ttt_status:
        ttt_status.configure(text=f"Ход: {current_turn}", text_color=T["text"])
    for btn in ttt_buttons:
        btn.configure(text="", state="normal", fg_color=T["bg"])


def check_ttt_winner():
    global game_active
    combo = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for c in combo:
        if board_state[c[0]] == board_state[c[1]] == board_state[c[2]] != "":
            game_active = False
            winner = board_state[c[0]]
            ttt_status.configure(text=f"ПОБЕДИЛ {winner}! 🎉", text_color=T["win"])
            for idx in c:
                ttt_buttons[idx].configure(fg_color=T["panel"], border_color=T["win"])
            return

    if "" not in board_state and game_active:
        game_active = False
        ttt_status.configure(text="НИЧЬЯ! 🤝", text_color=T["accent"])


# --- ИГРА КЛИКЕР ---
def open_clicker():
    click_win = CTkToplevel(window)
    click_win.title("⚡ КЛИКЕР")
    click_win.geometry("300x220")
    click_win.configure(fg_color=T["bg"])
    click_win.attributes("-topmost", True)

    score = [0]

    def add_score():
        score[0] += 1
        btn_click.configure(text=f"КЛИКОВ: {score[0]}")
        if score[0] >= 30:
            btn_click.configure(state="disabled", text="ПОБЕДА! 🎉", border_color=T["win"])

    CTkLabel(click_win, text="НАЖМИ 30 РАЗ!", font=(T["font"], 16, "bold"), text_color=T["secondary"]).pack(pady=15)

    btn_click = CTkButton(
        click_win, text="ЖМИ!", width=180, height=60,
        font=(T["font"], 20, "bold"),
        fg_color=T["panel"], border_width=2, border_color=T["accent"],
        command=add_score
    )
    btn_click.pack(pady=10)


# --- ИНТЕРФЕЙС МЕССЕНДЖЕРА ---
window = CTk()
window.title("Telegram Client + Mini Games")
window.geometry("1000x650")
window.configure(fg_color=T["bg"])

left_panel = CTkFrame(window, width=260, fg_color=T["panel"], corner_radius=0)
left_panel.pack(side="left", fill="y")

CTkLabel(left_panel, text="💬 Чаты", font=("Arial", 18, "bold"), text_color=T["text"]).pack(pady=15, padx=15, anchor="w")

chat_item = CTkFrame(left_panel, fg_color=T["bg"], height=50, corner_radius=10)
chat_item.pack(fill="x", padx=10, pady=5)
CTkLabel(chat_item, text="🌐 Общий Чат", font=("Arial", 13, "bold"), text_color=T["accent"]).pack(side="left", padx=10,
                                                                                                 pady=10)

CTkLabel(left_panel, text="🎨 Стиль оформления:", font=("Arial", 11), text_color=T["text"]).pack(pady=(30, 5), padx=15,
                                                                                                anchor="w")
theme_selector = CTkOptionMenu(
    left_panel, values=list(THEMES.keys()),
    command=apply_theme, fg_color=T["panel"], button_color=T["accent"]
)
theme_selector.pack(padx=15, fill="x")

main_chat_area = CTkFrame(window, fg_color="transparent")
main_chat_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)

chat_frame = CTkFrame(main_chat_area, fg_color=T["chat_bg"], corner_radius=12)
chat_frame.pack(fill="both", expand=True, pady=(0, 10))

g = CTkTextbox(
    chat_frame, fg_color="transparent", text_color=T["text"],
    font=(T["font"], 13), wrap="word"
)
g.configure(state="disabled")
g.pack(fill="both", expand=True, padx=10, pady=10)

input_frame = CTkFrame(main_chat_area, fg_color="transparent")
input_frame.pack(fill="x")

h = CTkEntry(
    input_frame, placeholder_text="Написать сообщение...",
    fg_color=T["panel"], text_color=T["text"],
    border_width=1, border_color=T["accent"], font=(T["font"], 13), height=45
)
h.pack(side="left", fill="x", expand=True, padx=(0, 10))

btn_send = CTkButton(
    input_frame, text="Отправить", command=send_msg,
    fg_color=T["accent"], text_color=T["btn_text"],
    font=(T["font"], 12, "bold"), height=45, width=110
)
btn_send.pack(side="left", padx=(0, 5))

btn_games = CTkButton(
    input_frame, text="🎮 Игры", command=open_games_window,
    fg_color=T["secondary"], text_color=T["btn_text"],
    font=(T["font"], 12, "bold"), height=45, width=100
)
btn_games.pack(side="left")

hread = Thread(target=recv_message, daemon=True)
hread.start()

window.mainloop()