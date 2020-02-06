from tkinter import *
from backend import *
import getpass
from func_timeout import func_timeout, FunctionTimedOut
import threading

TT_TITLE = "Time Tracker 0.5"
TT_TITLE_UPDATING = TT_TITLE + " - updating..."
TIMEOUT_IN_S = 43200
TIMEOUT_IN_MS = TIMEOUT_IN_S * 1000
jira_operations = None


class Window:
    def __init__(self, window):
        window.update_idletasks()
        width = window.winfo_reqwidth()
        height = window.winfo_reqheight()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        window.resizable(False, False)


class GUI(Window):
    def __init__(self, master):
        self.master = master
        self.master.title(TT_TITLE)
        self.master.after(TIMEOUT_IN_MS, self.logout)

        self.l_work = Label(self.master, text="WORK", font='BOLD 16')
        self.l_work.grid(row=0, column=0)

        self.l_break = Label(self.master, text="BREAK", font='BOLD 16')
        self.l_break.grid(row=0, column=1)

        self.b_start_work = Button(self.master, text="Start work", width=20, command=lambda: self.start_new_thread(self.start_work))
        self.b_start_work.grid(row=1, column=0, pady=5)
        if jira_operations.is_story_created('WORK'):
            self.b_start_work['state'] = 'disabled'

        self.b_stop_work = Button(self.master, text="Stop work", width=20, command=lambda: self.start_new_thread(self.stop_work))
        self.b_stop_work.grid(row=2, column=0, pady=5)
        if not jira_operations.is_story_created('WORK'):
            self.b_stop_work['state'] = 'disabled'

        self.b_start_break = Button(self.master, text="Start break", width=20, command=lambda: self.start_new_thread(self.start_break))
        self.b_start_break.grid(row=1, column=1, pady=5)
        if jira_operations.is_story_created('BREAK'):
            self.b_start_break['state'] = 'disabled'

        self.b_stop_break = Button(self.master, text="Stop break", width=20, command=lambda: self.start_new_thread(self.stop_break))
        self.b_stop_break.grid(row=2, column=1, pady=5)
        if not jira_operations.is_story_created('BREAK'):
            self.b_stop_break['state'] = 'disabled'

        self.l_description_of_work = Label(self.master, text="Description of work story:")
        self.l_description_of_work.grid(row=3, column=0)

        self.t_description_of_work = Text(self.master, height=8, width=50)
        self.t_description_of_work.grid(row=4, column=0, padx=5)
        self.t_description_of_work.insert(END, jira_operations.description_init('WORK'))

        self.b_update_description_work = Button(self.master, text="Update description", width=20,
                                                command=lambda: self.start_new_thread(self.update_description_work))
        self.b_update_description_work.grid(row=5, column=0, pady=5)
        if not jira_operations.is_story_created('WORK'):
            self.b_update_description_work['state'] = 'disabled'

        self.l_description_of_break = Label(self.master, text="Description of break story:")
        self.l_description_of_break.grid(row=3, column=1)

        self.t_description_of_break = Text(self.master, height=8, width=50)
        self.t_description_of_break.grid(row=4, column=1, padx=5)
        self.t_description_of_break.insert(END, jira_operations.description_init('BREAK'))

        self.b_update_description_break = Button(self.master, text="Update description", width=20,
                                                 command=lambda: self.start_new_thread(self.update_description_break))
        self.b_update_description_break.grid(row=5, column=1, pady=5)
        if not jira_operations.is_story_created('BREAK'):
            self.b_update_description_break['state'] = 'disabled'

        self.l_todays_worklog = Label(self.master, text="Today's worklog:")
        self.l_todays_worklog.grid(row=6, column=0, columnspan=2)

        self.list_of_stories_today = Listbox(self.master, height=5, width=130)
        self.list_of_stories_today.grid(row=7, column=0, rowspan=2, columnspan=2)

        self.current_week = Label(self.master, text="Current week statistics:")
        self.current_week.grid(row=9, column=0, columnspan=2)

        self.list_current_week = Listbox(self.master, height=4, width=130)
        self.list_current_week.grid(row=10, column=0, rowspan=2, columnspan=2)

        self.b_update_list = Button(self.master, text="Update lists", width=20, command=lambda: self.start_new_thread(self.update_list))
        self.b_update_list.grid(row=12, column=0, pady=5, columnspan=2)

        super().__init__(self.master)
        self.update_list()

    def logout(self):
        self.master.destroy()
        run_program()

    def start_work(self):
        self.b_start_work['state'] = 'disabled'
        self.b_stop_work['state'] = 'normal'
        self.b_update_description_work['state'] = 'normal'
        self.master.title(TT_TITLE_UPDATING)
        if not jira_operations.start_work():
            messagebox.showinfo("Error", "Ticket WORK already created.")
        self.update_list()

    def stop_work(self):
        self.b_start_work['state'] = 'normal'
        self.b_stop_work['state'] = 'disabled'
        self.b_update_description_work['state'] = 'disabled'
        self.master.title(TT_TITLE_UPDATING)
        if not jira_operations.stop_work():
            messagebox.showinfo("Error", "Ticket WORK not created.")
        self.update_list()
        self.t_description_of_work.delete("1.0", END)

    def start_new_thread(self, target_function):
        self.thread = threading.Thread(target=target_function)
        self.thread.daemon = True
        self.thread.start()
        self.master.after(20, self.check_thread)

    def check_thread(self):
        if self.thread.is_alive():
            self.master.after(20, self.check_thread)

    def start_break(self):
        self.b_start_break['state'] = 'disabled'
        self.b_stop_break['state'] = 'normal'
        self.b_update_description_break['state'] = 'normal'
        self.master.title(TT_TITLE_UPDATING)
        if not jira_operations.start_break(self.t_description_of_break.get("1.0", END)):
            messagebox.showinfo("Error", "Ticket BREAK already created.")
        self.update_list()

    def stop_break(self):
        self.b_start_break['state'] = 'normal'
        self.b_stop_break['state'] = 'disabled'
        self.b_update_description_break['state'] = 'disabled'
        self.master.title(TT_TITLE_UPDATING)
        if not jira_operations.stop_break():
            messagebox.showinfo("Error", "Ticket BREAK not created.")
        self.update_list()
        self.t_description_of_break.delete("1.0", END)

    def update_list(self):
        self.master.title(TT_TITLE_UPDATING)
        self.list_of_stories_today.delete(0, END)
        for row in jira_operations.get_stories_created_today():
            self.list_of_stories_today.insert(END, row)

        self.list_current_week.delete(0, END)
        for row in jira_operations.get_week_statistics():
            self.list_current_week.insert(END, row)
        self.master.title(TT_TITLE)

    def update_description_work(self):
        self.master.title(TT_TITLE_UPDATING)
        description = self.t_description_of_work.get("1.0", END)
        if not jira_operations.update_description('WORK', description):
            messagebox.showinfo("Error", "Ticket WORK not created.")
        self.update_list()
        self.master.title(TT_TITLE)

    def update_description_break(self):
        self.master.title(TT_TITLE_UPDATING)
        description = self.t_description_of_break.get("1.0", END)
        if not jira_operations.update_description('BREAK', description):
            messagebox.showinfo("Error", "Ticket BREAK not created.")
        self.update_list()
        self.master.title(TT_TITLE)


