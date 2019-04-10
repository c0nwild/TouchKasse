import sqlite3
import tkinter as tk
from abc import abstractmethod
import time
from datetime import datetime


tk_root_base = tk.Tk()
tk_root_base.geometry('{}x{}'.format(1280, 800))
tk_root_base.resizable(width=False, height=False)
tk_root_base.wm_attributes('-fullscreen', 'true')


class DBAccess:

    def __init__(self, db_name):
        self._db_name = db_name
        self._db_conn = sqlite3.connect(self._db_name)
        self._cursor = self._db_conn.cursor()
        self._tr_list_items = ''

    def db_get(self, table_name, item_name: str = '', value: str = '*') -> list:
        """
        Get db entries by name of item
        :param table_name: Name of the sqlite table
        :param value: Specific value to query
        :param item_name: Name of the db item to be queried
        :return: List of all db entries belonging to the item
        """

        if item_name is not '':
            cmd = "SELECT ({val}) FROM {table_name} WHERE Name=='{name}'".format(
                val=value,
                table_name=table_name,
                name=item_name
            )
        else:
            cmd = "SELECT {val} FROM {table_name}".format(
                val=value,
                table_name=table_name
            )
        self._cursor.execute(cmd)
        db_content = self._cursor.fetchall()
        return db_content

    def db_update_sold(self, table_name, item_name, sold=0):
        """
        Set db entry for sold items.
        :param table_name: Name of the sqlite table
        :param item_name: Name of the db item to be queried
        :param sold: How many sold items
        :return: Nothing
        """
        cmd = "UPDATE {table_name} SET Sold={sold} WHERE Name='{name}'".format(
            table_name=table_name,
            sold=sold,
            name=item_name

        )
        self._db_conn.execute(cmd)
        self._db_conn.commit()

    def set_tr_list_items(self, tr_list_items: list):
        """
        From db.fetchall comes list of tuples. This function can process it and stores it
        in string for the db access command to be used.
        :param tr_list_items: List of tuples with shortnames for db items.
        :return: zip
        """
        item_list = []
        for item in tr_list_items:
            item_list.append(item[0])
        item_str = ','.join(item_list)

        self._tr_list_items = item_str

    def db_create_transaction_entry(self, table_name, value_str):
        """
        Create db entry
        :param table_name: Name of the sqlite table
        :param value_str: String of comma separated values to be inserted into db table.
        :return: nothing
        """
        cmd = 'INSERT INTO {table_name} ({items}) VALUES ({values})'.format(
            table_name=table_name,
            items='date, bill, cash, ' + self._tr_list_items,
            values=value_str
        )
        self._db_conn.execute(cmd)
        self._db_conn.commit()


class UIFrameItem:

    def __init__(self, name, width, height, tk_root, pos='', color='white'):
        """
        Create tkinter frame object
        :param name:
        :param width:
        :param height:
        :param tk_root:
        :param pos:
        :param color:
        """
        self._tk_master = tk_root
        self._name = name
        self._width = width
        self._height = height
        self._pos = pos
        self._color = color
        self.make_frame()
        self._frame = self.make_frame()

    def make_frame(self) -> tk.Frame:
        """
        Generate tkinter frame object
        :return: Tkinter frame object
        """
        return tk.Frame(self._tk_master,
                        width=self._width,
                        height=self._height,
                        bg=self._color)

    def get_frame(self) -> tk.Frame:
        """
        Get reference to frame object
        :return:tkinter frame object
        """
        return self._frame

    def clear(self):
        """
        Recreate frame object
        :return: Nothing
        """
        self._frame.destroy()
        self._frame = self.make_frame()
        self._frame.pack_propagate(False)

        if self._pos is not '':
            self._frame.pack(side=self._pos)
        else:
            self._frame.pack()


class UIButtonItem:

    def __init__(self, name, _tk_root):
        self._tk_master = _tk_root
        self._name = name

    def generate_button(self) -> tk.Button:
        """

        :return:tkinter button object
        """
        return tk.Button(self._tk_master,
                         text=self._name,
                         font=('Arial', 20),
                         width=100,
                         height=1,
                         command=self.button_callback)

    def get_name(self):
        """

        :return:
        """
        return self._name

    @abstractmethod
    def button_callback(self):
        pass


