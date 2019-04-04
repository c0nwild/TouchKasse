import sqlite3
import tkinter as tk
from abc import abstractmethod

tk_root_base = tk.Tk()
tk_root_base.geometry('{}x{}'.format(1200, 800))
tk_root_base.resizable(width=False, height=False)
tk_root_base.wm_attributes('-fullscreen', 'true')


class DBAccess:

    _cursor = None
    _db_conn = None
    _db_name = ''
    _table_name = ''

    def __init__(self, db_name, table_name):
        self._db_name = db_name
        self._table_name = table_name
        self._db_conn = sqlite3.connect(self._db_name)
        self._cursor = self._db_conn.cursor()

    def db_get(self, item_name=None):
        if item_name is not None:
            cmd = "SELECT * FROM {table_name} WHERE Name=={name}".format(
                table_name=self._table_name,
                name=item_name
            )
        else:
            cmd = "SELECT * FROM {table_name}".format(
                table_name=self._table_name
            )
        self._cursor.execute(cmd)
        db_content = self._cursor.fetchall()
        return db_content

    def db_put(self, name, sold, price):
        cmd = "INSERT INTO {table_name} (Name, Sold, Price) VALUES ({name}, {sold}, {price}".format(
            table_name=self._table_name,
            name=name,
            sold=sold,
            price=price
        )
        self._db_conn.execute(cmd)
        self._db_conn.commit()

    def db_update(self, name, sold, price):
        cmd = "UPDATE {table_name} SET Name={name}, Sold={sold}, Price={price} WHERE Name={name}".format(
            table_name=self._table_name,
            name=name,
            sold=sold,
            price=price
        )
        self._db_conn.execute(cmd)
        self._db_conn.commit()

    def db_get_name(self):
        return self._db_name


class UIFrameItem:

    _name = ''
    _width = 0
    _height = 0
    _pos = ''
    _child_elements = []

    def __init__(self, name, width, height, tk_root, color='white', pos=tk.TOP):
        self._tk_master = tk_root
        self._name = name
        self._width = width
        self._height = height
        self._pos = pos
        self._color = color

        self._frame = tk.Frame(self._tk_master,
                               width=self._width,
                               height=self._height,
                               bg=self._color)

    def get_frame(self) -> tk.Frame:
        """

        :return:tkinter frame object
        """
        return self._frame

    def clear(self):
        self._frame.destroy()
        self._frame = tk.Frame(self._tk_master,
                               width=self._width,
                               height=self._height)
        self._frame.pack_propagate(False)

        self._frame.pack(side=self._pos)


class UIButtonItem:

    _name = ''

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
                         width=510,
                         height=1,
                         command=self.button_callback)

    def get_name(self):
        return self._name

    @abstractmethod
    def button_callback(self):
        pass


class FoodButtonItem(UIButtonItem):

    _event_cb = None

    _price = 0.0
    _sold = tk.IntVar()

    _tk_master = None
    _db_interface = DBAccess('touchReg.db', 'food_list')

    def __init__(self, name, price, _tk_root):
        super(FoodButtonItem, self).__init__(name, _tk_root)
        self._tk_master = _tk_root
        self._price = price

    def button_callback(self):
        _sold_local = self._sold.get()
        print("Set sold counter for {name} to {sold}".format(name=self._name, sold=_sold_local))
        self._sold.set(_sold_local + 1)
        if self._event_cb is not None:
            self._event_cb(self._name, self._price)

    def attach_external_callback(self, cb):
        self._event_cb = cb

    def get_sold(self):
        return self._sold.get()

    def increment_sold(self):
        pass

    def db_get(self, item_name=None):
        """

        :return: db items related to food item
        """
        return self._db_interface.db_get(item_name)