class GUILogin(Window):
    def __init__(self, top):
        self.top = top
        self.top.title("Login to JIRA")

        self.l_login = Label(top, text="Login: ")
        self.l_password = Label(top, text="Password: ")

        self.e_login = Entry(top)
        self.e_password = Entry(top, show='*')

        self.b_login = Button(top, text="Login", width=12, command=self.login)
        self.b_cancel = Button(top, text="Cancel", width=12, command=self.cancel)

        self.l_text = Label(top, text="Please enter your credentials and press ENTER.")

        self.l_login.grid(row=0, column=0, pady=5)
        self.l_password.grid(row=0, column=1, pady=5)
        self.e_login.grid(row=1, column=0, pady=5, padx=5)
        self.e_password.grid(row=1, column=1, pady=5, padx=5)
        self.b_login.grid(row=2, column=0, pady=5)
        self.b_cancel.grid(row=2, column=1, pady=5)
        self.l_text.grid(row=3, column=0, columnspan=2, pady=5)

        super().__init__(top)

        self.username = getpass.getuser()
        self.e_login.insert(0, self.username)
        self.e_password.focus_set()
        self.top.bind('<Return>', self.login)

    def login(self, _=None):
        self.l_text['text'] = 'Loading...'
        self.b_login['state'] = 'disabled'
        self.top.update()
        try:
            func_timeout(5, self.login_to_jira, args=(self.e_login.get(), self.e_password.get()))
            GUI(root_window)
            root_window.deiconify()
            login_window.destroy()
        except FunctionTimedOut:
            messagebox.showinfo("Error", "Timeout, probably wrong password.")
            self.b_login['state'] = 'normal'
            self.l_text['text'] = 'Please enter your credentials and press ENTER.'
            self.top.update()
        except Exception as e:
            messagebox.showinfo("Error", "Probably you have to login to JIRA via browser and enter CAPTCHA.")
            print(e)
            self.b_login['state'] = 'normal'
            self.l_text['text'] = 'Please enter your credentials and press ENTER.'
            self.top.update()

    @staticmethod
    def login_to_jira(login, password):
        global jira_operations
        jira_operations = JiraOperations((login, password))

    @staticmethod
    def cancel():
        login_window.destroy()
        root_window.destroy()
        sys.exit()


if __name__ == "__main__":
    def run_program():
        global root_window
        global login_window
        root_window = Tk()
        login_window = Toplevel()
        GUILogin(login_window)

        root_window.withdraw()
        login_window.mainloop()


    run_program()