class FoodButtonItem(UIButtonItem):

    _db_interface = DBAccess('touchReg.db')

    def __init__(self, name, price, _tk_root):
        super(FoodButtonItem, self).__init__(name, _tk_root)
        self._tk_master = _tk_root
        self._price = price
        self._sold = 0

    def button_callback(self):
        self.increment_sold()
        print("Set sold counter for {name} to {sold}".format(name=self._name, sold=self._sold))
        if self._event_cb is not None:
            self._event_cb(self._name, self._price)

    def attach_external_callback(self, cb):
        self._event_cb = cb

    @property
    def get_sold(self):
        """How many items are sold?"""
        return self._sold

    def increment_sold(self):
        self._sold += 1

    def reset_sold(self):
        self._sold = 0

    def db_get(self, item_name='', value=''):
        """

        :return: db items related to food item
        """
        if item_name is '':
            item_name = self._name

        return self._db_interface.db_get('food_list', item_name, value)


class CashButtonItem(UIButtonItem):

    def __init__(self, name, value, _tk_root):
        super(CashButtonItem, self).__init__(name, _tk_root)
        self._tk_master = _tk_root
        self._value = value

    def button_callback(self):
        if self._event_cb is not None:
            self._event_cb(self._value)

    def attach_external_callback(self, cb):
        self._event_cb = cb


