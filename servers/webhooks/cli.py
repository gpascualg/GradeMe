import npyscreen
import curses


class GradeMeCLI(npyscreen.NPSAppManaged):
    def __init__(self, on_run_webhook):
        self.on_run_webhook = on_run_webhook
        
        npyscreen.NPSAppManaged.__init__(self)

    def onStart(self):
        self.registerForm("MAIN", MainForm(
            self.on_run_webhook
        ))

class MainForm(npyscreen.FormWithMenus):
    def __init__(self, on_run_webhook):
        self.on_run_webhook = on_run_webhook
        self.webhook_status = {}

        npyscreen.FormWithMenus.__init__(self)

    def _on_run_webhook(self):
        self.webhook_status.value = self.on_run_webhook()

    def create(self):
        self.add(npyscreen.TitleText, name = "Welcome:", value= "Access MENU by pressing CTRL+X." )
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exit_application    
        
        # The menus are created here.
        self.m1 = self.add_menu(name="Main Menu", shortcut="^M")
        self.webhook_status = self.add(npyscreen.TitleText, name = "Last webhook:", value={})

        self.m1.addItemsFromList([
            ("Run sample webhook", self._on_run_webhook, None),
            ("Exit Application", self.exit_application, "é"),
        ])
        
        # self.m2 = self.add_menu(name="Another Menu", shortcut="b",)
        # self.m2.addItemsFromList([
        #     ("Just Beep",   self.whenJustBeep),
        # ])
        
        # self.m3 = self.m2.addNewSubmenu("A sub menu", "^F")
        # self.m3.addItemsFromList([
        #     ("Just Beep",   self.whenJustBeep),
        # ])        

    # def whenDisplayText(self, argument):
    #    npyscreen.notify_confirm(argument)

    def exit_application(self):
        self.parentApp.setNextForm(None)
        self.editing = False
        self.parentApp.switchFormNow()
    