class CashButtonItem(UIButtonItem):

    _event_cb = None

    _value = 0.0

    _tk_master = None
    #_db_interface = DBAccess('touchReg.db', 'cash_list')

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

    button_elements = []
    display_elements = []
    total_cash = 0
    current_cash = 0
    current_sum = 0
    _db_interface = DBAccess('touchReg.db', 'food_list')
    transaction_done = False

    def __init__(self):
        """Main frame"""
        self.tk_main_frame = UIFrameItem('main_frame',
                                         width=1200,
                                         height=800,
                                         tk_root=tk_root_base)
        self.tk_main_frame.get_frame().pack()

        """Display"""
        self.tk_display_frame = UIFrameItem('display_frame',
                                            width=600,
                                            height=800,
                                            tk_root=self.tk_main_frame.get_frame())
        self.tk_display_frame.get_frame().pack_propagate(False)
        self.tk_display_frame.get_frame().pack(side=tk.LEFT)

        self.tk_display_element_frame = UIFrameItem('display_elements',
                                                    width=600,
                                                    height=700,
                                                    pos=tk.LEFT,
                                                    tk_root=self.tk_display_frame.get_frame())
        self.tk_display_element_frame.get_frame().pack_propagate(False)
        self.tk_display_element_frame.get_frame().pack()

        self.tk_display_sum = tk.Label(self.tk_display_frame.get_frame(),
                                       text='SUMME',
                                       justify=tk.LEFT,
                                       anchor=tk.W,
                                       width=600,
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
                                        width=600,
                                        font=('Arial', 20),
                                        pady=10,
                                        padx=10
                                        )
        self.tk_display_cash.pack_propagate(False)
        self.tk_display_cash.pack(side=tk.BOTTOM)

        """Frame für Essenstasten und Funktionstasten"""
        self.tk_food_function_frame = tk.Frame(self.tk_main_frame.get_frame(), height=800, width=600)
        self.tk_food_function_frame.pack_propagate(False)
        self.tk_food_function_frame.pack(side=tk.RIGHT)

        """Frame für Essenstasten"""
        self.tk_food_frame = UIFrameItem('food_buttons',
                                         width=600,
                                         height=650,
                                         color='red',
                                         tk_root=self.tk_food_function_frame)
        self.tk_food_frame.get_frame().pack_propagate(False)
        self.tk_food_frame.get_frame().pack(side=tk.TOP)
        self.food_element_factory()

        """Frame für Funktionstasten"""
        self.tk_function_frame = UIFrameItem('function_buttons',
                                             width=600,
                                             height=150,
                                             color='green',
                                             tk_root=self.tk_food_function_frame)
        self.tk_function_frame.get_frame().pack()
        self.function_element_factory()

    def food_element_factory(self):
        b_elem = []
        db_elements = self._db_interface.db_get()
        for element in db_elements:
            eval_str = "FoodButtonItem('{name}', {price}, self.tk_food_frame.get_frame())".format(
                name=element[1],
                price=element[3]
            )
            obj: FoodButtonItem = eval(eval_str)
            obj.attach_external_callback(self.display_element_factory)
            b_elem.append(obj.generate_button())

        for element in b_elem:
            element.pack()

        return b_elem

    def display_element_factory(self, name, price):
        if self.transaction_done is True:
            self.reset_transaction()

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
                                 font=('Arial',15),
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

    def function_element_factory(self):
        clear_list_button = tk.Button(self.tk_function_frame.get_frame(),
                                      text='Löschen',
                                      font=('Arial', 20),
                                      width=15,
                                      height=2,
                                      command=self.clear_display_element_list)

        got_cash_button = tk.Button(self.tk_function_frame.get_frame(),
                                    text='Gegeben',
                                    font=('Arial', 20),
                                    width=15,
                                    height=2,
                                    command=self.got_cash)

        got_cash_button.pack(side=tk.LEFT)
        clear_list_button.pack(side=tk.LEFT)

    def got_cash_button_factory(self):
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

        self.got_cash_button_factory()

        got_cash_ok_button = tk.Button(self.tk_function_frame.get_frame(),
                                       text='Ok',
                                       font=('Arial', 20),
                                       width=10,
                                       height=2,
                                       command=lambda: self.got_cash_done(True))
        got_cash_ok_button.pack(side=tk.LEFT)

        got_cash_reset_button = tk.Button(self.tk_function_frame.get_frame(),
                                          text='Löschen',
                                          font=('Arial', 20),
                                          width=10,
                                          height=2,
                                          command=self.reset_cash_display)
        got_cash_reset_button.pack(side=tk.LEFT)

        got_cash_cancel_button = tk.Button(self.tk_function_frame.get_frame(),
                                           text='Abbrechen',
                                           font=('Arial', 20),
                                           width=10,
                                           height=2,
                                           command=lambda: self.got_cash_done(False))
        got_cash_cancel_button.pack(side=tk.LEFT)

    def got_cash_done(self, is_transaction_done):
        self.tk_food_frame.clear()
        self.tk_function_frame.clear()

        self.food_element_factory()  # restore food buttons

        self.function_element_factory()  # restore function buttons

        if is_transaction_done is True:
            self.tk_display_cash.config(
                text="ZURÜCK: {cash:.02f} €".format(
                    cash=self.current_cash - self.current_sum
                )
            )
            self.transaction_done = True
        else:
            self.reset_transaction()

    def reset_transaction(self):
        self.reset_cash_display()
        self.current_cash = 0
        self.clear_display_element_list()
        self.update_sum()
        self.transaction_done = False

    def update_sum(self):
        _sum = 0
        for e in self.display_elements:
            _sum = _sum + e['price']
        txt = "SUMME: {sum:.02f}€".format(sum=_sum)
        self.tk_display_sum.config(text=txt)
        self.current_sum = _sum


if __name__ == "__main__":
    reg = TouchRegisterUI()
    tk_root_base.mainloop()