class TouchRegisterUI:
    """Main class for tkinter UI"""

    food_buttons = []
    display_elements = []
    total_cash = 0
    current_cash = 0
    current_sum = 0
    _db_interface = DBAccess('touchReg.db')
    transaction_done = False

    def __init__(self):
        """Main frame"""
        self.tk_main_frame = UIFrameItem('main_frame',
                                         width=1280,
                                         height=800,
                                         tk_root=tk_root_base)
        self.tk_main_frame.get_frame().pack()

        """Display"""
        self.tk_display_frame = UIFrameItem('display_frame',
                                            width=640,
                                            height=800,
                                            tk_root=self.tk_main_frame.get_frame())
        self.tk_display_frame.get_frame().pack_propagate(False)
        self.tk_display_frame.get_frame().pack(side=tk.LEFT)

        self.tk_display_element_frame = UIFrameItem('display_elements',
                                                    width=640,
                                                    height=700,
                                                    pos=tk.LEFT,
                                                    tk_root=self.tk_display_frame.get_frame())
        self.tk_display_element_frame.get_frame().pack_propagate(False)
        self.tk_display_element_frame.get_frame().pack()

        self.tk_display_sum = tk.Label(self.tk_display_frame.get_frame(),
                                       text='SUMME',
                                       justify=tk.LEFT,
                                       anchor=tk.W,
                                       width=640,
                                       font=('Arial', 20),
                                       pady=10,
                                       padx=10
                                       )
        self.tk_display_sum.pack_propagate(False)
        self.tk_display_sum.pack(side=tk.BOTTOM)

        self.tk_display_cash = tk.Label(self.tk_display_frame.get_frame(),
                                        text='BAR',
                                        justify=tk.LEFT,
                                        anchor=tk.W,
                                        width=640,
                                        font=('Arial', 20),
                                        pady=10,
                                        padx=10
                                        )
        self.tk_display_cash.pack_propagate(False)
        self.tk_display_cash.pack(side=tk.BOTTOM)

        """Frame für Essenstasten und Funktionstasten"""
        self.tk_food_function_frame = tk.Frame(self.tk_main_frame.get_frame(), height=800, width=640)
        self.tk_food_function_frame.pack_propagate(False)
        self.tk_food_function_frame.pack(side=tk.RIGHT)

        """Frame für Essenstasten"""
        self.tk_food_frame = UIFrameItem('food_buttons',
                                         width=640,
                                         height=650,
                                         color='red',
                                         tk_root=self.tk_food_function_frame)
        self.tk_food_frame.get_frame().pack_propagate(False)
        self.tk_food_frame.get_frame().pack()
        self.food_buttons = self.food_element_factory()

        """Frame für Funktionstasten"""
        self.tk_function_frame = UIFrameItem('function_buttons',
                                             width=640,
                                             height=150,
                                             color='green',
                                             tk_root=self.tk_food_function_frame)
        self.tk_function_frame.get_frame().pack_propagate(False)
        self.tk_function_frame.get_frame().pack()
        self.food_function_element_factory()

        """prepare db access function for transfer list"""
        tr_list_items = self._db_interface.db_get('food_list', value='name_short')
        self._db_interface.set_tr_list_items(tr_list_items)

    def food_element_factory(self):
        b_elem = []
        db_elements = self._db_interface.db_get('food_list', value='*')
        for element in db_elements:
            eval_str = "FoodButtonItem('{name}', {price}, self.tk_food_frame.get_frame())".format(
                name=element[1],
                price=element[3]
            )
            obj: FoodButtonItem = eval(eval_str)
            obj.attach_external_callback(self.display_element_factory)
            btn = obj.generate_button()
            btn.pack()
            b_elem.append(obj)

        return b_elem

    def display_element_factory(self, name, price):
        if self.transaction_done is True:
            self.reset_transaction()

        self.got_cash_button.config(state='active')

        disp_obj = {
            'tk_name': tk.Label(self.tk_display_element_frame.get_frame(),
                                text=name,
                                font=('Arial', 15),
                                justify=tk.LEFT,
                                anchor=tk.W,
                                width=250,
                                padx=10
                                ),
            'tk_price': tk.Label(self.tk_display_element_frame.get_frame(),
                                 text="{price:.02f}€".format(price=price),
                                 font=('Arial', 15),
                                 justify=tk.LEFT,
                                 anchor=tk.W,
                                 width=250,
                                 padx=20
                                 ),
            'name': name,
            'price': price
        }
        disp_obj['tk_name'].pack()
        disp_obj['tk_price'].pack()

        self.display_elements.append(disp_obj)
        self.update_sum()

    def food_function_element_factory(self):
        got_cash_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                         width=400,
                                         height=150)
        self.got_cash_button = tk.Button(got_cash_button_frame,
                                         text='Gegeben',
                                         font=('Arial', 20),
                                         width=100,
                                         height=100,
                                         state='disabled',
                                         command=self.got_cash)

        cancel_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                       width=240,
                                       height=150)
        cancel_button = tk.Button(cancel_button_frame,
                                  text='Abbrechen',
                                  font=('Arial', 20),
                                  width=100,
                                  height=100,
                                  command=lambda: self.end_transaction('cancel'))

        got_cash_button_frame.pack_propagate(False)
        got_cash_button_frame.pack(side=tk.LEFT)
        cancel_button_frame.pack_propagate(False)
        cancel_button_frame.pack(side=tk.LEFT)
        self.got_cash_button.pack()
        cancel_button.pack()

    def cash_button_factory(self):
        b_elem = []
        cash_vals = {
            '1 Cent': 0.01,
            '2 Cent': 0.02,
            '5 Cent': 0.05,
            '10 Cent': 0.1,
            '20 Cent': 0.2,
            '50 Cent': 0.5,
            '1 €': 1,
            '2 €': 2,
            '5 €': 5,
            '10 €': 10,
            '20 €': 20,
            '50 €': 50,
            '100 €': 100
        }

        for val in cash_vals:
            eval_str = "CashButtonItem('{name}', {value}, self.tk_food_frame.get_frame())".format(
                name=val,
                value=cash_vals[val]
            )
            obj: CashButtonItem = eval(eval_str)
            obj.attach_external_callback(self.cash_display)
            b_elem.append(obj.generate_button())

        for b in b_elem:
            b.pack()

    def got_cash_function_element_factory(self):
        got_cash_ok_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                           width=215,
                                           height=150)
        got_cash_ok_button = tk.Button(got_cash_ok_button_frame,
                                       text='Ok',
                                       font=('Arial', 20),
                                       width=100,
                                       height=100,
                                       command=lambda: self.end_transaction('ok'))

        got_cash_reset_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                           width=215,
                                           height=150)
        got_cash_reset_button = tk.Button(got_cash_reset_button_frame,
                                          text='Löschen',
                                          font=('Arial', 20),
                                          width=100,
                                          height=100,
                                          command=self.reset_cash_display)

        got_cash_cancel_button_frame = tk.Frame(self.tk_function_frame.get_frame(),
                                           width=210,
                                           height=150)
        got_cash_cancel_button = tk.Button(got_cash_cancel_button_frame,
                                           text='Abbrechen',
                                           font=('Arial', 20),
                                           width=100,
                                           height=100,
                                           command=lambda: self.end_transaction('cancel'))
        got_cash_ok_button_frame.pack_propagate(False)
        got_cash_ok_button_frame.pack(side=tk.LEFT)
        got_cash_reset_button_frame.pack_propagate(False)
        got_cash_reset_button_frame.pack(side=tk.LEFT)
        got_cash_cancel_button_frame.pack_propagate(False)
        got_cash_cancel_button_frame.pack(side=tk.LEFT)
        got_cash_ok_button.pack()
        got_cash_reset_button.pack()
        got_cash_cancel_button.pack()

    def cash_display(self, value):
        self.current_cash = self.current_cash + value
        self.tk_display_cash.config(
            text="BAR: {cash:.02f} €".format(
                cash=self.current_cash
            )
        )

    def reset_cash_display(self):
        self.current_cash = 0
        self.cash_display(0)

    def clear_display_element_list(self):
        self.tk_display_element_frame.clear()
        self.display_elements.clear()
        self.update_sum()

    def got_cash(self):
        self.tk_food_frame.clear()
        self.tk_function_frame.clear()

        self.cash_button_factory()
        self.reset_cash_display()

        self.got_cash_function_element_factory()

    def end_transaction(self, outcome):
        if outcome is 'ok':
            try:
                self.close_transaction()
            except Exception:
                self.tk_display_cash.config(text="Zu wenig erhalten")
            else:
                self.transaction_done = True
            finally:
                self.tk_food_frame.clear()
                self.tk_function_frame.clear()

                self.food_buttons = self.food_element_factory()  # restore food buttons

                self.food_function_element_factory()  # restore function buttons

        elif outcome is 'cancel':
            self.reset_transaction()

    def close_transaction(self):
        """
        Display return money and check in data in DB.
        :return:
        """
        _transaction_log_items = list()
        _transaction_log_str = ''

        _cash_back = self.current_cash - self.current_sum

        if _cash_back < 0:
            raise Exception

        self.tk_display_cash.config(
            text="ZURÜCK: {cash:.02f} €".format(
                cash=self.current_cash - self.current_sum
            )
        )

        date = datetime.now()

        _transaction_log_items.append('"' + date.ctime() + '"')
        _transaction_log_items.append(str(self.current_sum))
        _transaction_log_items.append(str(self.current_cash))

        for e in self.food_buttons:
            db_entry = e.db_get(e.get_name(), 'Sold')
            _sold = e.get_sold
            _transaction_log_items.append(str(_sold))
            e.reset_sold()
            _sold = _sold + db_entry[0][0]
            self._db_interface.db_update_sold('food_list', item_name=e.get_name(), sold=_sold)

        _transaction_log_str = ','.join(_transaction_log_items)
        print(_transaction_log_str)
        self._db_interface.db_create_transaction_entry('tr_list', _transaction_log_str)

    def reset_transaction(self):
        self.tk_food_frame.clear()
        self.tk_function_frame.clear()
        self.food_buttons = self.food_element_factory()
        self.food_function_element_factory()
        self.reset_cash_display()
        self.current_cash = 0
        self.clear_display_element_list()
        self.update_sum()
        self.transaction_done = False
        self.got_cash_button.config(state='disabled')

    def update_sum(self):
        _sum = 0
        for e in self.display_elements:
            _sum = _sum + e['price']
        txt = "SUMME: {sum:.02f}€".format(sum=_sum)
        self.tk_display_sum.config(text=txt)
        self.current_sum = _sum


if __name__ == "__main__":
    TouchRegisterUI()
    tk_root_base.mainloop()
